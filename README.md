# W&B FC-Translation Agent

An automated tool for translating Weights & Biases (W&B) Reports using Amazon Bedrock and Slack integration.

## Features

- Slack Integration: Mention @fc-agent in the #fc-agent Slack channel to interact with the Amazon Bedrock agent
- Current Available Functions:
  - **Translation**: Provide a W&B Report URL with a translation request (e.g., "translate to Japanese") to receive a URL of the translated report
  - **Prompt Management**:
    - View current prompt: Ask "What is the current prompt?" to see the active translation prompt
    - Update prompt: Request "Update the prompt to {new prompt}" to modify the translation prompt (Updates the [prompt in Weave](https://wandb.ai/wandb-japan/fc-agent/weave/prompts))
- Upcoming Features:
  - Japanese W&B Report mirroring to Note
  - Korean W&B Report mirroring to Medium

## Architecture

- Deployment: ECS on Fargate
- Agent: Amazon Bedrock agent with Lambda function integration
- Communication: Slack WebSocket API

## Local Development Setup

### Prerequisites

1. Create a `.env` file with the following environment variables:

```
WANDB_API_KEY=your_wandb_api_key
SLACK_TOKEN=your_slack_bot_token
AWS_ACCESS_KEY_ID=your_aws_access_key_id
AWS_SECRET_ACCESS_KEY=your_aws_secret_access_key
WANDB_TARGET_PROJECT=wandb-japan/fc-reports  # default
SLACK_CHANNEL=#wandb-translations  # default
AWS_REGION=us-west-2  # default
DEFAULT_LANGUAGE=jp  # default
MAX_CHUNK_SIZE=1000  # default
```

### Installation

1. Set up a virtual environment and install dependencies:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. Start the application:
```bash
python app.py
```

## Testing

The project includes comprehensive test suites:

### Unit Tests
- `tests/unit_test1.py`: Tests for report copying functionality
- `tests/unit_test2.py`: Tests for content translation functionality

### Evaluation Tests
- `tests/eval1.py`: Comprehensive evaluation of translation capability using Weave Evaluation (tests 50 reports)
- `tests/eval2.py`: Evaluation of tool selection and task completion across various scenarios

For detailed testing instructions, please refer to `tests/README.md`. Note that running tests does not require the main application (`app.py`) to be running.

## Current Development Tasks

- Bug fixes for W&B Report copying functionality
- Implementation of Human Feedback system

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.