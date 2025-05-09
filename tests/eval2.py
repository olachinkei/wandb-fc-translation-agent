import os
import pytest
import sys
from pathlib import Path
import boto3
import json
from tqdm import tqdm
import time
# Add the project root directory to the Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from dotenv import load_dotenv
import weave
from weave.flow.eval_imperative import EvaluationLogger
from wandb_translator.handler import WandBReportTranslator
# Import app after adding to path
from app import invoke_bedrock_agent

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path, override=True)


# Example input data (replace with your actual dataset if needed)
evaluation_dataset_path = "weave:///wandb-japan/fc-agent-dev/object/fc-agent-tool-use-evaluation:1HMiNW1wV2G0QUwYYqMRuRmnuLepw2CYnYl5j2a4664"
current_prompt = weave.ref("weave:///wandb-japan/fc-agent/object/translate_prompt:latest").get().content

def get_eval_samples():
    """
    Fetch and prepare evaluation samples from the dataset.
    Returns a list of samples with properly formatted prompts.
    """
    eval_dataset = weave.ref(evaluation_dataset_path).get().to_pandas()
    samples = []
    for _, row in eval_dataset.iterrows():
        prompt = None  # Initialize prompt
        if row['expected_tool'] == 'translate_report':
            prompt = row['prompt_template'].format(report_url=row['report_url'])
        elif row['expected_tool'] == 'update_prompt':
            prompt = row['prompt_template'].format(prompt_for_update=row['prompt_for_update'])
        elif row['expected_tool'] == 'show_prompt':
            prompt = row['prompt_template']
            
        if prompt is not None:  # Only add sample if prompt was successfully created
            samples.append({
                'id': row['id'],
                'expected_tool': row['expected_tool'],
                'prompt': prompt,
                'report_url': row['report_url'],
                'target_language': row['target_language'],
                'prompt_for_update': row['prompt_for_update'],
                'prompt_template': row['prompt_template']
            })
    return samples

#==============================================
# Scorerの設定
#==============================================

# Tool use scoring functions
def tool_use_scorer(row, extracted_result):
    """
    Score whether the detected tool matches the expected tool.
    Args:
        row: Sample data containing expected tool
        extracted_result: Result from agent containing detected tool
    Returns:
        Boolean indicating if the tools match
    """
    try:
        expected = row['expected_tool']
        actual = extracted_result['extracted_info']['function_name']
        return expected == actual
    except Exception as e:
        print(f"Warning in tool_use_scorer: {e}")
        return False


def success_scorer(row, extracted_result, tool_use_score):
    """
    Score whether the tool execution was successful based on the tool type.
    Args:
        row: Sample data containing expected results
        extracted_result: Result from agent containing actual output
    Returns:
        Boolean indicating if the tool execution was successful
    """
    if tool_use_score==False:
        return False
    
    if extracted_result=="":
        return False
    
    info = extracted_result['extracted_info']
    expected_tool = row['expected_tool']

    if expected_tool == 'translate_report':
        # Check if we have a valid report URL
        return isinstance(info['report_url'], str) and len(info['report_url']) > 0
    
    elif expected_tool == 'show_prompt':
        # Check if the extracted prompt matches the current translation prompt
        return isinstance(info['prompt'], str) and info['prompt'] == current_prompt
    
    elif expected_tool == 'update_prompt':
        # Check if the updated prompt matches the target prompt for update
        time.sleep(5)
        try:
            updated_prompt = weave.ref("weave:///wandb-japan/fc-agent-dev/object/translate_prompt:latest").get().content
            print(f"Updated prompt: {updated_prompt}")
            return row['prompt_for_update']==updated_prompt
        except Exception as e:
            print(f"Error fetching updated prompt: {e}")
            return False
    else:
        return False
        

# Example model logic (translator)
@weave.op()
def invole_agent_extract_info(sample) -> dict:
    """
    Process a single evaluation sample through the agent and extract relevant information.
    Returns a dictionary containing the raw output and extracted information.
    """
    try:
        result = invoke_bedrock_agent(user_input=sample["prompt"], mode="eval")
        if isinstance(result, str):
            print(f"Warning: Unexpected string result from invoke_bedrock_agent for sample {sample['id']}")
            return {
                "output": result,
                "extracted_info": {
                    "function_name": None,
                    "report_url": None,
                    "prompt": None,
                    "updated_prompt": None
                }
            }
        
        info = extract_info_from_result_with_llm(result)
        if info["function_name"] is None:
            print(f"Warning: Could not extract function name for sample {sample['id']}")
            
        return {"output": result["result"], "extracted_info": info}
    except Exception as e:
        print(f"Error processing sample {sample['id']}: {str(e)}")
        return {
            "output": str(e),
            "extracted_info": {
                "function_name": None,
                "report_url": None,
                "prompt": None,
                "updated_prompt": None
            }
        }

def overall_test():
    """
    Run the overall evaluation process:
    1. Initialize Weave connection
    2. Set up evaluation logger
    3. Process each sample and log results
    """
    eval_samples = get_eval_samples()
    print(f"\nStarting evaluation with {len(eval_samples)} samples...")
    
    eval_logger = EvaluationLogger(
        model="wandb_fc_agent",
        dataset=eval_samples
    )
    success_scores = []
    tool_use_scores = []

    for _, sample in enumerate(tqdm(eval_samples, desc="Processing samples", unit="sample")):
        # Process sample and extract information
        extracted_result = invole_agent_extract_info(sample)
        
        # Log prediction and scores
        pred_logger = eval_logger.log_prediction(
            inputs=sample,
            output=extracted_result
        )

        # Calculate and log scores
        tool_use_score = tool_use_scorer(sample, extracted_result)
        success_score = success_scorer(sample, extracted_result, tool_use_score)
        
        pred_logger.log_score(
            scorer="tool_use",
            score=tool_use_score
        )
        pred_logger.log_score(
            scorer="success",
            score=success_score
        )
        pred_logger.finish()

        success_scores.append(success_score)
        tool_use_scores.append(tool_use_score)
    success_rate = sum(success_scores) / len(success_scores) if success_scores else 0.0
    tool_use_rate = sum(tool_use_scores) / len(tool_use_scores) if tool_use_scores else 0.0
    summary_stats = {"overall_score": success_rate, "tool_use_score": tool_use_rate}
    eval_logger.log_summary(summary_stats)

    print("\nEvaluation complete! View detailed results in the Weave UI.")

def main():
    # Initialize Weave at the start
    weave.init(os.environ["WANDB_ENTITY"] + "/" + os.environ["WANDB_PROJECT"])
    overall_test()


@weave.op()
def extract_function_name(eval_info: list) -> str:
    """
    Extract the function name from evaluation info using LLM.
    Args:
        eval_info: List of evaluation information strings
    Returns:
        Extracted function name or None if extraction fails
    """
    bedrock_client = boto3.client("bedrock-runtime", region_name=os.getenv("AWS_REGION", "us-east-1"))
    eval_info_text = "".join(eval_info)
    
    response = bedrock_client.invoke_model(
        modelId="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
        contentType="application/json",
        accept="application/json",
        body=json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 100,
            "temperature": 0,
            "messages": [{
                "role": "user", 
                "content": f"Extract the function name from this text. Return ONLY one of these exact values: translate_report, show_prompt, or update_prompt. No other text or explanation. If you cannot find the function name, return None:\n\n{eval_info_text}"
            }]
        })
    )
    response_body = json.loads(response["body"].read())
    function_name = response_body["content"][0]["text"].strip()
    
    valid_functions = ["translate_report", "show_prompt", "update_prompt"]
    if function_name in valid_functions:
        return function_name
        
    print(f"Warning: Invalid function name extracted: {function_name}")
    return None
        

@weave.op()
def extract_output_info(function_name: str, result: str) -> str:
    """
    Extract specific output information based on the function type using LLM.
    Args:
        function_name: Name of the function to extract information for
        result: Result text to extract information from
    Returns:
        Extracted information string or empty string if extraction fails
    """
    bedrock_client = boto3.client("bedrock-runtime", region_name=os.getenv("AWS_REGION", "us-east-1"))
    
    system_prompt = """You are an expert at extracting specific information from text.
Your task is to find and extract ONLY the relevant information based on the function type:
- For "translate_report": Find and extract ONLY the URL. Look for patterns like http://, https://
- For "show_prompt": Find and extract ONLY the prompt text. 
- For "update_prompt": Extract the updated prompt.

If you find multiple matches, return the most relevant one.
If you can't find an exact match, return the text that most closely resembles what we're looking for.
Return ONLY the extracted information, no labels or formatting."""

    if function_name in ["translate_report", "update_prompt", "show_prompt"]:
        response = bedrock_client.invoke_model(
            modelId="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
            contentType="application/json",
            accept="application/json",
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 4000,
                "temperature": 0.1,
                "top_p": 0.5,
                "system": system_prompt,
                "messages": [{"role": "user", "content": f"Function: {function_name}\n\nText to extract from:\n{result}"}]
            })
        )
        response_body = json.loads(response["body"].read())
        extracted_info = response_body["content"][0]["text"].strip()
        
        # Validate extracted information
        if function_name == "translate_report":
            # Check for URL patterns
            if any(pattern in extracted_info for pattern in ["http://", "https://"]):
                return extracted_info
            # Try direct URL extraction from result
            for line in result.split("\n"):
                if any(pattern in line for pattern in ["http://", "https://", "weave:///"]):
                    return line.strip()
            
        elif function_name == "show_prompt":
            if len(extracted_info) > 10:  # Minimum length check
                return extracted_info
            # Try direct prompt extraction from result
            for line in result.split("\n"):
                if len(line.strip()) > 50:  # Look for substantial text
                    return line.strip()
                    
        elif function_name == "update_prompt":
            if len(extracted_info) > 10:  # Minimum length check
                return extracted_info
            else:
                return ""
    else:
        return ""
    
@weave.op()
def extract_info_from_result_with_llm(result: dict) -> dict:
    """
    Extract information from the agent's response using LLM.
    Args:
        result: Dictionary containing the agent's response and evaluation info
    Returns:
        Dictionary containing extracted function name and relevant information
    """
    try:
        # 関数名の抽出
        function_name = extract_function_name(result["eval_info"])
        if not function_name:
            return {
                "function_name": None,
                "report_url": None,
                "prompt": None,
                "updated_prompt": None
            }
        
        # 出力情報の抽出
        extracted_info = extract_output_info(function_name, result["result"])
        if not extracted_info:
            return {
                "function_name": function_name,
                "report_url": None,
                "prompt": None,
                "updated_prompt": None
            }
        
        # 結果の構築
        result_dict = {
            "function_name": function_name,
            "report_url": None,
            "prompt": None,
            "updated_prompt": None
        }
        
        # 抽出された情報を適切なフィールドに設定
        if function_name == "translate_report":
            result_dict["report_url"] = extracted_info
        elif function_name == "show_prompt":
            result_dict["prompt"] = extracted_info
        elif function_name == "update_prompt":
            try:
                result_dict["updated_prompt"] = weave.ref(extracted_info).get().content
            except Exception as e:
                print(f"Error fetching updated prompt: {e}")
        
        return result_dict
        
    except Exception as e:
        print(f"Error in overall extraction process: {e}")
        return {
            "function_name": None,
            "report_url": None,
            "prompt": None,
            "updated_prompt": None
        }


if __name__ == "__main__":
    main()


