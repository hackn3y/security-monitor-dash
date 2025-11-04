"""
Slack Notification Module
Sends security alerts to Slack channels
"""

import json
import os
from urllib import request
from urllib.error import URLError, HTTPError


def send_slack_alert(alert, webhook_url=None):
    """
    Sends a security alert to Slack using incoming webhooks.

    Args:
        alert: Alert dictionary with severity, rule, description, etc.
        webhook_url: Slack webhook URL (if None, uses SLACK_WEBHOOK_URL env var)

    Returns:
        bool: True if successful, False otherwise
    """
    # Get webhook URL from parameter or environment
    webhook = webhook_url or os.environ.get('SLACK_WEBHOOK_URL')

    if not webhook:
        print("Slack webhook URL not configured. Skipping Slack notification.")
        return False

    # Determine color based on severity
    color_map = {
        'CRITICAL': '#FF0000',  # Red
        'HIGH': '#FF6600',      # Orange
        'MEDIUM': '#FFCC00',    # Yellow
        'LOW': '#36A64F'        # Green
    }

    severity = alert.get('severity', 'UNKNOWN')
    color = color_map.get(severity, '#808080')

    # Determine emoji based on severity
    emoji_map = {
        'CRITICAL': ':rotating_light:',
        'HIGH': ':warning:',
        'MEDIUM': ':large_orange_diamond:',
        'LOW': ':information_source:'
    }
    emoji = emoji_map.get(severity, ':bell:')

    # Build Slack message
    source_event = alert.get('sourceEvent', {})
    details = alert.get('details', {})

    # Format details as fields
    fields = [
        {
            "title": "Source IP",
            "value": source_event.get('sourceIp', 'Unknown'),
            "short": True
        },
        {
            "title": "User",
            "value": source_event.get('user', 'Unknown'),
            "short": True
        },
        {
            "title": "Resource",
            "value": source_event.get('resource', 'Unknown'),
            "short": True
        },
        {
            "title": "Event Type",
            "value": source_event.get('eventType', 'Unknown'),
            "short": True
        }
    ]

    # Add additional details
    for key, value in details.items():
        if key not in ['source_ip', 'user', 'resource'] and isinstance(value, (str, int, float)):
            fields.append({
                "title": key.replace('_', ' ').title(),
                "value": str(value),
                "short": True
            })

    slack_message = {
        "username": "Security Monitor",
        "icon_emoji": ":shield:",
        "attachments": [
            {
                "color": color,
                "title": f"{emoji} Security Alert: {alert.get('rule', 'Unknown Rule')}",
                "text": alert.get('description', 'No description provided'),
                "fields": fields,
                "footer": "Security Monitoring Dashboard",
                "footer_icon": "https://platform.slack-edge.com/img/default_application_icon.png",
                "ts": alert.get('timestamp', 0),
                "mrkdwn_in": ["text", "pretext"]
            }
        ]
    }

    # Add alert ID as a field
    slack_message["attachments"][0]["fields"].append({
        "title": "Alert ID",
        "value": alert.get('alertId', 'Unknown'),
        "short": False
    })

    try:
        # Send POST request to Slack webhook
        req = request.Request(
            webhook,
            data=json.dumps(slack_message).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )

        response = request.urlopen(req)

        if response.getcode() == 200:
            print(f"Slack notification sent for alert: {alert.get('alertId')}")
            return True
        else:
            print(f"Slack notification failed with status: {response.getcode()}")
            return False

    except HTTPError as e:
        print(f"HTTP Error sending Slack notification: {e.code} - {e.reason}")
        return False
    except URLError as e:
        print(f"URL Error sending Slack notification: {e.reason}")
        return False
    except Exception as e:
        print(f"Unexpected error sending Slack notification: {str(e)}")
        return False


def format_slack_summary(stats):
    """
    Formats a security summary for Slack (useful for periodic reports).

    Args:
        stats: Dictionary with security statistics

    Returns:
        dict: Formatted Slack message
    """
    overview = stats.get('overview', {})

    message = {
        "username": "Security Monitor",
        "icon_emoji": ":bar_chart:",
        "text": ":chart_with_upwards_trend: *Security Monitoring Daily Summary*",
        "attachments": [
            {
                "color": "#36A64F",
                "fields": [
                    {
                        "title": "Total Events (24h)",
                        "value": str(overview.get('total_events', 0)),
                        "short": True
                    },
                    {
                        "title": "Total Alerts",
                        "value": str(overview.get('total_alerts', 0)),
                        "short": True
                    },
                    {
                        "title": "Open Alerts",
                        "value": str(overview.get('open_alerts', 0)),
                        "short": True
                    },
                    {
                        "title": "Critical Alerts",
                        "value": str(overview.get('critical_alerts', 0)),
                        "short": True
                    }
                ],
                "footer": "Security Monitoring Dashboard",
                "ts": int(os.time.time()) if hasattr(os, 'time') else 0
            }
        ]
    }

    return message
