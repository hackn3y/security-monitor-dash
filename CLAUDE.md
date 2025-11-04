# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A serverless security monitoring dashboard built on AWS that ingests security events, detects threats in real-time using 11 detection rules, and sends alerts via Slack. The system uses Lambda functions triggered by DynamoDB Streams for event-driven threat detection.

**Runtime**: Python 3.13
**Infrastructure**: AWS SAM (Serverless Application Model)
**Primary Services**: Lambda, DynamoDB, API Gateway, SNS, S3, CloudWatch

## Essential Commands

### Build and Deploy
```powershell
# Build SAM application
sam build

# Deploy (first time - interactive prompts)
sam deploy --guided

# Deploy (subsequent - uses saved config)
sam deploy

# View deployment outputs (API endpoint, dashboard URL, SNS topic)
aws cloudformation describe-stacks --stack-name security-monitoring --query 'Stacks[0].Outputs' --output table
```

### Local Development
```powershell
# View Lambda logs in real-time
sam logs -n ThreatDetection --stack-name security-monitoring --tail
sam logs -n SecurityLogIngestion --stack-name security-monitoring --tail

# Test with traffic simulator
python scripts/traffic-simulator.py --endpoint <API_ENDPOINT> --scenario all
python scripts/traffic-simulator.py --endpoint <API_ENDPOINT> --scenario brute-force

# Create CloudWatch dashboard
python scripts/create-cloudwatch-dashboard.py --stack-name security-monitoring --region us-east-1
```

### Query Data
```powershell
# View recent alerts
aws dynamodb scan --table-name SecurityAlerts --limit 10

# View recent events
aws dynamodb scan --table-name SecurityEvents --limit 10

# Check alert counts by severity
aws dynamodb scan --table-name SecurityAlerts --query 'Items[*].severity.S' | ConvertFrom-Json | Group-Object | Select-Object Name, Count
```

## Architecture

### Event Flow (Critical Path)
1. **API Gateway** (`POST /ingest`) → **Ingestion Lambda** (`src/ingestion/handler.py`)
   - Normalizes events into standard schema
   - Stores in DynamoDB `SecurityEvents` table with 30-day TTL

2. **DynamoDB Stream** → **Detection Lambda** (`src/detection/handler.py`)
   - Triggered automatically on new events
   - Runs 11 detection rules against each event
   - Creates alerts in `SecurityAlerts` table
   - Sends Slack notifications for MEDIUM/HIGH/CRITICAL

3. **Dashboard API Lambda** (`src/dashboard/handler.py`) ← **Web Dashboard** (`dashboard/index.html`)
   - Provides REST endpoints: `/events`, `/alerts`, `/stats`
   - Dashboard polls every 30 seconds

### Key DynamoDB Design
- **SecurityEvents**: Partition key = `eventId`, Sort key = `timestamp`
  - GSI: `SourceIpIndex` (enables IP-based threat correlation)
  - Stream enabled (triggers detection Lambda)

- **SecurityAlerts**: Partition key = `alertId`, Sort key = `timestamp`
  - GSI: `SeverityIndex` (enables severity filtering)

### Detection Rule Engine
All threat detection logic is in `src/detection/handler.py`:
- `detect_threats()` orchestrates all 11 rules
- Each rule queries DynamoDB using `SourceIpIndex` for correlation
- Rules are configurable via `src/detection/config.py`

**11 Detection Rules**:
1. Brute force (5+ failed logins in 5 min)
2. Suspicious IPs (Tor nodes, malicious ranges)
3. Privilege escalation (non-admin attempting admin actions)
4. Data exfiltration (>10MB transfers)
5. Port scanning/directory traversal
6. Anomalous time access (2-5 AM UTC)
7. Failed privileged account auth
8. SQL injection patterns
9. API rate limiting (100+ req/min)
10. Credential stuffing (10+ unique usernames)
11. Geo-location anomalies

## Configuration Management

### Detection Thresholds
Edit `src/detection/config.py` to adjust sensitivity:
```python
BRUTE_FORCE_THRESHOLD = 5  # Failed attempts before alert
API_RATE_LIMIT_THRESHOLD = 100  # Requests per minute
CREDENTIAL_STUFFING_THRESHOLD = 10  # Unique usernames
```

After changes: `sam build && sam deploy`

### Slack Integration
Set Lambda environment variable:
```powershell
aws lambda update-function-configuration \
  --function-name ThreatDetection \
  --environment "Variables={...,SLACK_WEBHOOK_URL=https://hooks.slack.com/...}"
```

Alert routing configured in `src/detection/config.py`:
```python
ALERT_SEVERITIES = {
    'MEDIUM': {'send_slack': True, 'send_email': False},
    'HIGH': {'send_slack': True, 'send_email': False},
    'CRITICAL': {'send_slack': True, 'send_email': False}
}
```

## Adding New Detection Rules

1. **Define detection function** in `src/detection/handler.py`:
```python
def detect_new_threat(event_data):
    if <condition>:
        return {
            'rule': 'NEW_THREAT_NAME',
            'severity': 'HIGH',  # LOW/MEDIUM/HIGH/CRITICAL
            'description': 'Description of threat',
            'details': {...}
        }
    return None
```

2. **Register in orchestrator**:
```python
def detect_threats(event_data):
    threats = []
    # ... existing rules ...
    new_threat = detect_new_threat(event_data)
    if new_threat:
        threats.append(new_threat)
    return threats
```

3. **Add configuration** to `src/detection/config.py` if needed

4. **Redeploy**: `sam build && sam deploy`

## Testing Strategy

### Traffic Simulator
Located in `scripts/traffic-simulator.py` - generates realistic attack patterns:
```python
# Scenarios: all, normal, brute-force, suspicious-ip, scanning,
#            privilege-escalation, exfiltration, anomalous-time
```

### Monitoring Alerts
- **Dashboard**: Check real-time at S3 website URL from stack outputs
- **Slack**: Messages appear in configured channel within 1-2 minutes
- **Logs**: `sam logs -n ThreatDetection --tail` shows alert creation

## Important Notes

### Lambda Dependencies
Each Lambda has its own `requirements.txt`. The detection Lambda imports:
- `config.py` - Configuration constants
- `slack_notifier.py` - Slack integration

These must be in the same directory as `handler.py` for SAM to package correctly.

### Event Schema
All events follow this normalized schema (defined in `src/ingestion/handler.py`):
```python
{
    'eventId': uuid,
    'timestamp': unix_timestamp,
    'eventType': 'authentication|api_request|file_access|admin_action|network',
    'sourceIp': string,
    'user': string,
    'action': string,
    'resource': string,
    'statusCode': int,
    'metadata': dict
}
```

### DynamoDB Stream Processing
Detection Lambda processes events in batches (10 events, 5 sec window). The `deserialize_dynamodb_item()` function converts DynamoDB stream format to Python dicts.

### Cost Optimization
- Events auto-delete after 30 days (TTL on `SecurityEvents`)
- DynamoDB uses on-demand billing (no idle costs)
- Simulated events generate every 1 minute (adjustable in `template.yaml` schedule)

## Cleanup
```powershell
# Delete entire stack
aws cloudformation delete-stack --stack-name security-monitoring

# Delete CloudWatch dashboard
aws cloudwatch delete-dashboards --dashboard-names security-monitoring-SecurityMonitoring
```

## References
- **Architecture Details**: See `ARCHITECTURE.md` for component-level documentation
- **Deployment Guide**: See `QUICKSTART.md` for step-by-step setup
- **Slack Setup**: See `SLACK_SETUP.md` for webhook configuration
