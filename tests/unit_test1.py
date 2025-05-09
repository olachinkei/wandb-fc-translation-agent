import os
from dotenv import load_dotenv
from pathlib import Path
from wandb_translator.handler import WandBReportTranslator

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path, override=True)

def test_translate_single_report():
    # 手打ちのW&BレポートURLをここに記載
    #report_url = "https://wandb.ai/wandb_fc/product-announcements-fc/reports/Weights-Biases-is-recognized-by-Gartner-as-an-Emerging-Leader-for-Generative-AI-Engineering-category---VmlldzoxMjAwOTkzMA"
    report_url = "https://wandb.ai/byyoung3/Generative-AI/reports/Sentiment-classification-with-the-Reddit-Praw-API-and-GPT-4o-mini--VmlldzoxMjEwODE3Nw"
    language = "jp"
    translator = WandBReportTranslator(notify=True)
    new_report_url, new_report_title = translator._wandb_report_transformation(report_url, language)
    print(f"New report URL: {new_report_url}")
    print(f"New report title: {new_report_title}")
    assert new_report_url is not None and not str(new_report_url).startswith("Error during translation:"), "Translation failed!"

if __name__ == "__main__":
    test_translate_single_report() 