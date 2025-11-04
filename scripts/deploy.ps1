# PowerShell Deployment script for Security Monitoring Dashboard
# This script deploys the serverless application using AWS SAM

$ErrorActionPreference = "Stop"

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Security Monitoring Dashboard Deployment" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# Check if AWS CLI is installed
try {
    aws --version | Out-Null
} catch {
    Write-Host "Error: AWS CLI is not installed. Please install it first." -ForegroundColor Red
    exit 1
}

# Check if SAM CLI is installed
try {
    sam --version | Out-Null
} catch {
    Write-Host "Error: AWS SAM CLI is not installed. Please install it first." -ForegroundColor Red
    Write-Host "Visit: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html" -ForegroundColor Yellow
    exit 1
}

# Get stack name
$STACK_NAME = Read-Host "Enter stack name (default: security-monitoring)"
if ([string]::IsNullOrEmpty($STACK_NAME)) {
    $STACK_NAME = "security-monitoring"
}

# Get AWS region
$AWS_REGION = Read-Host "Enter AWS region (default: us-east-1)"
if ([string]::IsNullOrEmpty($AWS_REGION)) {
    $AWS_REGION = "us-east-1"
}

# Get S3 bucket for deployment artifacts
$S3_BUCKET = Read-Host "Enter S3 bucket name for deployment artifacts"

if ([string]::IsNullOrEmpty($S3_BUCKET)) {
    Write-Host "Error: S3 bucket name is required" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Deployment Configuration:" -ForegroundColor Green
Write-Host "  Stack Name: $STACK_NAME"
Write-Host "  Region: $AWS_REGION"
Write-Host "  S3 Bucket: $S3_BUCKET"
Write-Host ""

$CONFIRM = Read-Host "Proceed with deployment? (y/n)"
if ($CONFIRM -ne "y") {
    Write-Host "Deployment cancelled" -ForegroundColor Yellow
    exit 0
}

Write-Host ""
Write-Host "[1/4] Building SAM application..." -ForegroundColor Cyan
sam build

Write-Host ""
Write-Host "[2/4] Packaging application..." -ForegroundColor Cyan
sam package `
    --output-template-file packaged.yaml `
    --s3-bucket $S3_BUCKET `
    --region $AWS_REGION

Write-Host ""
Write-Host "[3/4] Deploying to AWS..." -ForegroundColor Cyan
sam deploy `
    --template-file packaged.yaml `
    --stack-name $STACK_NAME `
    --capabilities CAPABILITY_IAM `
    --region $AWS_REGION `
    --no-fail-on-empty-changeset

Write-Host ""
Write-Host "[4/4] Retrieving stack outputs..." -ForegroundColor Cyan

$API_ENDPOINT = aws cloudformation describe-stacks `
    --stack-name $STACK_NAME `
    --region $AWS_REGION `
    --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' `
    --output text

$DASHBOARD_URL = aws cloudformation describe-stacks `
    --stack-name $STACK_NAME `
    --region $AWS_REGION `
    --query 'Stacks[0].Outputs[?OutputKey==`DashboardURL`].OutputValue' `
    --output text

$SNS_TOPIC_ARN = aws cloudformation describe-stacks `
    --stack-name $STACK_NAME `
    --region $AWS_REGION `
    --query 'Stacks[0].Outputs[?OutputKey==`SNSTopicArn`].OutputValue' `
    --output text

$DASHBOARD_BUCKET = $DASHBOARD_URL -replace 'http://', '' -replace '.s3-website.*', ''

Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Deployment Complete!" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "API Endpoint: $API_ENDPOINT" -ForegroundColor Green
Write-Host "SNS Topic ARN: $SNS_TOPIC_ARN" -ForegroundColor Green
Write-Host ""

# Upload dashboard to S3
Write-Host "[5/4] Uploading dashboard to S3..." -ForegroundColor Cyan
aws s3 cp dashboard/index.html "s3://$DASHBOARD_BUCKET/index.html" `
    --content-type "text/html" `
    --region $AWS_REGION

Write-Host ""
Write-Host "Dashboard URL: $DASHBOARD_URL" -ForegroundColor Green
Write-Host ""

# Subscribe to SNS topic
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "SNS Alert Subscription" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
$EMAIL = Read-Host "Enter email address to receive alerts (or press Enter to skip)"

if (-not [string]::IsNullOrEmpty($EMAIL)) {
    Write-Host "Subscribing $EMAIL to SNS topic..." -ForegroundColor Cyan
    aws sns subscribe `
        --topic-arn $SNS_TOPIC_ARN `
        --protocol email `
        --notification-endpoint $EMAIL `
        --region $AWS_REGION

    Write-Host ""
    Write-Host "Please check your email and confirm the subscription!" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Next Steps" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Open the dashboard: $DASHBOARD_URL" -ForegroundColor White
Write-Host "2. Configure the API endpoint in the dashboard: $API_ENDPOINT" -ForegroundColor White
Write-Host "3. Confirm SNS email subscription (if configured)" -ForegroundColor White
Write-Host "4. Run the traffic simulator to test:" -ForegroundColor White
Write-Host "   python scripts/traffic-simulator.py --endpoint $API_ENDPOINT --scenario all" -ForegroundColor Yellow
Write-Host ""
Write-Host "Monitoring is now active!" -ForegroundColor Green
Write-Host "The system will automatically ingest simulated events every minute." -ForegroundColor Green
Write-Host ""
