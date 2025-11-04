# Deployment Steps

## Prerequisites Check
Run these in PowerShell to verify everything is ready:

```powershell
# 1. Verify SAM CLI
sam --version

# 2. Verify AWS CLI
aws --version

# 3. Verify AWS credentials are configured
aws sts get-caller-identity
```

You should see your IAM user information (not root user).

---

## Step 1: Create S3 Bucket for Deployment

Choose a unique bucket name (S3 bucket names must be globally unique):

```powershell
# Replace YOUR-UNIQUE-NAME with something unique (e.g., your initials + random numbers)
aws s3 mb s3://security-monitoring-deploy-YOUR-UNIQUE-NAME --region us-east-1
```

Example:
```powershell
aws s3 mb s3://security-monitoring-deploy-jd12345 --region us-east-1
```

---

## Step 2: Build the Application

```powershell
sam build
```

This will:
- Package all Lambda functions
- Install Python dependencies
- Prepare for deployment

Expected output: "Build Succeeded"

---

## Step 3: Deploy to AWS

### Option A: Guided Deployment (First Time - Recommended)

```powershell
sam deploy --guided
```

Answer the prompts:
- **Stack Name**: `security-monitoring` (or your choice)
- **AWS Region**: `us-east-1` (or your choice)
- **Confirm changes before deploy**: `Y`
- **Allow SAM CLI IAM role creation**: `Y`
- **Disable rollback**: `N`
- **Save arguments to configuration file**: `Y`
- **SAM configuration file**: Press Enter (use default)
- **SAM configuration environment**: Press Enter (use default)

For each function, when asked "may not have authorization defined, Is this okay?": Enter `Y`

### Option B: Quick Deploy (After First Time)

```powershell
sam deploy
```

---

## Step 4: Get the Outputs

After successful deployment, SAM will display outputs:
- **ApiEndpoint**: Copy this URL (you'll need it for the dashboard)
- **SNSTopicArn**: Copy this for email subscriptions
- **DashboardURL**: This is your dashboard URL

Or retrieve them anytime with:
```powershell
aws cloudformation describe-stacks --stack-name security-monitoring --query 'Stacks[0].Outputs' --output table
```

---

## Step 5: Upload Dashboard to S3

Get your dashboard bucket name:
```powershell
$DASHBOARD_BUCKET = aws cloudformation describe-stacks --stack-name security-monitoring --query 'Stacks[0].Outputs[?OutputKey==`DashboardURL`].OutputValue' --output text
$DASHBOARD_BUCKET = $DASHBOARD_BUCKET -replace 'http://', '' -replace '.s3-website.*', ''
echo $DASHBOARD_BUCKET
```

Upload the dashboard:
```powershell
aws s3 cp dashboard/index.html "s3://$DASHBOARD_BUCKET/index.html" --content-type "text/html"
```

---

## Step 6: Subscribe to SNS Alerts

Get the SNS Topic ARN:
```powershell
$SNS_TOPIC = aws cloudformation describe-stacks --stack-name security-monitoring --query 'Stacks[0].Outputs[?OutputKey==`SNSTopicArn`].OutputValue' --output text
echo $SNS_TOPIC
```

Subscribe your email:
```powershell
# Replace YOUR-EMAIL@EXAMPLE.COM with your actual email
aws sns subscribe --topic-arn $SNS_TOPIC --protocol email --notification-endpoint YOUR-EMAIL@EXAMPLE.COM
```

Check your email and **confirm the subscription**!

---

## Step 7: Access the Dashboard

Get the dashboard URL:
```powershell
aws cloudformation describe-stacks --stack-name security-monitoring --query 'Stacks[0].Outputs[?OutputKey==`DashboardURL`].OutputValue' --output text
```

1. Open this URL in your browser
2. Enter your API Endpoint in the configuration section
3. Click "Save Configuration"
4. The dashboard will start loading data

---

## Step 8: Test with Traffic Simulator

Install Python dependencies:
```powershell
pip install -r scripts/requirements.txt
```

Get your API endpoint:
```powershell
$API_ENDPOINT = aws cloudformation describe-stacks --stack-name security-monitoring --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' --output text
echo $API_ENDPOINT
```

Run the simulator:
```powershell
python scripts/traffic-simulator.py --endpoint $API_ENDPOINT --scenario all
```

This will:
- Generate normal traffic
- Simulate various attacks (brute force, scanning, etc.)
- Trigger security alerts

Wait 1-2 minutes, then check:
- Dashboard for events and alerts
- Your email for HIGH/CRITICAL alerts

---

## Troubleshooting

### Build Fails
```powershell
# Make sure you're in the project directory
cd C:\Users\PC\Documents\security-monitoring-dashboard

# Try build again
sam build
```

### Deploy Fails - "Stack already exists"
```powershell
# Delete the existing stack
aws cloudformation delete-stack --stack-name security-monitoring

# Wait for deletion
aws cloudformation wait stack-delete-complete --stack-name security-monitoring

# Try deploy again
sam deploy --guided
```

### No Data in Dashboard
1. Check API endpoint is correct (should end with `/Prod/`)
2. Wait 1-2 minutes for simulated events to be generated
3. Run traffic simulator to generate test data
4. Check browser console for errors

### View Lambda Logs
```powershell
# View ingestion logs
sam logs -n SecurityLogIngestion --stack-name security-monitoring --tail

# View detection logs
sam logs -n ThreatDetection --stack-name security-monitoring --tail
```

---

## Cleanup (When Done)

To delete everything and avoid charges:

```powershell
# Delete CloudFormation stack
aws cloudformation delete-stack --stack-name security-monitoring

# Wait for deletion
aws cloudformation wait stack-delete-complete --stack-name security-monitoring

# Delete S3 buckets (must be empty first)
aws s3 rb s3://security-monitoring-deploy-YOUR-NAME --force
aws s3 rb s3://DASHBOARD-BUCKET-NAME --force
```

---

## Success Checklist

- [ ] SAM build completed successfully
- [ ] Stack deployed without errors
- [ ] Dashboard accessible via S3 URL
- [ ] API endpoint configured in dashboard
- [ ] SNS email subscription confirmed
- [ ] Traffic simulator generates events
- [ ] Events visible in dashboard
- [ ] Alerts appearing in dashboard
- [ ] Email notifications received for HIGH/CRITICAL alerts

---

**Ready to deploy? Run the commands in order starting from Step 1!**
