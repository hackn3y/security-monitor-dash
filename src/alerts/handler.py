import json
import boto3
import os
from datetime import datetime

sns = boto3.client('sns')
dynamodb = boto3.resource('dynamodb')

alerts_table = dynamodb.Table(os.environ['ALERTS_TABLE'])
sns_topic_arn = os.environ['SNS_TOPIC_ARN']

def lambda_handler(event, context):
    """
    Manages alert notifications and alert status updates.
    Can be invoked directly or via API Gateway.
    """

    try:
        # Check if this is an API Gateway request
        if event.get('httpMethod'):
            return handle_api_request(event, context)
        else:
            return handle_direct_invocation(event, context)

    except Exception as e:
        print(f"Error in alert handler: {str(e)}")
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

def handle_api_request(event, context):
    """
    Handles API Gateway requests for alert management.
    """
    method = event.get('httpMethod')
    path = event.get('path')

    if method == 'POST' and '/alert' in path:
        # Acknowledge or resolve an alert
        body = json.loads(event.get('body', '{}'))
        alert_id = body.get('alertId')
        action = body.get('action')  # 'acknowledge' or 'resolve'

        if not alert_id or not action:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Missing alertId or action'
                })
            }

        update_alert_status(alert_id, action)

        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'message': f'Alert {action}d successfully',
                'alertId': alert_id
            })
        }

    return {
        'statusCode': 404,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({
            'error': 'Not found'
        })
    }

def handle_direct_invocation(event, context):
    """
    Handles direct Lambda invocations (e.g., from CloudWatch Events).
    """
    alert_data = event.get('alert')

    if alert_data:
        # Send notification for a specific alert
        send_notification(alert_data)

    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': 'Alert processed successfully'
        })
    }

def update_alert_status(alert_id, action):
    """
    Updates the status of an alert in DynamoDB.
    """
    try:
        status_map = {
            'acknowledge': 'ACKNOWLEDGED',
            'resolve': 'RESOLVED',
            'reopen': 'OPEN'
        }

        new_status = status_map.get(action, 'OPEN')

        # Note: This is a simplified update. In production, you'd need both
        # the hash key (alertId) and range key (timestamp) to update.
        # For this example, we're showing the pattern.

        response = alerts_table.update_item(
            Key={'alertId': alert_id},
            UpdateExpression='SET #status = :status, updatedAt = :updated',
            ExpressionAttributeNames={
                '#status': 'status'
            },
            ExpressionAttributeValues={
                ':status': new_status,
                ':updated': datetime.utcnow().isoformat()
            },
            ReturnValues='UPDATED_NEW'
        )

        print(f"Alert {alert_id} status updated to {new_status}")

        # Send notification about status change
        if new_status == 'RESOLVED':
            send_resolution_notification(alert_id)

    except Exception as e:
        print(f"Error updating alert status: {str(e)}")
        raise

def send_notification(alert_data):
    """
    Sends an alert notification via SNS.
    """
    try:
        message = format_alert_message(alert_data)

        sns.publish(
            TopicArn=sns_topic_arn,
            Subject=f"Security Alert: {alert_data.get('rule', 'Unknown')}",
            Message=message,
            MessageAttributes={
                'severity': {
                    'DataType': 'String',
                    'StringValue': alert_data.get('severity', 'MEDIUM')
                }
            }
        )

        print(f"Notification sent for alert: {alert_data.get('alertId')}")

    except Exception as e:
        print(f"Error sending notification: {str(e)}")

def send_resolution_notification(alert_id):
    """
    Sends a notification when an alert is resolved.
    """
    try:
        message = f"""
Alert Resolved

Alert ID: {alert_id}
Status: RESOLVED
Resolved At: {datetime.utcnow().isoformat()}

This alert has been marked as resolved and no further action is required.
"""

        sns.publish(
            TopicArn=sns_topic_arn,
            Subject=f"Alert Resolved: {alert_id}",
            Message=message
        )

        print(f"Resolution notification sent for alert: {alert_id}")

    except Exception as e:
        print(f"Error sending resolution notification: {str(e)}")

def format_alert_message(alert_data):
    """
    Formats an alert into a human-readable message.
    """
    message = f"""
SECURITY ALERT - {alert_data.get('severity', 'UNKNOWN')}

Rule: {alert_data.get('rule', 'Unknown')}
Description: {alert_data.get('description', 'No description available')}

Alert Details:
{json.dumps(alert_data.get('details', {}), indent=2)}

Event Information:
{json.dumps(alert_data.get('sourceEvent', {}), indent=2)}

Alert ID: {alert_data.get('alertId', 'Unknown')}
Timestamp: {alert_data.get('createdAt', datetime.utcnow().isoformat())}

---
This is an automated alert from your Security Monitoring Dashboard.
"""
    return message
