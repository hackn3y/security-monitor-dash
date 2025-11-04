# Quick Start Guide

Get your Security Monitoring Dashboard up and running in 10 minutes!

## Prerequisites Checklist

- [ ] AWS Account with admin access
- [ ] AWS CLI installed and configured
- [ ] AWS SAM CLI installed
- [ ] Python 3.9+ installed
- [ ] S3 bucket created for deployment artifacts

## Step 1: Install Required Tools

### AWS CLI

**Windows:**
```powershell
msiexec.exe /i https://awscli.amazonaws.com/AWSCLIV2.msi
```

**macOS:**
```bash
brew install awscli
```

**Linux:**
```bash
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
```

### AWS SAM CLI

**Windows:**
```powershell
choco install aws-sam-cli
```

**macOS:**
```bash
brew install aws-sam-cli
```

**Linux:**
```bash
wget https://github.com/aws/aws-sam-cli/releases/latest/download/aws-sam-cli-linux-x86_64.zip
unzip aws-sam-cli-linux-x86_64.zip -d sam-installation
sudo ./sam-installation/install
```

## Step 2: Configure AWS Credentials

```bash
aws configure
```

Enter:
- AWS Access Key ID
- AWS Secret Access Key
- Default region (e.g., us-east-1)
- Default output format (json)

## Step 3: Create S3 Bucket

```bash
# Replace 'your-unique-bucket-name' with a globally unique name
aws s3 mb s3://your-unique-bucket-name
```

## Step 4: Deploy the Application

### Option A: Automated (Recommended)

**Windows:**
```powershell
cd security-monitoring-dashboard
.\scripts\deploy.ps1
```

**macOS/Linux:**
```bash
cd security-monitoring-dashboard
chmod +x scripts/deploy.sh
./scripts/deploy.sh
```

Follow the prompts:
1. Stack name: `security-monitoring` (or your choice)
2. AWS region: `us-east-1` (or your choice)
3. S3 bucket: Enter the bucket name from Step 3
4. Confirm deployment: `y`
5. Email for alerts: Enter your email address

### Option B: Manual

```bash
# Build
sam build

# Deploy
sam deploy --guided
```

Follow the prompts and save your configuration.

## Step 5: Confirm SNS Subscription

1. Check your email inbox
2. Look for "AWS Notification - Subscription Confirmation"
3. Click the confirmation link

## Step 6: Access the Dashboard

The deployment script will output:
- **API Endpoint**: Copy this URL
- **Dashboard URL**: Open this in your browser

In the dashboard:
1. Paste the API Endpoint into the configuration field
2. Click "Save Configuration"
3. Wait for data to load (or proceed to Step 7)

## Step 7: Generate Test Data

```bash
# Install Python dependencies
pip install -r scripts/requirements.txt

# Run traffic simulator with all scenarios
python scripts/traffic-simulator.py \
    --endpoint YOUR-API-ENDPOINT \
    --scenario all
```

Replace `YOUR-API-ENDPOINT` with the endpoint from Step 6.

## Step 8: Verify Everything Works

Within 1-2 minutes, you should see:

1. **Dashboard**:
   - Events appearing in the event table
   - Statistics updating
   - Charts showing data

2. **Email**:
   - Alerts for HIGH and CRITICAL threats detected by the simulator

3. **CloudWatch**:
   ```bash
   sam logs -n ThreatDetection --tail
   ```
   You should see detection logs

## Common Issues

### Issue: "Stack already exists"

**Solution**: Use a different stack name or delete the existing stack:
```bash
aws cloudformation delete-stack --stack-name security-monitoring
```

### Issue: "Bucket does not exist"

**Solution**: Create the S3 bucket:
```bash
aws s3 mb s3://your-bucket-name
```

### Issue: Dashboard shows no data

**Solutions**:
1. Verify API endpoint is correct (should end with `/Prod/`)
2. Check browser console for CORS errors
3. Generate test data with traffic simulator
4. Wait 1-2 minutes for DynamoDB Stream propagation

### Issue: No email alerts received

**Solutions**:
1. Confirm SNS subscription via email
2. Check spam folder
3. Verify simulator generated HIGH/CRITICAL alerts:
   ```bash
   aws dynamodb scan \
       --table-name SecurityAlerts \
       --filter-expression "severity = :sev" \
       --expression-attribute-values '{":sev":{"S":"CRITICAL"}}'
   ```

### Issue: "Unable to locate credentials"

**Solution**: Configure AWS CLI:
```bash
aws configure
```

## Testing Scenarios

### Generate Normal Traffic

```bash
python scripts/traffic-simulator.py \
    --endpoint YOUR-API-ENDPOINT \
    --scenario normal \
    --count 50
```

### Simulate Specific Attacks

**Brute Force:**
```bash
python scripts/traffic-simulator.py \
    --endpoint YOUR-API-ENDPOINT \
    --scenario brute-force
```

**Port Scanning:**
```bash
python scripts/traffic-simulator.py \
    --endpoint YOUR-API-ENDPOINT \
    --scenario scanning
```

**Privilege Escalation:**
```bash
python scripts/traffic-simulator.py \
    --endpoint YOUR-API-ENDPOINT \
    --scenario privilege-escalation
```

## Monitoring Your System

### View Lambda Logs

```bash
# All logs
sam logs --tail

# Specific function
sam logs -n ThreatDetection --tail
```

### Check DynamoDB Tables

```bash
# Count events
aws dynamodb scan \
    --table-name SecurityEvents \
    --select COUNT

# Count alerts
aws dynamodb scan \
    --table-name SecurityAlerts \
    --select COUNT
```

### View CloudWatch Metrics

```bash
# Open CloudWatch console
aws cloudwatch list-metrics \
    --namespace SecurityMonitoring
```

Or visit: https://console.aws.amazon.com/cloudwatch/

## Cost Monitoring

Check your estimated costs:

```bash
# Get current month's estimated charges
aws ce get-cost-and-usage \
    --time-period Start=2024-01-01,End=2024-01-31 \
    --granularity MONTHLY \
    --metrics BlendedCost
```

Or visit: https://console.aws.amazon.com/billing/

Expected cost: $15-40/month for moderate usage

## Cleanup

When you're done testing:

```bash
# Delete the stack
aws cloudformation delete-stack --stack-name security-monitoring

# Wait for deletion to complete
aws cloudformation wait stack-delete-complete --stack-name security-monitoring

# Delete the S3 bucket
aws s3 rb s3://your-bucket-name --force
```

## Next Steps

Now that your system is running:

1. **Customize Detection Rules**: Edit `src/detection/handler.py`
2. **Integrate Real Sources**: Connect CloudTrail, VPC Flow Logs, etc.
3. **Enhance Dashboard**: Modify `dashboard/index.html`
4. **Add More Alerts**: Configure additional SNS subscribers
5. **Set Up Monitoring**: Create CloudWatch dashboards

## Getting Help

- **Documentation**: See [README.md](README.md) for detailed information
- **Architecture**: See [ARCHITECTURE.md](ARCHITECTURE.md) for system design
- **AWS SAM Docs**: https://docs.aws.amazon.com/serverless-application-model/

## Security Checklist for Production

Before using in production:

- [ ] Enable DynamoDB encryption with KMS
- [ ] Add API Gateway authentication
- [ ] Deploy Lambdas in VPC
- [ ] Enable CloudTrail logging
- [ ] Set up AWS Config rules
- [ ] Configure backup strategy
- [ ] Review IAM permissions (least privilege)
- [ ] Enable DynamoDB point-in-time recovery
- [ ] Set up multi-region deployment
- [ ] Configure alerting thresholds
- [ ] Integrate with SIEM system
- [ ] Add CloudFront to dashboard
- [ ] Enable AWS WAF on API Gateway

## Resources

- AWS SAM: https://aws.amazon.com/serverless/sam/
- DynamoDB: https://aws.amazon.com/dynamodb/
- Lambda: https://aws.amazon.com/lambda/
- CloudWatch: https://aws.amazon.com/cloudwatch/

---

**Congratulations!** Your Security Monitoring Dashboard is now running.

Start exploring the dashboard and try different attack scenarios with the traffic simulator.
