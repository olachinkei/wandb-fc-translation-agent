# W&B Report Translator Lambda

This directory contains the Lambda function and deployment scripts for translating Weights & Biases (W&B) Reports using Amazon Bedrock and Slack integration.

> **Note**: For detailed information about deploying Python Lambda functions using container images, please refer to the [AWS Lambda Developer Guide](https://docs.aws.amazon.com/lambda/latest/dg/python-image.html).

## Overview

The main Lambda handler (`handler.py`) provides the following features:
- Translates W&B Reports into a target language using Amazon Bedrock models.
- Notifies a specified Slack channel about translation progress and completion.
- Uses Weave for prompt management.

## Files

- `handler.py`: Main Lambda function for report translation.
- `requirements.txt`: Python dependencies for the Lambda function.
- `Dockerfile`: Docker image definition for Lambda deployment.
- `deploy-lambda.sh`: Shell script to build, push, and deploy the Lambda function as a container image.

## How to Deploy

### 1. Configure `deploy-lambda.sh`
Before using `deploy-lambda.sh`, **edit the following variables at the top of the script** to match your AWS environment:

```
ACCOUNT_ID="<your-account-id>"
REGION="<your-region>"
REPO_NAME="<your-ecr-repo-name>"
LAMBDA_NAME="<your-lambda-function-name>"
ROLE_ARN="<your-lambda-execution-role-arn>"
LOCAL_IMAGE_NAME="<your-local-image-name>"
TAG="latest"
FULL_URI="$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$REPO_NAME:$TAG"
```
**Do not commit your actual credentials or account information to version control.**

### 2. Build and Deploy Lambda
Run the following command in this directory:

```sh
./deploy-lambda.sh
```

This script will:
- Log in to Amazon ECR
- Create the ECR repository if it does not exist
- Build the Docker image
- Push the image to ECR
- Create or update the Lambda function with the new image

### 3. Set Environment Variables
After deploying, set the required environment variables for the Lambda function:

```sh
aws lambda update-function-configuration \
  --function-name fc-agent-wandb-translator \
  --environment "Variables={WANDB_API_KEY=YOUR_WANDB_API_KEY,WANDB_ENTITY=YOUR_WANDB_ENTITY,WANDB_PROJECT=YOUR_WANDB_PROJECT,SLACK_BOT_TOKEN=YOUR_SLACK_BOT_TOKEN,SLACK_APP_TOKEN=YOUR_SLACK_APP_TOKEN,SLACK_SIGNING_SECRET=YOUR_SLACK_SIGNING_SECRET,SLACK_CHANNEL=YOUR_SLACK_CHANNEL,AGENT_ID=YOUR_AGENT_ID,AGENT_ALIAS_ID=YOUR_AGENT_ALIAS_ID}"
```
Replace each value with your actual credentials and configuration.

### 4. Add Lambda Invoke Permission for Bedrock Agent
To allow Amazon Bedrock Agent to invoke this Lambda function, run:

```sh
aws lambda add-permission \
  --function-name fc-agent-wandb-translator \
  --statement-id allow-bedrock-agent \
  --action lambda:InvokeFunction \
  --principal bedrock.amazonaws.com
```

## Notes
- Make sure all required environment variables are set, or the Lambda function will fail at runtime.
- The deploy-lambda.sh script should be customized for your environment and **should not contain sensitive information when pushed to version control**.
- Check CloudWatch Logs for troubleshooting Lambda errors.

## Contact
For questions or issues, please contact the repository maintainer. 