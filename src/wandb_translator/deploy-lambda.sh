#!/bin/bash

set -e

# ---- Settings ----
ACCOUNT_ID="601636808299"
REGION="us-east-1"
REPO_NAME="fc-agent-wandb-translator"
LAMBDA_NAME="fc-agent-wandb-translator"
ROLE_ARN="arn:aws:iam::601636808299:role/lambda-ex"
LOCAL_IMAGE_NAME="fc-agent-wandb-translator"
TAG="latest"
FULL_URI="$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$REPO_NAME:$TAG"

# ---- 1. ECR Login ----
echo "[1/6] Logging into Amazon ECR..."
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com

# ---- 2. Create ECR repository if not exists ----
echo "[2/6] Creating ECR repository if it does not exist..."
aws ecr describe-repositories --repository-names $REPO_NAME --region $REGION >/dev/null 2>&1 || \
aws ecr create-repository \
  --repository-name $REPO_NAME \
  --region $REGION \
  --image-scanning-configuration scanOnPush=true \
  --image-tag-mutability MUTABLE

# ---- 3. Build and tag Docker image ----
echo "[3/6] Building Docker image..."
docker buildx build --platform linux/amd64 -t $LOCAL_IMAGE_NAME .

echo "[4/6] Tagging image..."
docker tag $LOCAL_IMAGE_NAME:latest $FULL_URI

# ---- 5. Push Docker image to ECR ----
echo "[5/6] Pushing image to ECR..."
docker push $FULL_URI

# ---- 6. Create or update Lambda function ----
echo "[6/6] Deploying Lambda function..."

# Check if function exists
if aws lambda get-function --function-name $LAMBDA_NAME --region $REGION >/dev/null 2>&1; then
  echo "Lambda function exists. Updating code..."
  aws lambda update-function-code \
    --function-name $LAMBDA_NAME \
    --image-uri $FULL_URI \
    --publish \
    --region $REGION
else
  echo "Lambda function does not exist. Creating..."
  aws lambda create-function \
    --function-name $LAMBDA_NAME \
    --package-type Image \
    --code ImageUri=$FULL_URI \
    --role $ROLE_ARN \
    --region $REGION
fi

echo "✅ Deployment complete!"
