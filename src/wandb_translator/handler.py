import os
import wandb
import weave
import re
import wandb_workspaces.reports.v2 as wr
import slack_sdk
import sys
import boto3
import json
from typing import Tuple, Optional, List, Dict, Any
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import concurrent.futures
import traceback


# Add src/wandb_translator to sys.path to allow module import
sys.path.append(os.path.dirname(__file__))

@weave.op(call_display_name="lambda_handler_translate_report")
def lambda_handler(event, context):
    """
    Lambda handler compatible with Bedrock function details schema
    """
    
    # Get original_report_url and language from event["parameters"]
    parameters = event.get("parameters", [])
    param_dict = {p["name"]: p["value"] for p in parameters}
    original_report_url = param_dict.get("original_report_url")
    language = param_dict.get("language")

    if not original_report_url:
        return {
            "messageVersion": "1.0",
            "response": {
                "actionGroup": event.get("actionGroup", ""),
                "function": event.get("function", ""),
                "functionResponse": {
                    "responseBody": {
                        "TEXT": {
                            "body": "Error: original_report_url is required."
                        }
                    }
                }
            },
            "sessionAttributes": event.get("sessionAttributes", {}),
            "promptSessionAttributes": event.get("promptSessionAttributes", {})
        }

    # Fix malformed URLs: replace '---' with '--' if present
    if original_report_url and '---' in original_report_url:
        original_report_url = original_report_url.replace('---', '--')

    # Report translation process
    translator = WandBReportTranslator()
    try:
        new_report_url, new_report_title = translator._wandb_report_transformation(
            original_report_url, language
        )
        result_text = f"Translation completed!\nTitle: {new_report_title}\nURL: {new_report_url}"
    except Exception as e:
        result_text = f"Error during translation: {str(e)}"

    # Return response according to Bedrock function details schema
    response_body = {
        "TEXT": {
            "body": result_text
        }
    }
    function_response = {
        "actionGroup": event.get("actionGroup", ""),
        "function": event.get("function", ""),
        "functionResponse": {
            "responseBody": response_body
        }
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

class WandBReportTranslator:
    def __init__(self, notify: bool = True):
        """Initialize the translator with credentials from environment variables."""
        # Initialize AWS Bedrock client
        session = boto3.Session(region_name=os.getenv("AWS_REGION"))
        self.bedrock_client = session.client('bedrock-runtime')
        # Initialize Weave
        self.target_project = f"{os.environ['WANDB_ENTITY']}/{os.environ['WANDB_PROJECT']}"
        weave.init(self.target_project)
        
    @weave.op()
    def _wandb_report_transformation(
        self,
        original_report_url: str,
        language: str
    ) -> Tuple[str, str]:
        """Main function to transform and translate a W&B report.
        
        Args:
            original_report_url: URL of the original W&B report
            language: Target language ('jp' or 'ko' or 'en')
        Returns:
            Tuple of (new_report_url, new_report_title or error message)
        """
        # Fix malformed URLs: replace '---' with '--' if present
        if original_report_url and '---' in original_report_url:
            original_report_url = original_report_url.replace('---', '--')

        # Copy the report and translation
        try:
            source_report = wr.Report.from_url(original_report_url)
        except Exception as e:
            tb = traceback.format_exc()
            print(f"Error loading report from URL: {e}")
            return f"Error loading report: {e}\n{tb}", None

        try:
            if hasattr(source_report, "_model"):
                original_title = source_report._model.title
                original_desc = source_report._model.description
            else:
                original_title = getattr(source_report, "title", "Cloned Report")
                original_desc = getattr(source_report, "description", "Cloned from " + original_report_url)

            translated_title = self._translation(original_title, language)
            translated_desc = self._translation(original_desc, language)

            new_report = wr.Report(
                project=os.getenv("WANDB_PROJECT"),
                entity=os.getenv("WANDB_ENTITY"),
                title=translated_title,
                description=translated_desc
            )

            def translate_block(i):
                block = source_report.blocks[i]
                block_type = type(block).__name__
                if block_type == "UnknownBlock":
                    if block.type in ["image", "image "]:
                        return i, block
                    elif block.type == "default":
                        translated_text = self._translation(self.unknownblock_children_to_list(block.children), language)
                        return i, wr.P(text=translated_text)
                    else:
                        return i, block
                elif block_type in ["P", "H1", "H2", "H3", "BlockQuote", "CalloutBlock", "MarkdownBlock", "MarkdownPanel"]:
                    block.text = self._translation(block.text, language)
                    return i, block
                # CheckedListItem, OrderedListItem, UnorderedListItemはそのまま
                return i, block

            # Parallel translation of blocks with as_completed
            new_blocks = [None] * len(source_report.blocks)
            with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
                futures = {executor.submit(translate_block, i): i for i in range(len(source_report.blocks))}
                for future in concurrent.futures.as_completed(futures):
                    try:
                        i, block = future.result()
                        new_blocks[i] = block
                    except Exception as e:
                        tb = traceback.format_exc()
                        print(f"Error translating block {i}: {e}")
                        return f"Error translating block {i}: {e}\n{tb}", None

            new_report.blocks = new_blocks
            new_report.save()

            return new_report.url, new_report.title
        except Exception as e:
            tb = traceback.format_exc()
            print(f"Error during translation: {e}")
            return f"Error during translation: {e}\n{tb}", None
    
    @weave.op()
    def unknownblock_children_to_list(self, children):
        if not isinstance(children, list):
            return [children]
        list_incline = []
        for child in children:
            if isinstance(child, dict):
                if child.get("inlineCode"):
                    list_incline.append(wr.InlineCode(child.get("text", "")))
                elif child.get("type") == "link":
                    # Extract text from link children
                    for link_child in child.get("children", []):
                        if isinstance(link_child, dict) and "text" in link_child:
                            list_incline.append(link_child["text"])
                elif "text" in child:
                    list_incline.append(child["text"])
                else:
                    list_incline.append(str(child))
            else:
                list_incline.append(str(child))
        return list_incline
    
    @weave.op()
    def _translation(self, text, language):
        # If text is empty, whitespace only, or an empty list, return as is
        if text is None or (isinstance(text, str) and not text.strip()) or (isinstance(text, list) and (not text or all((isinstance(t, str) and not t.strip()) or t is None for t in text))):
            return text
        
        if isinstance(text, list):
            # Convert all items to string, handling InlineCode specially
            placeholders = []
            flat = ""
            
            for i, item in enumerate(text):
                if isinstance(item, wr.InlineCode):
                    ph = f"__INLINECODE_{i}__"
                    flat += ph
                    placeholders.append((ph, item.text))
                else:
                    flat += str(item)
            
            # Translate the flattened text
            translated = self._call_translation_api(flat, language)
            
            # If we had placeholders, restore them but keep everything as a single string
            if placeholders:
                ph_dict = dict(placeholders)
                parts = re.split("(" + "|".join(re.escape(ph) for ph, _ in placeholders) + ")", translated)
                final_text = ""
                for p in parts:
                    if p in ph_dict:
                        final_text += ph_dict[p]
                    elif p:
                        final_text += p
                return final_text
            
            return translated
        
        # If text is a string
        return self._call_translation_api(text, language)

    @weave.op()
    def _call_translation_api(self, text, language):
        """
        Args:
            text: The text to translate. Either a str or a list of [str, wr.InlineCode, ...].
            language: Target language (e.g., 'jp', 'ko', 'en').
        Returns:
            Translated text. Returns a list if input is a list, or a str if input is a str.
        """
        # If text is empty, return as is without calling the API
        if text is None or (isinstance(text, str) and not text.strip()):
            return text
        prompt_language = {"jp": "Japanese", "ko": "Korean", "en": "English"}.get(language, language)
        system_prompt = weave.ref("weave:///wandb-japan/fc-agent/object/translate_prompt:latest").get().content
        payload = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 2000,
            "temperature": 0.1,
            "top_p": 0.5,
            "system": system_prompt.format(prompt_language=prompt_language),
            "messages": [{"role": "user", "content": text}]
        }
        try:
            response = self.bedrock_client.invoke_model(
                modelId="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
                contentType="application/json",
                accept="application/json",
                body=json.dumps(payload)
            )
            response_body = json.loads(response["body"].read().decode("utf-8"))
            return response_body["content"][0]["text"]
        except Exception as e:
            print(f"Error invoking Bedrock model: {e}")
            raise