# WandB FC Translation Agent - Test Suite

This directory contains test files for the WandB FC Translation Agent, which is designed to translate W&B reports into different languages.

## Environment Setup

This project requires Python 3.10 or later. Here's how to set up your environment:

```bash
# Install Python 3.10+ if not already installed
pyenv install 3.10.13
pyenv local 3.10.13

# Install uv
pip install uv

# Create and activate virtual environment
uv venv
source .venv/bin/activate  # On Unix/macOS
# OR .venv\Scripts\activate  # On Windows

# Install dependencies
uv pip install -r requirements.txt
```

Configure environment variables in a `.env` file at the project root:
```
WANDB_ENTITY=wandb-japan
WANDB_PROJECT=fc-agent-dev
SLACK_BOT_TOKEN=your_slack_bot_token
SLACK_APP_TOKEN=your_slack_app_token
AGENT_ID=your_agent_id
AGENT_ALIAS_ID=your_agent_alias_id
AWS_REGION=your_aws_region
```

To verify your environment variables are set correctly:
```bash
# Check all required environment variables
env | grep -E 'WANDB_|SLACK_|AGENT_|AWS_REGION'

# Or check individual variables
echo $WANDB_ENTITY
echo $WANDB_PROJECT
echo $SLACK_BOT_TOKEN
echo $SLACK_APP_TOKEN
echo $AGENT_ID
echo $AGENT_ALIAS_ID
echo $AWS_REGION
```

> **Note**: This project uses modern Python type annotations that require Python 3.10 or later. If you're using an older version, you'll encounter type annotation errors.

## How to Deploy

For detailed information about deploying Python Lambda functions using container images, please refer to the [AWS Lambda Developer Guide](https://docs.aws.amazon.com/lambda/latest/dg/python-image.html). The guide covers:

- Using Python AWS base images
- Building with alternative base images
- Options for packaging dependencies
- Step-by-step deployment process

The Lambda functions in this project (`src/prompt_manager` and `src/wandb_translator`) follow this container-based deployment approach. See their respective README files for specific deployment instructions.

## Test Files Overview

### 1. unit_test1.py
A simple unit test that tests the translation functionality directly. This test:
- Takes a W&B report URL 
- Passes it to the `WandBReportTranslator` class
- Verifies that the report can be translated successfully

Run this test to validate that the report translation function works in isolation.

### 2. unit_test2.py
Tests the functionality of actually sending queries to the Foundation Client (FC) agent. This test:
- Invokes the Bedrock agent with various prompts
- Tests report translation
- Tests prompt retrieval
- Tests prompt updating

Run this test to validate that the agent responds correctly to different types of requests.

### 3. eval1.py
A comprehensive test for evaluating report translation capabilities. This test:
- Retrieves multiple report URLs from a W&B workspace API
- Attempts to translate each report
- Verifies that each translation was successful
- Records results to W&B for tracking and analysis

Run this test to validate the end-to-end report translation process across a variety of report types.

### 4. eval2.py
A comprehensive test for evaluating tool usage and output accuracy. This test:
- Tests various scenarios for tool usage
- Verifies that the appropriate tools are selected for different inputs
- Evaluates the correctness of tool outputs
- Records detailed metrics to W&B for analysis

This is the most comprehensive test for validating the agent's overall behavior and accuracy.

### 5. print_action_groups.py
A utility script to list all action groups and their details from a Bedrock agent. This helps to:
- Understand what actions are currently registered with the agent
- Verify the structure and parameters of each action
- Debug action-related issues

## Important Notes for Evaluation

When evaluating the agent, please keep in mind:

1. Always use `wandb-japan` as the WANDB_ENTITY and `fc-agent-dev` as the WANDB_PROJECT.

2. Remember that lambda functions used by the agent need to have the same environment variables configured.

3. **Lambda Function Updates**: Changes made locally to lambda functions will not affect the deployed functions. For information on how to update the lambda functions, please refer to:
   - The README in `src/prompt_manager`
   - The README in `src/wandb_translator`

4. **Evaluation Results**: You can view the evaluation results and metrics in the [W&B Evaluations Dashboard](https://wandb.ai/wandb-japan/fc-agent-dev/weave/evaluations?view=evaluations_default).

## Running Tests

To run a specific test, use:
```bash
python -m tests.test_file_name
```

For example, to run unit_test1.py:
```bash
python -m tests.unit_test1
``` 