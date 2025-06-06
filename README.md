# W&B FC-Agent

An automated tool for translating Weights & Biases (W&B) Reports using Amazon Bedrock and Slack integration.

![System Overview](docs/images/overview.png)

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

## System Architecture

The system consists of several components working together to provide seamless translation services:

![Architecture Diagram](docs/images/architecture.png)

### Components

1. **Slack Interface**
   - Handles user interactions through Slack
   - Processes mentions and commands
   - Uses WebSocket API for real-time communication

2. **ECS on Fargate**
   - Minimal deployment configuration
   - Scalable container orchestration
   - Cost-effective resource management

3. **Amazon Bedrock Agent**
   - Manages the translation workflow
   - Processes natural language commands
   - Integrates with Lambda functions for specific tasks

4. **W&B Integration**
   - Handles report access and creation
   - Manages permissions and API interactions
   - Ensures proper content synchronization

- wandb/japan 

## Local Development Setup

### Prerequisites

1. Create a `.env` file with the following environment variables:

```
# W&B Configuration
WANDB_API_KEY=your_wandb_api_key
WANDB_ENTITY=wandb-japan
WANDB_PROJECT=fc-agent # for dev, fc-agent-dev

# Slack Configuration
SLACK_BOT_TOKEN=xoxb-your-slack-bot-token
SLACK_APP_TOKEN=xapp-your-slack-app-token
SLACK_SIGNING_SECRET=your-slack-signing-secret
SLACK_CHANNEL=#fc-agent

# AWS Configuration
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_aws_access_key_id
AWS_SECRET_ACCESS_KEY=your_aws_secret_access_key

# Bedrock Agent Configuration
AGENT_ID=your_agent_id
AGENT_ALIAS_ID=your_agent_alias_id
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
