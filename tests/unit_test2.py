import unittest
import os
import sys

# Add the src directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import invoke_bedrock_agent

class TestBedrockAgentInvocation(unittest.TestCase):
    def test_invoke_bedrock_agent(self):
        # 実際のBedrock Agentを呼び出し
    
        prompt = "https://wandb.ai/byyoung3/Generative-AI/reports/Sentiment-classification-with-the-Reddit-Praw-API-and-GPT-4o-mini--VmlldzoxMjEwODE3Nw を日本語に翻訳してください"
        result = invoke_bedrock_agent(user_input=prompt, mode="eval")
        print("output for wandb-translator:", result)

        prompt = "現状のプロンプトをを見せて"
        result = invoke_bedrock_agent(user_input=prompt, mode="eval")
        print("output for show_prompt:", result)

        prompt = "現状のプロンプトを以下にupdateして Translate the following text to {prompt_language}. \n ### Rules \n- Please do not include any other text than the translation. \n- If it is written by Markdown, please translate it as Markdown. \n- Please keep any parts like __INLINECODE_x__ unchanged during translation. \n- Please keep any parts like __LINK_x__ unchanged during translation.　\n- Please translate the content in a natural and professionalway."
        result = invoke_bedrock_agent(user_input=prompt, mode="eval")
        print("output for update_prompt:", result)

        # 応答の検証
        self.assertIsInstance(result, str)
        self.assertTrue(len(result) > 0)
        print("\nBedrock Agent Response:", result)

if __name__ == '__main__':
    unittest.main()
