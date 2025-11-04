# Slack Integration Setup Guide

## Step 1: Create Slack Incoming Webhook

1. Go to your Slack workspace
2. Visit: https://api.slack.com/messaging/webhooks
3. Click **"Create your Slack app"**
4. Choose **"From scratch"**
5. Enter app name: `Security Monitor`
6. Select your workspace
7. Click **"Create App"**

## Step 2: Enable Incoming Webhooks

1. In your app settings, click **"Incoming Webhooks"**
2. Toggle **"Activate Incoming Webhooks"** to ON
3. Click **"Add New Webhook to Workspace"**
4. Select the channel where you want alerts (e.g., `#security-alerts`)
5. Click **"Allow"**
6. Copy the Webhook URL (looks like: `https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXX`)

## Step 3: Configure Lambda Environment Variable

### Option A: Via AWS Console

1. Go to AWS Lambda Console
2. Find function: `ThreatDetection`
3. Go to **Configuration** → **Environment variables**
4. Click **Edit**
5. Add new variable:
   - **Key**: `SLACK_WEBHOOK_URL`
   - **Value**: (paste your webhook URL)
6. Click **Save**

### Option B: Via AWS CLI

```powershell
# Set your webhook URL
$WEBHOOK_URL = "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"

# Update Lambda function
aws lambda update-function-configuration `
    --function-name ThreatDetection `
    --environment "Variables={EVENTS_TABLE=SecurityEvents,ALERTS_TABLE=SecurityAlerts,SNS_TOPIC_ARN=your-sns-arn,SLACK_WEBHOOK_URL=$WEBHOOK_URL}"
```

## Step 4: Test Slack Integration

Run the traffic simulator to generate alerts:

```powershell
$API_ENDPOINT = aws cloudformation describe-stacks --stack-name security-monitoring --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' --output text

python scripts/traffic-simulator.py --endpoint $API_ENDPOINT --scenario brute-force
```

Within 1-2 minutes, you should see alerts in your Slack channel!

## Customizing Slack Alerts

### Change Alert Severity Levels

Edit `src/detection/config.py`:

```python
ALERT_SEVERITIES = {
    'LOW': {
        'send_slack': False,  # Don't send LOW alerts to Slack
        'send_email': False,
    },
    'MEDIUM': {
        'send_slack': True,   # Send MEDIUM alerts to Slack
        'send_email': False,
    },
    'HIGH': {
        'send_slack': True,   # Send HIGH alerts to Slack
        'send_email': False,
    },
    'CRITICAL': {
        'send_slack': True,   # Send CRITICAL alerts to Slack
        'send_email': True,   # Also send emails for CRITICAL
    }
}
```

After making changes, redeploy:
```powershell
sam build && sam deploy
```

## Slack Alert Format

Alerts will appear in Slack with:
- **Color-coded** by severity (Red=Critical, Orange=High, Yellow=Medium, Green=Low)
- **Emoji indicators** (🚨 Critical, ⚠️ High, 🔶 Medium, ℹ️ Low)
- **Detailed information**:
  - Source IP
  - User
  - Resource accessed
  - Event type
  - Additional threat details
- **Alert ID** for tracking

## Troubleshooting

### Not receiving Slack notifications?

1. **Check Lambda logs**:
   ```powershell
   sam logs -n ThreatDetection --stack-name security-monitoring --tail
   ```

2. **Verify webhook URL is set**:
   ```powershell
   aws lambda get-function-configuration --function-name ThreatDetection --query 'Environment.Variables.SLACK_WEBHOOK_URL'
   ```

3. **Test webhook directly**:
   ```powershell
   curl -X POST -H 'Content-type: application/json' `
       --data '{"text":"Test message from Security Monitor"}' `
       YOUR_WEBHOOK_URL
   ```

4. **Check alert severity** - Only MEDIUM, HIGH, and CRITICAL alerts are sent to Slack by default

### Webhook expired?

Slack webhooks can expire if the app is removed. Create a new webhook and update the Lambda environment variable.

## Advanced: Multiple Channels

To send different severity alerts to different channels:

1. Create multiple webhooks (one per channel)
2. Modify `src/detection/slack_notifier.py` to use different webhooks based on severity
3. Store multiple webhook URLs in environment variables

Example:
```python
# In slack_notifier.py
def send_slack_alert(alert, webhook_url=None):
    severity = alert.get('severity')

    # Route to different channels based on severity
    if severity == 'CRITICAL':
        webhook = os.environ.get('SLACK_WEBHOOK_CRITICAL')
    elif severity in ['HIGH', 'MEDIUM']:
        webhook = os.environ.get('SLACK_WEBHOOK_GENERAL')
    else:
        webhook = os.environ.get('SLACK_WEBHOOK_LOW')

    # ... rest of the code
```

## Security Best Practices

1. **Never commit webhook URLs to git** - Always use environment variables
2. **Rotate webhooks periodically** - Create new webhooks every 90 days
3. **Limit channel access** - Only security team should have access to security-alerts channel
4. **Monitor webhook usage** - Check Slack app analytics for unusual activity

---

**Your Slack integration is ready! Alerts will now appear in your configured channel.** 🎉
