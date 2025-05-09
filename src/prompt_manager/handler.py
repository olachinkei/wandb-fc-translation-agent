import os
import weave
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)
weave.init(os.environ["WANDB_ENTITY"] + "/" + os.environ["WANDB_PROJECT"])

PROMPT_NAME = "translate_prompt"

# Get the latest prompt
@weave.op()
def get_current_prompt():
    ref = weave.ref(f"weave:///wandb-japan/fc-agent/object/{PROMPT_NAME}:latest")
    return ref.get().content

# Update the prompt
@weave.op()
def update_prompt(new_prompt: str):
    prompt_obj = weave.StringPrompt(new_prompt)
    weave.publish(prompt_obj, name=PROMPT_NAME)
    return True

@weave.op(call_display_name="lambda_handler_prompt_manager")
def lambda_handler(event, context):
    """
    Lambda handler for Bedrock Agent.
    Expects instructions in event["parameters"]:
      - "show_prompt": Returns the latest prompt
      - "update_prompt": Updates the prompt with the new value
    """
    parameters = event.get("parameters", [])
    param_dict = {p["name"]: p["value"] for p in parameters}
    action = param_dict.get("action")
    
    if action == "show_prompt":
        prompt = get_current_prompt()
        prompt_url = f"weave:///wandb-japan/fc-agent/object/{PROMPT_NAME}:latest"
        result_text = f"Current prompt:\n{prompt}\n\nCurrent prompt's Weave URL:\n{prompt_url}"
    elif action == "update_prompt":
        new_prompt = param_dict.get("prompt")
        if not new_prompt:
            result_text = "Error: No new prompt specified."
        else:
            update_prompt(new_prompt)
            prompt_url = f"weave:///{os.environ['WANDB_ENTITY']}/{os.environ['WANDB_PROJECT']}/object/{PROMPT_NAME}:latest"
            result_text = f"Prompt has been updated.\nNew Prompt URL: {prompt_url}\nUpdated Prompt:\n{new_prompt}"
    else:
        result_text = "Error: Please specify a valid action (show_prompt, update_prompt)."

    response_body = {"TEXT": {"body": result_text}}
    function_response = {
        "actionGroup": event.get("actionGroup", ""),
        "function": event.get("function", ""),
        "functionResponse": {"responseBody": response_body}
    }
    session_attributes = event.get("sessionAttributes", {})
    prompt_session_attributes = event.get("promptSessionAttributes", {})
    action_response = {
        "messageVersion": "1.0",
        "response": function_response,
        "sessionAttributes": session_attributes,
        "promptSessionAttributes": prompt_session_attributes
    }
    return action_response 