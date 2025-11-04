import json
import boto3
import os
import uuid
import time
from datetime import datetime
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
cloudwatch = boto3.client('cloudwatch')
table = dynamodb.Table(os.environ['EVENTS_TABLE'])

def lambda_handler(event, context):
    """
    Ingests security events from various sources and stores them in DynamoDB.
    Supports both API Gateway POST requests and scheduled simulated events.
    """

    try:
        # Check if this is a scheduled event (simulation) or API call
        if event.get('source') == 'aws.events':
            # Generate simulated security events for testing
            events_to_ingest = generate_simulated_events()
        else:
            # Parse events from API Gateway request
            body = json.loads(event.get('body', '{}'))
            events_to_ingest = body.get('events', [body]) if isinstance(body, dict) else body

        ingested_count = 0
        failed_count = 0

        for event_data in events_to_ingest:
            try:
                # Normalize and enrich the event
                normalized_event = normalize_event(event_data)

                # Store in DynamoDB
                table.put_item(Item=normalized_event)
                ingested_count += 1

            except Exception as e:
                print(f"Failed to ingest event: {str(e)}")
                failed_count += 1

        # Send metrics to CloudWatch
        send_metrics(ingested_count, failed_count)

        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'message': 'Events ingested successfully',
                'ingested': ingested_count,
                'failed': failed_count
            })
        }

    except Exception as e:
        print(f"Error in lambda_handler: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': str(e)
            })
        }

def normalize_event(event_data):
    """
    Normalizes event data into a standard format for storage.
    """
    current_time = int(time.time())

    normalized = {
        'eventId': str(uuid.uuid4()),
        'timestamp': current_time,
        'ttl': current_time + (30 * 24 * 60 * 60),  # 30 days TTL
        'eventType': event_data.get('eventType', 'unknown'),
        'sourceIp': event_data.get('sourceIp', 'unknown'),
        'destinationIp': event_data.get('destinationIp', 'unknown'),
        'user': event_data.get('user', 'anonymous'),
        'action': event_data.get('action', 'unknown'),
        'resource': event_data.get('resource', 'unknown'),
        'userAgent': event_data.get('userAgent', 'unknown'),
        'requestMethod': event_data.get('requestMethod', 'unknown'),
        'statusCode': event_data.get('statusCode', 0),
        'responseTime': Decimal(str(event_data.get('responseTime', 0))),
        'bytesTransferred': event_data.get('bytesTransferred', 0),
        'geo': event_data.get('geo', {}),
        'metadata': event_data.get('metadata', {}),
        'rawEvent': json.dumps(event_data)
    }

    return normalized

def generate_simulated_events():
    """
    Generates simulated security events for testing purposes.
    Includes both normal and suspicious activities.
    """
    import random

    # Common IPs (mix of legitimate and suspicious)
    source_ips = [
        '192.168.1.100', '192.168.1.101', '192.168.1.102',  # Internal
        '10.0.0.50', '10.0.0.51',  # Internal
        '203.0.113.45', '198.51.100.23',  # Normal external
        '185.220.101.5', '45.142.120.10',  # Suspicious (Tor-like)
        '123.45.67.89', '98.76.54.32'  # Generic external
    ]

    users = ['admin', 'user1', 'user2', 'service_account', 'api_user', 'guest']

    event_types = [
        {'type': 'authentication', 'actions': ['login', 'logout', 'login_failed', 'password_reset']},
        {'type': 'api_request', 'actions': ['GET', 'POST', 'PUT', 'DELETE']},
        {'type': 'file_access', 'actions': ['read', 'write', 'delete', 'download']},
        {'type': 'admin_action', 'actions': ['user_create', 'user_delete', 'permission_change']},
        {'type': 'network', 'actions': ['connection', 'scan', 'probe']}
    ]

    resources = [
        '/api/users', '/api/data', '/admin/settings',
        '/files/sensitive.pdf', '/database/backup',
        '/api/login', '/api/config', '/system/logs'
    ]

    events = []
    num_events = random.randint(3, 8)

    for _ in range(num_events):
        event_category = random.choice(event_types)
        source_ip = random.choice(source_ips)

        # Create suspicious patterns occasionally
        is_suspicious = random.random() < 0.15  # 15% chance

        if is_suspicious:
            # Generate suspicious activity
            if random.random() < 0.5:
                # Brute force attempt
                event = {
                    'eventType': 'authentication',
                    'action': 'login_failed',
                    'sourceIp': source_ip,
                    'destinationIp': '10.0.0.100',
                    'user': random.choice(['admin', 'root', 'administrator']),
                    'resource': '/api/login',
                    'userAgent': 'curl/7.68.0',
                    'requestMethod': 'POST',
                    'statusCode': 401,
                    'responseTime': random.randint(100, 300),
                    'bytesTransferred': random.randint(200, 500)
                }
            else:
                # Suspicious scan or probe
                event = {
                    'eventType': 'network',
                    'action': 'probe',
                    'sourceIp': source_ip,
                    'destinationIp': '10.0.0.' + str(random.randint(1, 254)),
                    'user': 'anonymous',
                    'resource': random.choice(['/admin', '/.env', '/config.php', '/wp-admin']),
                    'userAgent': 'Mozilla/5.0 (compatible; scanner/1.0)',
                    'requestMethod': 'GET',
                    'statusCode': 404,
                    'responseTime': random.randint(10, 50),
                    'bytesTransferred': random.randint(100, 300)
                }
        else:
            # Normal activity
            event = {
                'eventType': event_category['type'],
                'action': random.choice(event_category['actions']),
                'sourceIp': source_ip,
                'destinationIp': '10.0.0.100',
                'user': random.choice(users),
                'resource': random.choice(resources),
                'userAgent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'requestMethod': random.choice(['GET', 'POST', 'PUT', 'DELETE']),
                'statusCode': random.choice([200, 201, 304, 400, 403, 404, 500]),
                'responseTime': random.randint(50, 2000),
                'bytesTransferred': random.randint(500, 50000)
            }

        event['metadata'] = {
            'simulated': True,
            'generatedAt': datetime.utcnow().isoformat()
        }

        events.append(event)

    return events

def send_metrics(ingested_count, failed_count):
    """
    Sends custom metrics to CloudWatch for monitoring.
    """
    try:
        cloudwatch.put_metric_data(
            Namespace='SecurityMonitoring',
            MetricData=[
                {
                    'MetricName': 'EventsIngested',
                    'Value': ingested_count,
                    'Unit': 'Count',
                    'Timestamp': datetime.utcnow()
                },
                {
                    'MetricName': 'EventsFailed',
                    'Value': failed_count,
                    'Unit': 'Count',
                    'Timestamp': datetime.utcnow()
                }
            ]
        )
    except Exception as e:
        print(f"Failed to send metrics: {str(e)}")
