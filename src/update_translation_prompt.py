"""
This script updates the translation prompt in Weave.
This script is not used for production. It is only used for development.

Usage:
python update_translation_prompt.py
"""


import weave
import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env file
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path)

# Initialize Weave with the project
weave.init(os.environ["WANDB_ENTITY"] + "/" + os.environ["WANDB_PROJECT"])

# Updated system prompt that handles both link and inline code placeholders
system_prompt = weave.StringPrompt(
    "Translate the following text to {prompt_language}."
    "\n ### Rules"
    "\n- Please do not include any other text than the translation."
    "\n- If it is written by Markdown, please translate it as Markdown."
    "\n- Please keep any parts like __INLINECODE_x__ unchanged during translation."
    "\n- Please keep any parts like __LINK_x__ unchanged during translation."
)

# Publish the updated prompt
weave.publish(system_prompt, name="translate_prompt")
print("Translation prompt updated successfully!") 