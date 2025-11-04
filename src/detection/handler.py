import json
import boto3
import os
import uuid
import time
from datetime import datetime, timedelta
from collections import defaultdict
from decimal import Decimal

# Import configuration and Slack notifier
try:
    from config import *
    from slack_notifier import send_slack_alert
except ImportError:
    # Fallback if modules not found (shouldn't happen in Lambda)
    print("Warning: Could not import config or slack_notifier modules")
    BRUTE_FORCE_THRESHOLD = 5
    BRUTE_FORCE_TIME_WINDOW = 300

dynamodb = boto3.resource('dynamodb')
sns = boto3.client('sns')
cloudwatch = boto3.client('cloudwatch')

events_table = dynamodb.Table(os.environ['EVENTS_TABLE'])
alerts_table = dynamodb.Table(os.environ['ALERTS_TABLE'])
sns_topic_arn = os.environ['SNS_TOPIC_ARN']

# In-memory cache for rate limiting detection (Lambda container reuse)
event_cache = defaultdict(list)

def lambda_handler(event, context):
    """
    Analyzes security events from DynamoDB stream and detects threats.
    Triggers alerts for suspicious activities.
    """

    alerts_generated = 0

    try:
        for record in event['Records']:
            if record['eventName'] == 'INSERT':
                # Parse the new event
                event_data = deserialize_dynamodb_item(record['dynamodb']['NewImage'])

                # Run threat detection rules
                detected_threats = detect_threats(event_data)

                # Generate alerts for detected threats
                for threat in detected_threats:
                    create_alert(threat, event_data)
                    alerts_generated += 1

        # Send metrics to CloudWatch
        if alerts_generated > 0:
            send_alert_metrics(alerts_generated)

        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': f'Processed {len(event["Records"])} events',
                'alerts_generated': alerts_generated
            })
        }

    except Exception as e:
        print(f"Error in threat detection: {str(e)}")
        raise

def detect_threats(event_data):
    """
    Applies multiple threat detection rules to identify suspicious activity.
    Returns a list of detected threats.
    """
    threats = []

    # Rule 1: Brute Force Detection
    brute_force = detect_brute_force(event_data)
    if brute_force:
        threats.append(brute_force)

    # Rule 2: Suspicious IP Detection
    suspicious_ip = detect_suspicious_ip(event_data)
    if suspicious_ip:
        threats.append(suspicious_ip)

    # Rule 3: Privilege Escalation
    privilege_escalation = detect_privilege_escalation(event_data)
    if privilege_escalation:
        threats.append(privilege_escalation)

    # Rule 4: Data Exfiltration
    data_exfiltration = detect_data_exfiltration(event_data)
    if data_exfiltration:
        threats.append(data_exfiltration)

    # Rule 5: Port Scanning / Probing
    scanning = detect_scanning(event_data)
    if scanning:
        threats.append(scanning)

    # Rule 6: Anomalous Time Access
    anomalous_time = detect_anomalous_time_access(event_data)
    if anomalous_time:
        threats.append(anomalous_time)

    # Rule 7: Multiple Failed Authentications
    failed_auth = detect_failed_authentication(event_data)
    if failed_auth:
        threats.append(failed_auth)

    # Rule 8: SQL Injection Detection
    sql_injection = detect_sql_injection(event_data)
    if sql_injection:
        threats.append(sql_injection)

    # Rule 9: API Rate Limit Violation
    rate_limit = detect_rate_limit_violation(event_data)
    if rate_limit:
        threats.append(rate_limit)

    # Rule 10: Credential Stuffing
    credential_stuffing = detect_credential_stuffing(event_data)
    if credential_stuffing:
        threats.append(credential_stuffing)

    # Rule 11: Geo-location Anomaly
    geo_anomaly = detect_geo_anomaly(event_data)
    if geo_anomaly:
        threats.append(geo_anomaly)

    return threats

def detect_brute_force(event_data):
    """
    Detects brute force attacks by tracking failed login attempts.
    """
    if event_data.get('eventType') != 'authentication':
        return None

    if event_data.get('action') != 'login_failed':
        return None

    source_ip = event_data.get('sourceIp')

    # Query recent failed attempts from this IP
    try:
        time_window_ago = int(time.time()) - BRUTE_FORCE_TIME_WINDOW

        response = events_table.query(
            IndexName='SourceIpIndex',
            KeyConditionExpression='sourceIp = :ip AND #ts >= :timestamp',
            ExpressionAttributeNames={'#ts': 'timestamp'},
            ExpressionAttributeValues={
                ':ip': source_ip,
                ':timestamp': time_window_ago
            }
        )

        failed_attempts = [
            item for item in response.get('Items', [])
            if item.get('eventType') == 'authentication' and item.get('action') == 'login_failed'
        ]

        # Threshold: Configurable failed attempts in configurable time window
        if len(failed_attempts) >= BRUTE_FORCE_THRESHOLD:
            return {
                'rule': 'BRUTE_FORCE_DETECTION',
                'severity': 'HIGH',
                'description': f'Brute force attack detected from {source_ip}',
                'details': {
                    'failed_attempts': len(failed_attempts),
                    'time_window': '5 minutes',
                    'target_user': event_data.get('user')
                }
            }

    except Exception as e:
        print(f"Error in brute force detection: {str(e)}")

    return None

def detect_suspicious_ip(event_data):
    """
    Detects requests from known suspicious IP ranges or Tor exit nodes.
    """
    source_ip = event_data.get('sourceIp')

    # Simulated suspicious IP ranges (in production, use threat intelligence feeds)
    suspicious_ranges = [
        '185.220.',  # Tor exit nodes
        '45.142.',   # Known malicious
        '123.45.67'  # Example suspicious range
    ]

    for suspicious_range in suspicious_ranges:
        if source_ip.startswith(suspicious_range):
            return {
                'rule': 'SUSPICIOUS_IP_DETECTION',
                'severity': 'MEDIUM',
                'description': f'Request from suspicious IP: {source_ip}',
                'details': {
                    'ip_category': 'potential_tor_or_vpn',
                    'action': event_data.get('action'),
                    'resource': event_data.get('resource')
                }
            }

    return None

def detect_privilege_escalation(event_data):
    """
    Detects attempts to escalate privileges or access admin resources.
    """
    if event_data.get('eventType') != 'admin_action':
        return None

    user = event_data.get('user')
    action = event_data.get('action')

    # Check if non-admin user is attempting admin actions
    non_admin_users = ['user1', 'user2', 'guest', 'api_user']

    if user in non_admin_users and action in ['user_create', 'user_delete', 'permission_change']:
        return {
            'rule': 'PRIVILEGE_ESCALATION',
            'severity': 'CRITICAL',
            'description': f'Privilege escalation attempt by {user}',
            'details': {
                'user': user,
                'action': action,
                'resource': event_data.get('resource')
            }
        }

    return None

def detect_data_exfiltration(event_data):
    """
    Detects potential data exfiltration based on large data transfers.
    """
    bytes_transferred = event_data.get('bytesTransferred', 0)

    # Threshold: 10MB transfer
    if bytes_transferred > 10 * 1024 * 1024:
        return {
            'rule': 'DATA_EXFILTRATION',
            'severity': 'HIGH',
            'description': f'Large data transfer detected: {bytes_transferred} bytes',
            'details': {
                'bytes': bytes_transferred,
                'source_ip': event_data.get('sourceIp'),
                'resource': event_data.get('resource'),
                'user': event_data.get('user')
            }
        }

    return None

def detect_scanning(event_data):
    """
    Detects port scanning or resource probing activities.
    """
    if event_data.get('eventType') != 'network':
        return None

    if event_data.get('action') in ['scan', 'probe']:
        return {
            'rule': 'NETWORK_SCANNING',
            'severity': 'MEDIUM',
            'description': f'Network scanning detected from {event_data.get("sourceIp")}',
            'details': {
                'scan_type': event_data.get('action'),
                'target': event_data.get('destinationIp'),
                'resource': event_data.get('resource')
            }
        }

    # Detect multiple 404s (directory traversal attempts)
    if event_data.get('statusCode') == 404:
        suspicious_resources = ['/.env', '/wp-admin', '/admin', '/config', '/.git']
        if any(res in event_data.get('resource', '') for res in suspicious_resources):
            return {
                'rule': 'DIRECTORY_TRAVERSAL',
                'severity': 'MEDIUM',
                'description': 'Potential directory traversal or scanning attempt',
                'details': {
                    'resource': event_data.get('resource'),
                    'source_ip': event_data.get('sourceIp')
                }
            }

    return None

def detect_anomalous_time_access(event_data):
    """
    Detects access during unusual hours (e.g., 2 AM - 5 AM UTC).
    """
    timestamp = event_data.get('timestamp')
    dt = datetime.fromtimestamp(timestamp)

    # Anomalous hours: 2 AM - 5 AM UTC
    if 2 <= dt.hour < 5:
        # Only flag for sensitive resources
        sensitive_resources = ['/admin', '/database', '/config', '/system']
        resource = event_data.get('resource', '')

        if any(sens in resource for sens in sensitive_resources):
            return {
                'rule': 'ANOMALOUS_TIME_ACCESS',
                'severity': 'LOW',
                'description': f'Access to sensitive resource during unusual hours',
                'details': {
                    'time': dt.strftime('%Y-%m-%d %H:%M:%S UTC'),
                    'resource': resource,
                    'user': event_data.get('user')
                }
            }

    return None

def detect_failed_authentication(event_data):
    """
    Detects patterns in failed authentication attempts.
    """
    if event_data.get('eventType') != 'authentication':
        return None

    if event_data.get('action') == 'login_failed':
        user = event_data.get('user')

        # Flag attempts on privileged accounts
        if user in ['admin', 'root', 'administrator']:
            return {
                'rule': 'PRIVILEGED_ACCOUNT_FAILED_AUTH',
                'severity': 'MEDIUM',
                'description': f'Failed authentication on privileged account: {user}',
                'details': {
                    'user': user,
                    'source_ip': event_data.get('sourceIp')
                }
            }

    return None

def detect_sql_injection(event_data):
    """
    Detects potential SQL injection attempts in request parameters.
    """
    resource = event_data.get('resource', '').lower()
    user_agent = event_data.get('userAgent', '').lower()

    # SQL injection patterns
    sql_patterns = [
        "' or '1'='1", "' or 1=1", "union select", "drop table",
        "insert into", "delete from", "exec(", "execute(",
        "'; --", "' --", "/*", "*/", "xp_cmdshell"
    ]

    for pattern in sql_patterns:
        if pattern in resource or pattern in user_agent:
            return {
                'rule': 'SQL_INJECTION_ATTEMPT',
                'severity': 'HIGH',
                'description': f'Potential SQL injection detected in request',
                'details': {
                    'resource': event_data.get('resource'),
                    'source_ip': event_data.get('sourceIp'),
                    'user_agent': event_data.get('userAgent'),
                    'pattern_matched': pattern
                }
            }

    return None

def detect_rate_limit_violation(event_data):
    """
    Detects API rate limit violations (too many requests).
    """
    source_ip = event_data.get('sourceIp')

    try:
        # Check requests in last minute
        one_minute_ago = int(time.time()) - 60

        response = events_table.query(
            IndexName='SourceIpIndex',
            KeyConditionExpression='sourceIp = :ip AND #ts >= :timestamp',
            ExpressionAttributeNames={'#ts': 'timestamp'},
            ExpressionAttributeValues={
                ':ip': source_ip,
                ':timestamp': one_minute_ago
            }
        )

        request_count = len(response.get('Items', []))

        # Threshold: 100 requests per minute from single IP
        if request_count >= 100:
            return {
                'rule': 'API_RATE_LIMIT_VIOLATION',
                'severity': 'MEDIUM',
                'description': f'Excessive requests from {source_ip}: {request_count} in 1 minute',
                'details': {
                    'source_ip': source_ip,
                    'request_count': request_count,
                    'time_window': '60 seconds',
                    'threshold': 100
                }
            }

    except Exception as e:
        print(f"Error in rate limit detection: {str(e)}")

    return None

def detect_credential_stuffing(event_data):
    """
    Detects credential stuffing attacks - multiple different user login attempts from same IP.
    """
    if event_data.get('eventType') != 'authentication':
        return None

    if event_data.get('action') != 'login_failed':
        return None

    source_ip = event_data.get('sourceIp')

    try:
        # Check failed logins in last 5 minutes
        five_minutes_ago = int(time.time()) - 300

        response = events_table.query(
            IndexName='SourceIpIndex',
            KeyConditionExpression='sourceIp = :ip AND #ts >= :timestamp',
            ExpressionAttributeNames={'#ts': 'timestamp'},
            ExpressionAttributeValues={
                ':ip': source_ip,
                ':timestamp': five_minutes_ago
            }
        )

        failed_logins = [
            item for item in response.get('Items', [])
            if item.get('eventType') == 'authentication' and
               item.get('action') == 'login_failed'
        ]

        # Count unique usernames attempted
        unique_users = set(item.get('user') for item in failed_logins)

        # Threshold: 10+ different usernames in 5 minutes = credential stuffing
        if len(unique_users) >= 10:
            return {
                'rule': 'CREDENTIAL_STUFFING',
                'severity': 'CRITICAL',
                'description': f'Credential stuffing attack from {source_ip}',
                'details': {
                    'source_ip': source_ip,
                    'unique_usernames_attempted': len(unique_users),
                    'total_attempts': len(failed_logins),
                    'time_window': '5 minutes'
                }
            }

    except Exception as e:
        print(f"Error in credential stuffing detection: {str(e)}")

    return None

def detect_geo_anomaly(event_data):
    """
    Detects suspicious geographic locations (simplified version).
    In production, integrate with GeoIP database and track user baseline locations.
    """
    source_ip = event_data.get('sourceIp')
    user = event_data.get('user')

    # High-risk countries/regions (simplified - use real GeoIP in production)
    # This is a placeholder - in reality you'd use MaxMind or similar
    high_risk_ip_ranges = [
        '185.220.',  # Known Tor exit nodes
        '45.142.',   # High-risk hosting
        '123.45.',   # Example suspicious range
    ]

    # Check if IP is from high-risk region
    for risk_range in high_risk_ip_ranges:
        if source_ip.startswith(risk_range):
            # Check if this user normally accesses from different location
            if user not in ['anonymous', 'guest']:
                return {
                    'rule': 'GEO_LOCATION_ANOMALY',
                    'severity': 'MEDIUM',
                    'description': f'User {user} accessing from unusual geographic location',
                    'details': {
                        'user': user,
                        'source_ip': source_ip,
                        'location_category': 'high_risk_region',
                        'action': event_data.get('action'),
                        'resource': event_data.get('resource')
                    }
                }

    return None

def create_alert(threat, event_data):
    """
    Creates an alert record in DynamoDB and sends notification via SNS.
    """
    try:
        current_time = int(time.time())

        alert = {
            'alertId': str(uuid.uuid4()),
            'timestamp': current_time,
            'severity': threat['severity'],
            'rule': threat['rule'],
            'description': threat['description'],
            'details': threat.get('details', {}),
            'sourceEvent': {
                'eventId': event_data.get('eventId'),
                'eventType': event_data.get('eventType'),
                'sourceIp': event_data.get('sourceIp'),
                'user': event_data.get('user'),
                'resource': event_data.get('resource')
            },
            'status': 'OPEN',
            'createdAt': datetime.utcnow().isoformat()
        }

        # Store alert in DynamoDB
        alerts_table.put_item(Item=alert)

        # Send notifications based on configuration
        severity_config = ALERT_SEVERITIES.get(threat['severity'], {})

        # Send Slack notification if configured
        if severity_config.get('send_slack', False):
            try:
                send_slack_alert(alert)
            except Exception as e:
                print(f"Failed to send Slack notification: {str(e)}")

        # Send SNS/Email notification if configured
        if severity_config.get('send_email', False):
            send_sns_notification(alert)

        print(f"Alert created: {alert['alertId']} - {threat['rule']}")

    except Exception as e:
        print(f"Error creating alert: {str(e)}")

def send_sns_notification(alert):
    """
    Sends alert notification via SNS.
    """
    try:
        message = f"""
SECURITY ALERT - {alert['severity']}

Rule: {alert['rule']}
Description: {alert['description']}

Event Details:
- Source IP: {alert['sourceEvent'].get('sourceIp')}
- User: {alert['sourceEvent'].get('user')}
- Resource: {alert['sourceEvent'].get('resource')}
- Event Type: {alert['sourceEvent'].get('eventType')}

Alert ID: {alert['alertId']}
Timestamp: {alert['createdAt']}

Additional Details:
{json.dumps(alert.get('details', {}), indent=2)}
"""

        sns.publish(
            TopicArn=sns_topic_arn,
            Subject=f"Security Alert: {alert['rule']} ({alert['severity']})",
            Message=message
        )

        print(f"SNS notification sent for alert: {alert['alertId']}")

    except Exception as e:
        print(f"Error sending SNS notification: {str(e)}")

def send_alert_metrics(count):
    """
    Sends alert metrics to CloudWatch.
    """
    try:
        cloudwatch.put_metric_data(
            Namespace='SecurityMonitoring',
            MetricData=[
                {
                    'MetricName': 'AlertsGenerated',
                    'Value': count,
                    'Unit': 'Count',
                    'Timestamp': datetime.utcnow()
                }
            ]
        )
    except Exception as e:
        print(f"Failed to send metrics: {str(e)}")

def deserialize_dynamodb_item(item):
    """
    Deserializes a DynamoDB item from stream format to Python dict.
    """
    result = {}
    for key, value in item.items():
        if 'S' in value:
            result[key] = value['S']
        elif 'N' in value:
            result[key] = int(value['N'])
        elif 'M' in value:
            result[key] = deserialize_dynamodb_item(value['M'])
        elif 'L' in value:
            result[key] = [deserialize_dynamodb_item({'item': v})['item'] for v in value['L']]
        elif 'BOOL' in value:
            result[key] = value['BOOL']
    return result
