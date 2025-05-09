import os
import pytest
from pathlib import Path
from dotenv import load_dotenv
import weave
from weave.flow.eval_imperative import EvaluationLogger
from wandb_translator.handler import WandBReportTranslator

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path, override=True)
dataset_name = "evaluation-report-list:v0"

# Example input data (replace with your actual dataset if needed)
def get_eval_samples():

    weave.init(os.environ["WANDB_ENTITY"] + "/" + os.environ["WANDB_PROJECT"])
    report_list = weave.ref(dataset_name).get().to_pandas()
    samples = []
    for _, row in report_list.iterrows():
        samples.append({
            'inputs': {'report_url': row['report_url'], 'title': row['title'],'language': 'Japanese'},
            'expected': True 
        })
    return samples

# Example model logic (translator)
@weave.op
def wandb_report_translator(report_url: str, language: str, report_title: str) -> str:
    translator = WandBReportTranslator(notify=False)
    new_report_url, _ = translator._wandb_report_transformation(report_url, language)
    return new_report_url

def test_translate_report():
    weave.init(os.environ["WANDB_ENTITY"] + "/" + os.environ["WANDB_PROJECT"])

    eval_logger = EvaluationLogger(
        model="WandBReportTranslator",
        dataset=dataset_name
    )
    eval_samples = get_eval_samples()

    success_scores = []
    for sample in eval_samples:
        inputs = sample["inputs"]
        model_output = wandb_report_translator(report_url=inputs["report_url"], language=inputs["language"], report_title=inputs["title"])

        pred_logger = eval_logger.log_prediction(
            inputs=inputs,
            output=model_output
        )

        correctness_score = not (isinstance(model_output, str) and model_output.startswith("Error"))
        pred_logger.log_score(
            scorer="success",
            score=correctness_score
        )
        pred_logger.finish()

        success_scores.append(correctness_score)

    success_rate = sum(success_scores) / len(success_scores) if success_scores else 0.0
    summary_stats = {"success_score": success_rate}
    eval_logger.log_summary(summary_stats)
    print("Evaluation logging complete. View results in the Weave UI.")


def main():
    test_translate_report()

if __name__ == "__main__":
    main()
