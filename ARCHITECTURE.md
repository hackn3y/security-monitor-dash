# Architecture Documentation

## System Architecture Overview

The Serverless Security Monitoring Dashboard is built on AWS serverless technologies, providing a scalable, cost-effective, and fully managed security monitoring solution.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        External Traffic Sources                      │
│              (APIs, Applications, Logs, Simulated Events)            │
└─────────────────────────┬───────────────────────────────────────────┘
                          │
                          ▼
                    ┌──────────┐
                    │   API    │
                    │ Gateway  │
                    └────┬─────┘
                         │
                         ▼
         ┌───────────────────────────────┐
         │   Log Ingestion Lambda        │
         │   - Normalize events          │
         │   - Validate data             │
         │   - Enrich metadata           │
         └───────────┬───────────────────┘
                     │
                     ▼
         ┌───────────────────────────┐
         │  DynamoDB Events Table    │
         │  - Event storage          │
         │  - GSI on sourceIp        │
         │  - 30-day TTL             │
         │  - Streams enabled        │
         └───────────┬───────────────┘
                     │
                     │ DynamoDB Stream
                     ▼
         ┌───────────────────────────────┐
         │   Threat Detection Lambda     │
         │   - Brute force detection     │
         │   - Suspicious IP detection   │
         │   - Privilege escalation      │
         │   - Data exfiltration         │
         │   - Network scanning          │
         │   - Anomaly detection         │
         └───────┬───────────────────────┘
                 │
        ┌────────┴────────┐
        │                 │
        ▼                 ▼
┌─────────────┐   ┌──────────────┐
│  Alerts     │   │  SNS Topic   │
│  Table      │   │  - Email     │
│  (DynamoDB) │   │  - SMS       │
└──────┬──────┘   └──────────────┘
       │
       │
       ▼
┌─────────────────────┐
│  Dashboard API      │
│  Lambda             │
│  - GET /events      │
│  - GET /alerts      │
│  - GET /stats       │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│  Web Dashboard      │
│  (S3 Static Site)   │
│  - Real-time view   │
│  - Auto-refresh     │
│  - Analytics        │
└─────────────────────┘

       ┌──────────────────┐
       │   CloudWatch     │
       │   - Metrics      │
       │   - Logs         │
       │   - Alarms       │
       └──────────────────┘
```

## Component Details

### 1. API Gateway

**Purpose**: Entry point for security event ingestion

**Features**:
- RESTful API endpoints
- CORS enabled for dashboard
- Request validation
- Throttling and rate limiting
- Integration with Lambda

**Endpoints**:
- `POST /ingest` - Ingest security events
- `GET /events` - Query events
- `GET /alerts` - Query alerts
- `GET /stats` - Get statistics

### 2. Log Ingestion Lambda

**Runtime**: Python 3.11

**Triggers**:
- API Gateway POST requests
- CloudWatch Events (scheduled - every 1 minute for simulation)

**Responsibilities**:
1. Receive events from multiple sources
2. Normalize event data into standard schema
3. Validate and sanitize input
4. Enrich events with metadata
5. Store in DynamoDB with TTL
6. Send metrics to CloudWatch

**Event Schema**:
```json
{
  "eventId": "uuid",
  "timestamp": 1234567890,
  "ttl": 1234567890,
  "eventType": "authentication|api_request|file_access|admin_action|network",
  "sourceIp": "192.168.1.100",
  "destinationIp": "10.0.0.100",
  "user": "username",
  "action": "login|GET|POST|scan|...",
  "resource": "/api/endpoint",
  "userAgent": "...",
  "requestMethod": "GET|POST|PUT|DELETE",
  "statusCode": 200,
  "responseTime": 150,
  "bytesTransferred": 5000,
  "metadata": {}
}
```

### 3. DynamoDB Events Table

**Purpose**: Store all security events with efficient querying

**Schema**:
- **Primary Key**:
  - Partition Key: `eventId` (String)
  - Sort Key: `timestamp` (Number)
- **Attributes**: eventType, sourceIp, user, action, resource, etc.
- **TTL**: 30 days (configurable)
- **Stream**: Enabled (NEW_IMAGE)

**Global Secondary Index**:
- **SourceIpIndex**:
  - Partition Key: `sourceIp`
  - Sort Key: `timestamp`
  - Projection: ALL
  - Purpose: Query events by source IP for threat correlation

**Settings**:
- Billing Mode: PAY_PER_REQUEST (on-demand)
- Point-in-time Recovery: Recommended for production
- Encryption: AWS owned keys (upgrade to KMS for production)

### 4. Threat Detection Lambda

**Runtime**: Python 3.11

**Trigger**: DynamoDB Stream from Events Table
- Batch Size: 10 events
- Maximum Batching Window: 5 seconds
- Starting Position: LATEST

**Detection Rules**:

1. **Brute Force Detection**
   - Monitors: Failed login attempts
   - Threshold: 5 failures in 5 minutes from same IP
   - Severity: HIGH
   - Query: Uses SourceIpIndex

2. **Suspicious IP Detection**
   - Monitors: All connections
   - Check: IP against threat intelligence
   - Severity: MEDIUM
   - Data: Simulated threat feeds (integrate real feeds in production)

3. **Privilege Escalation**
   - Monitors: Admin actions
   - Check: User permissions vs. attempted action
   - Severity: CRITICAL
   - Logic: Non-admin attempting admin operations

4. **Data Exfiltration**
   - Monitors: Data transfers
   - Threshold: > 10MB in single request
   - Severity: HIGH
   - Check: bytesTransferred field

5. **Network Scanning**
   - Monitors: 404 errors, probe attempts
   - Patterns: /.env, /admin, /.git, etc.
   - Severity: MEDIUM
   - Logic: Common attack path enumeration

6. **Anomalous Time Access**
   - Monitors: Sensitive resource access
   - Check: Time window (2-5 AM UTC)
   - Severity: LOW
   - Logic: Off-hours access to critical systems

7. **Failed Privileged Authentication**
   - Monitors: Admin/root login failures
   - Severity: MEDIUM
   - Logic: Attempts on privileged accounts

**Processing Flow**:
```
Event → Parse Stream Record
     → Apply Detection Rules
     → Generate Alerts
     → Store in Alerts Table
     → Send SNS Notification (HIGH/CRITICAL)
     → Update CloudWatch Metrics
```

### 5. DynamoDB Alerts Table

**Purpose**: Store generated security alerts

**Schema**:
- **Primary Key**:
  - Partition Key: `alertId` (String)
  - Sort Key: `timestamp` (Number)
- **Attributes**: severity, rule, description, details, sourceEvent, status

**Global Secondary Index**:
- **SeverityIndex**:
  - Partition Key: `severity`
  - Sort Key: `timestamp`
  - Projection: ALL
  - Purpose: Query by alert severity

**Alert Statuses**:
- `OPEN`: New alert requiring attention
- `ACKNOWLEDGED`: Alert reviewed but not resolved
- `RESOLVED`: Alert fully addressed

**Settings**:
- Billing Mode: PAY_PER_REQUEST
- No TTL (retain alert history)

### 6. SNS Topic

**Purpose**: Send real-time notifications for security alerts

**Supported Protocols**:
- Email
- SMS
- HTTP/HTTPS webhooks
- AWS Lambda
- SQS queues

**Message Format**:
```
Subject: Security Alert: [RULE_NAME] ([SEVERITY])

Body:
SECURITY ALERT - [SEVERITY]

Rule: [RULE_NAME]
Description: [DESCRIPTION]

Event Details:
- Source IP: [IP]
- User: [USER]
- Resource: [RESOURCE]
- Event Type: [TYPE]

Alert ID: [UUID]
Timestamp: [ISO8601]

Additional Details:
[JSON]
```

**Filtering**:
- Only HIGH and CRITICAL alerts trigger notifications
- Prevents alert fatigue

### 7. Dashboard API Lambda

**Runtime**: Python 3.11

**Trigger**: API Gateway

**Endpoints**:

1. **GET /events**
   - Query Parameters: `limit`, `eventType`, `sourceIp`
   - Returns: Recent security events
   - Sorting: Timestamp descending

2. **GET /alerts**
   - Query Parameters: `limit`, `severity`, `status`
   - Returns: Security alerts
   - Filtering: By severity or status

3. **GET /stats**
   - Returns: Aggregated statistics
   - Includes:
     - Overview (counts by status)
     - Events by hour/day
     - Events by type
     - Alerts by severity
     - Top source IPs
     - Top users
     - Recent critical alerts

**Response Format**: JSON with CORS headers

### 8. Web Dashboard

**Hosting**: S3 Static Website

**Technology**:
- Pure HTML/CSS/JavaScript
- No framework dependencies
- Responsive design
- Real-time updates

**Features**:
1. **Statistics Cards**:
   - Total Events (24h)
   - Total Alerts
   - Open Alerts
   - Critical Alerts

2. **Alert Timeline**:
   - Color-coded by severity
   - Detailed alert information
   - Timestamp and source details

3. **Event Analytics**:
   - Bar charts for event distribution
   - Top source IPs visualization
   - Event type breakdown

4. **Event Table**:
   - Sortable, filterable
   - Shows recent 50 events
   - Detailed event attributes

5. **Auto-Refresh**:
   - 30-second refresh interval
   - Last update timestamp

**Configuration**:
- Stores API endpoint in localStorage
- One-time setup per browser

### 9. CloudWatch

**Metrics** (Namespace: SecurityMonitoring):
- `EventsIngested`: Count of ingested events
- `EventsFailed`: Failed ingestion attempts
- `AlertsGenerated`: Total alerts created
- `CriticalAlerts`: Critical severity count

**Logs**:
- `/aws/lambda/SecurityLogIngestion`
- `/aws/lambda/ThreatDetection`
- `/aws/lambda/AlertNotification`
- `/aws/lambda/DashboardAPI`

**Alarms**:
- `HighSeveritySecurityAlerts`: Triggers on CriticalAlerts >= 1

## Data Flow Scenarios

### Normal Event Processing

```
1. Event arrives at API Gateway
2. Ingestion Lambda validates and normalizes
3. Event stored in DynamoDB with TTL
4. CloudWatch metrics updated
5. DynamoDB Stream triggers Detection Lambda
6. Detection Lambda analyzes event
7. No threats detected - processing complete
8. Event visible in dashboard immediately
```

### Threat Detection and Alerting

```
1. Event arrives and stored in DynamoDB
2. DynamoDB Stream triggers Detection Lambda
3. Detection Lambda identifies threat pattern
4. Alert created in Alerts Table:
   - Alert record saved
   - Severity assigned
   - Source event linked
5. If HIGH/CRITICAL:
   - SNS notification sent
   - Email delivered to subscribers
6. CloudWatch metrics updated
7. Dashboard shows new alert in real-time
```

### Dashboard Query Flow

```
1. User opens dashboard
2. JavaScript makes 3 parallel API calls:
   - GET /stats
   - GET /alerts
   - GET /events
3. API Gateway routes to Dashboard Lambda
4. Lambda queries DynamoDB tables
5. Aggregates and formats data
6. Returns JSON with CORS headers
7. Dashboard renders visualizations
8. Auto-refresh every 30 seconds
```

## Scalability Considerations

### Horizontal Scaling

- **Lambda**: Automatically scales to handle concurrent requests
- **DynamoDB**: On-demand billing scales with load
- **API Gateway**: No scaling required, handles any load

### Performance Optimization

1. **DynamoDB**:
   - GSI for efficient queries
   - TTL for automatic data cleanup
   - Stream for event-driven processing

2. **Lambda**:
   - Minimal cold starts (Python runtime)
   - Connection pooling for AWS SDK
   - Batch processing for stream events

3. **API Gateway**:
   - Caching (can be enabled)
   - Request throttling
   - Regional endpoints

### Cost Optimization

1. **DynamoDB TTL**: Automatic deletion of old events
2. **On-demand billing**: Pay only for what you use
3. **Lambda memory**: Optimized for cost/performance
4. **CloudWatch Logs**: Configurable retention period

## Security Architecture

### Authentication & Authorization

- **API Gateway**: Can be enhanced with:
  - API Keys
  - IAM authentication
  - Cognito user pools
  - Lambda authorizers

- **Lambda**: IAM roles with least privilege

### Data Protection

- **In Transit**:
  - HTTPS for all API calls
  - TLS 1.2+ enforced

- **At Rest**:
  - DynamoDB encryption (AWS owned keys)
  - Upgrade to KMS for customer-managed keys

### Network Security

- **VPC Integration**:
  - Can deploy Lambdas in VPC
  - Access internal resources
  - Use VPC endpoints for AWS services

### Monitoring & Compliance

- **CloudTrail**: API activity logging
- **CloudWatch**: Operational monitoring
- **AWS Config**: Resource compliance
- **GuardDuty**: Integrated threat detection

## High Availability

### Region Design

- Single-region deployment by default
- Multi-region option:
  - DynamoDB Global Tables
  - Route 53 for failover
  - Cross-region replication

### Fault Tolerance

- **Lambda**: Automatic retries
- **DynamoDB**: Multi-AZ by default
- **API Gateway**: Multi-AZ by default
- **SNS**: Message durability

### Disaster Recovery

- **RTO/RPO**: Near-zero (serverless benefits)
- **Backups**:
  - DynamoDB point-in-time recovery
  - CloudFormation for infrastructure
  - S3 versioning for dashboard

## Integration Points

### Existing Systems

The system can integrate with:

1. **AWS Services**:
   - CloudTrail logs
   - VPC Flow Logs
   - GuardDuty findings
   - WAF logs
   - ALB/NLB logs

2. **Third-party**:
   - SIEM systems
   - Threat intelligence feeds
   - Ticketing systems (Jira, ServiceNow)
   - Chat platforms (Slack, Teams)

3. **Custom Applications**:
   - REST API for event submission
   - Webhook notifications
   - Custom Lambda integrations

## Future Enhancements

1. **Machine Learning**:
   - Anomaly detection with SageMaker
   - Behavioral analysis
   - Predictive alerting

2. **Advanced Analytics**:
   - Athena for complex queries
   - QuickSight for BI dashboards
   - OpenSearch for full-text search

3. **Incident Response**:
   - Automated remediation
   - Playbook execution
   - Integration with security orchestration

4. **Enhanced UI**:
   - React/Vue dashboard
   - Mobile app
   - Real-time WebSocket updates

## Deployment Considerations

### Prerequisites

- AWS account with permissions for:
  - CloudFormation
  - Lambda
  - DynamoDB
  - API Gateway
  - SNS
  - S3
  - CloudWatch
  - IAM

### Deployment Regions

Recommended regions:
- `us-east-1` (N. Virginia) - Most services available
- `us-west-2` (Oregon)
- `eu-west-1` (Ireland)
- `ap-southeast-1` (Singapore)

### Resource Naming

All resources prefixed with stack name for easy identification and management.

## Maintenance

### Monitoring

- Review CloudWatch dashboards daily
- Check alert patterns weekly
- Analyze cost trends monthly

### Updates

- Lambda runtime updates (managed by AWS)
- Security patches (no OS to patch)
- Application code updates via SAM deploy

### Backup Strategy

- DynamoDB: Enable point-in-time recovery
- Code: Version control (Git)
- Configuration: CloudFormation templates

## Conclusion

This architecture provides a robust, scalable, and cost-effective security monitoring solution using AWS serverless technologies. The event-driven design ensures real-time threat detection while maintaining low operational overhead.
