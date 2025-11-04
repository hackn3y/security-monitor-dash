#!/bin/bash

# Deployment script for Security Monitoring Dashboard
# This script deploys the serverless application using AWS SAM

set -e

echo "========================================="
echo "Security Monitoring Dashboard Deployment"
echo "========================================="
echo ""

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "Error: AWS CLI is not installed. Please install it first."
    exit 1
fi

# Check if SAM CLI is installed
if ! command -v sam &> /dev/null; then
    echo "Error: AWS SAM CLI is not installed. Please install it first."
    echo "Visit: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html"
    exit 1
fi

# Get stack name
read -p "Enter stack name (default: security-monitoring): " STACK_NAME
STACK_NAME=${STACK_NAME:-security-monitoring}

# Get AWS region
read -p "Enter AWS region (default: us-east-1): " AWS_REGION
AWS_REGION=${AWS_REGION:-us-east-1}

# Get S3 bucket for deployment artifacts
read -p "Enter S3 bucket name for deployment artifacts: " S3_BUCKET

if [ -z "$S3_BUCKET" ]; then
    echo "Error: S3 bucket name is required"
    exit 1
fi

echo ""
echo "Deployment Configuration:"
echo "  Stack Name: $STACK_NAME"
echo "  Region: $AWS_REGION"
echo "  S3 Bucket: $S3_BUCKET"
echo ""

read -p "Proceed with deployment? (y/n): " CONFIRM
if [ "$CONFIRM" != "y" ]; then
    echo "Deployment cancelled"
    exit 0
fi

echo ""
echo "[1/4] Building SAM application..."
sam build

echo ""
echo "[2/4] Packaging application..."
sam package \
    --output-template-file packaged.yaml \
    --s3-bucket "$S3_BUCKET" \
    --region "$AWS_REGION"

echo ""
echo "[3/4] Deploying to AWS..."
sam deploy \
    --template-file packaged.yaml \
    --stack-name "$STACK_NAME" \
    --capabilities CAPABILITY_IAM \
    --region "$AWS_REGION" \
    --no-fail-on-empty-changeset

echo ""
echo "[4/4] Retrieving stack outputs..."
API_ENDPOINT=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --region "$AWS_REGION" \
    --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' \
    --output text)

DASHBOARD_URL=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --region "$AWS_REGION" \
    --query 'Stacks[0].Outputs[?OutputKey==`DashboardURL`].OutputValue' \
    --output text)

SNS_TOPIC_ARN=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --region "$AWS_REGION" \
    --query 'Stacks[0].Outputs[?OutputKey==`SNSTopicArn`].OutputValue' \
    --output text)

DASHBOARD_BUCKET=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --region "$AWS_REGION" \
    --query 'Stacks[0].Outputs[?OutputKey==`DashboardURL`].OutputValue' \
    --output text | sed 's|http://||' | sed 's|.s3-website.*||')

echo ""
echo "========================================="
echo "Deployment Complete!"
echo "========================================="
echo ""
echo "API Endpoint: $API_ENDPOINT"
echo "SNS Topic ARN: $SNS_TOPIC_ARN"
echo ""

# Upload dashboard to S3
echo "[5/4] Uploading dashboard to S3..."
aws s3 cp dashboard/index.html "s3://$DASHBOARD_BUCKET/index.html" \
    --content-type "text/html" \
    --region "$AWS_REGION"

echo ""
echo "Dashboard URL: $DASHBOARD_URL"
echo ""

# Subscribe to SNS topic
echo "========================================="
echo "SNS Alert Subscription"
echo "========================================="
read -p "Enter email address to receive alerts (or press Enter to skip): " EMAIL

if [ ! -z "$EMAIL" ]; then
    echo "Subscribing $EMAIL to SNS topic..."
    aws sns subscribe \
        --topic-arn "$SNS_TOPIC_ARN" \
        --protocol email \
        --notification-endpoint "$EMAIL" \
        --region "$AWS_REGION"

    echo ""
    echo "Please check your email and confirm the subscription!"
fi

echo ""
echo "========================================="
echo "Next Steps"
echo "========================================="
echo ""
echo "1. Open the dashboard: $DASHBOARD_URL"
echo "2. Configure the API endpoint in the dashboard: $API_ENDPOINT"
echo "3. Confirm SNS email subscription (if configured)"
echo "4. Run the traffic simulator to test:"
echo "   python scripts/traffic-simulator.py --endpoint $API_ENDPOINT --scenario all"
echo ""
echo "Monitoring is now active!"
echo "The system will automatically ingest simulated events every minute."
echo ""
