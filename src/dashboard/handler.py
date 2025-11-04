import json
import boto3
import os
from datetime import datetime, timedelta
from decimal import Decimal
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource('dynamodb')
events_table = dynamodb.Table(os.environ['EVENTS_TABLE'])
alerts_table = dynamodb.Table(os.environ['ALERTS_TABLE'])

class DecimalEncoder(json.JSONEncoder):
    """Helper class to convert Decimal to float for JSON serialization."""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)

def lambda_handler(event, context):
    """
    API endpoint for the security dashboard.
    Provides data about events, alerts, and statistics.
    """

    try:
        path = event.get('path', '')
        method = event.get('httpMethod', 'GET')

        if method != 'GET':
            return error_response('Method not allowed', 405)

        # Route to appropriate handler
        if '/events' in path:
            return get_events(event)
        elif '/alerts' in path:
            return get_alerts(event)
        elif '/stats' in path:
            return get_statistics(event)
        else:
            return error_response('Not found', 404)

    except Exception as e:
        print(f"Error in dashboard handler: {str(e)}")
        return error_response(str(e), 500)

def get_events(event):
    """
    Retrieves recent security events with optional filtering.
    """
    try:
        query_params = event.get('queryStringParameters', {}) or {}

        limit = int(query_params.get('limit', 50))
        event_type = query_params.get('eventType')
        source_ip = query_params.get('sourceIp')

        if source_ip:
            # Query by source IP using GSI
            response = events_table.query(
                IndexName='SourceIpIndex',
                KeyConditionExpression=Key('sourceIp').eq(source_ip),
                Limit=limit,
                ScanIndexForward=False  # Most recent first
            )
        else:
            # Scan for all events (expensive, but works for demo)
            scan_params = {
                'Limit': limit
            }

            if event_type:
                scan_params['FilterExpression'] = Key('eventType').eq(event_type)

            response = events_table.scan(**scan_params)

        items = response.get('Items', [])

        # Sort by timestamp descending
        items.sort(key=lambda x: x.get('timestamp', 0), reverse=True)

        return success_response({
            'events': items[:limit],
            'count': len(items)
        })

    except Exception as e:
        print(f"Error retrieving events: {str(e)}")
        return error_response(str(e), 500)

def get_alerts(event):
    """
    Retrieves security alerts with optional filtering.
    """
    try:
        query_params = event.get('queryStringParameters', {}) or {}

        limit = int(query_params.get('limit', 50))
        severity = query_params.get('severity')
        status = query_params.get('status', 'OPEN')

        if severity:
            # Query by severity using GSI
            response = alerts_table.query(
                IndexName='SeverityIndex',
                KeyConditionExpression=Key('severity').eq(severity),
                Limit=limit,
                ScanIndexForward=False  # Most recent first
            )
        else:
            # Scan for all alerts
            scan_params = {
                'Limit': limit
            }

            if status:
                scan_params['FilterExpression'] = Key('status').eq(status)

            response = alerts_table.scan(**scan_params)

        items = response.get('Items', [])

        # Sort by timestamp descending
        items.sort(key=lambda x: x.get('timestamp', 0), reverse=True)

        return success_response({
            'alerts': items[:limit],
            'count': len(items)
        })

    except Exception as e:
        print(f"Error retrieving alerts: {str(e)}")
        return error_response(str(e), 500)

def get_statistics(event):
    """
    Retrieves aggregated statistics for the dashboard.
    """
    try:
        # Time ranges
        now = int(datetime.utcnow().timestamp())
        one_hour_ago = now - 3600
        one_day_ago = now - 86400

        # Get recent events
        events_response = events_table.scan(
            Limit=1000
        )
        all_events = events_response.get('Items', [])

        # Get recent alerts
        alerts_response = alerts_table.scan(
            Limit=1000
        )
        all_alerts = alerts_response.get('Items', [])

        # Calculate statistics
        stats = {
            'overview': {
                'total_events': len(all_events),
                'total_alerts': len(all_alerts),
                'open_alerts': len([a for a in all_alerts if a.get('status') == 'OPEN']),
                'critical_alerts': len([a for a in all_alerts if a.get('severity') == 'CRITICAL'])
            },
            'events_by_hour': count_by_time(all_events, one_hour_ago),
            'events_by_day': count_by_time(all_events, one_day_ago),
            'events_by_type': count_by_field(all_events, 'eventType'),
            'alerts_by_severity': count_by_field(all_alerts, 'severity'),
            'alerts_by_rule': count_by_field(all_alerts, 'rule'),
            'top_source_ips': get_top_items(all_events, 'sourceIp', 10),
            'top_users': get_top_items(all_events, 'user', 10),
            'recent_critical_alerts': [
                {
                    'alertId': a.get('alertId'),
                    'rule': a.get('rule'),
                    'description': a.get('description'),
                    'timestamp': a.get('timestamp'),
                    'severity': a.get('severity')
                }
                for a in sorted(
                    [a for a in all_alerts if a.get('severity') == 'CRITICAL'],
                    key=lambda x: x.get('timestamp', 0),
                    reverse=True
                )[:5]
            ]
        }

        return success_response(stats)

    except Exception as e:
        print(f"Error calculating statistics: {str(e)}")
        return error_response(str(e), 500)

def count_by_time(items, since_timestamp):
    """
    Counts items that occurred since a given timestamp.
    """
    return len([item for item in items if item.get('timestamp', 0) >= since_timestamp])

def count_by_field(items, field_name):
    """
    Counts items grouped by a specific field.
    """
    counts = {}
    for item in items:
        value = item.get(field_name, 'unknown')
        counts[value] = counts.get(value, 0) + 1
    return counts

def get_top_items(items, field_name, limit=10):
    """
    Gets the top N items by count for a specific field.
    """
    counts = count_by_field(items, field_name)
    sorted_items = sorted(counts.items(), key=lambda x: x[1], reverse=True)
    return [{'name': name, 'count': count} for name, count in sorted_items[:limit]]

def success_response(data):
    """
    Returns a successful API response.
    """
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Methods': 'GET, OPTIONS'
        },
        'body': json.dumps(data, cls=DecimalEncoder)
    }

def error_response(message, status_code=500):
    """
    Returns an error API response.
    """
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({
            'error': message
        })
    }
