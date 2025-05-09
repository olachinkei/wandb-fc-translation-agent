# W&B Report Translator

A tool for automatically translating W&B Reports using Amazon Bedrock and Slack integration.

## Features

- Copy W&B Reports to a target project
- Translate report content using Amazon Bedrock
- Notify Slack about translation progress
- Support for Japanese and Korean translations
- Integration with Weave for prompts and dictionaries
- Secure configuration management using environment variables

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/wandb-fc-translation-agent.git
cd wandb-fc-translation-agent
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up configuration:
```bash
# Copy the template file
cp .env.template .env

# Edit the .env file with your credentials
nano .env
```

The `.env` file should contain:
```bash
# W&B Configuration
WANDB_API_KEY=your_wandb_api_key
WANDB_TARGET_PROJECT=wandb-japan/fc-reports

# Slack Configuration
SLACK_TOKEN=your_slack_token
SLACK_CHANNEL=#wandb-translations

# AWS Configuration
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_REGION=us-west-2

# Translation Configuration
DEFAULT_LANGUAGE=jp
MAX_CHUNK_SIZE=1000
```

## Usage

```python
from wandb_translator.translator import WandBReportTranslator

# Initialize the translator (credentials will be loaded from environment variables)
translator = WandBReportTranslator()

# Or provide credentials explicitly
translator = WandBReportTranslator(
    wandb_api_key="your_wandb_api_key",
    slack_token="your_slack_token",
    bedrock_region="us-west-2",
    target_project="wandb-japan/fc-reports"
)

# Translate a report
new_url, new_title = translator.wandb_report_transformation(
    original_report_url="https://wandb.ai/your-project/your-report",
    language="jp",
    prompt_path="your/prompt/path",
    dictionary_path="your/dictionary/path"
)
```

## Configuration

The application uses a configuration system that supports:

1. Environment variables
2. `.env` file
3. Explicit parameters in the constructor

The configuration is validated on initialization to ensure all required variables are set.

### Required Environment Variables

- `WANDB_API_KEY`: Your W&B API key
- `SLACK_TOKEN`: Your Slack bot token
- `AWS_ACCESS_KEY_ID`: Your AWS access key ID
- `AWS_SECRET_ACCESS_KEY`: Your AWS secret access key

### Optional Environment Variables

- `WANDB_TARGET_PROJECT`: Target project for translated reports (default: "wandb-japan/fc-reports")
- `SLACK_CHANNEL`: Slack channel for notifications (default: "#wandb-translations")
- `AWS_REGION`: AWS region for Bedrock (default: "us-west-2")
- `DEFAULT_LANGUAGE`: Default language for translation (default: "jp")
- `MAX_CHUNK_SIZE`: Maximum size of content chunks for translation (default: 1000)

## Testing

### Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables in `.env` file:
```bash
# W&B Configuration
WANDB_API_KEY=your_wandb_api_key
WANDB_TARGET_PROJECT=wandb-japan/fc-reports

# Slack Configuration
SLACK_TOKEN=your_slack_token
SLACK_CHANNEL=#wandb-translations

# AWS Configuration
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_REGION=us-west-2

# Translation Configuration
DEFAULT_LANGUAGE=jp
MAX_CHUNK_SIZE=1000
```

### Running Tests

Run all tests:
```bash
pytest tests/
```

Run specific test file:
```bash
pytest tests/test_unit1.py
```

Run tests with verbose output:
```bash
pytest -v tests/
```

### Test Structure

The tests are organized as follows:

- `tests/test_unit1.py`: Tests for report copying functionality
- `tests/test_unit2.py`: Tests for content translation functionality

Each test uses actual API calls to verify the functionality.

## Project Structure

```
wandb-fc-translation-agent/
├── src/
│   └── wandb_translator/
│       ├── __init__.py
│       ├── translator.py
│       └── config.py
├── tests/
│   ├── test_unit1.py
│   └── test_unit2.py
├── requirements.txt
├── .env.template
└── README.md
```

## License

MIT License