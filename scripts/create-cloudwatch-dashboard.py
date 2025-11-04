#!/usr/bin/env python3
"""
Creates a CloudWatch Dashboard for Security Monitoring
"""

import boto3
import json
import argparse

def create_dashboard(stack_name='security-monitoring', region='us-east-1'):
    """Creates a CloudWatch dashboard for the security monitoring system."""

    cloudwatch = boto3.client('cloudwatch', region_name=region)

    dashboard_body = {
        "widgets": [
            {
                "type": "metric",
                "properties": {
                    "metrics": [
                        ["SecurityMonitoring", "EventsIngested", {"stat": "Sum"}],
                        [".", "EventsFailed", {"stat": "Sum"}]
                    ],
                    "period": 300,
                    "stat": "Average",
                    "region": region,
                    "title": "Event Ingestion",
                    "yAxis": {
                        "left": {
                            "label": "Count"
                        }
                    }
                },
                "width": 12,
                "height": 6,
                "x": 0,
                "y": 0
            },
            {
                "type": "metric",
                "properties": {
                    "metrics": [
                        ["SecurityMonitoring", "AlertsGenerated", {"stat": "Sum"}],
                        [".", "CriticalAlerts", {"stat": "Sum", "color": "#d13212"}]
                    ],
                    "period": 300,
                    "stat": "Sum",
                    "region": region,
                    "title": "Alerts Generated",
                    "yAxis": {
                        "left": {
                            "label": "Count"
                        }
                    }
                },
                "width": 12,
                "height": 6,
                "x": 12,
                "y": 0
            },
            {
                "type": "log",
                "properties": {
                    "query": f"SOURCE '/aws/lambda/ThreatDetection'\n| fields @timestamp, @message\n| filter @message like /Alert created/\n| sort @timestamp desc\n| limit 20",
                    "region": region,
                    "stacked": False,
                    "title": "Recent Alerts",
                    "view": "table"
                },
                "width": 24,
                "height": 6,
                "x": 0,
                "y": 6
            },
            {
                "type": "metric",
                "properties": {
                    "metrics": [
                        ["AWS/Lambda", "Invocations", "FunctionName", "SecurityLogIngestion"],
                        ["...", "ThreatDetection"],
                        ["...", "DashboardAPI"]
                    ],
                    "period": 300,
                    "stat": "Sum",
                    "region": region,
                    "title": "Lambda Invocations",
                    "yAxis": {
                        "left": {
                            "label": "Count"
                        }
                    }
                },
                "width": 12,
                "height": 6,
                "x": 0,
                "y": 12
            },
            {
                "type": "metric",
                "properties": {
                    "metrics": [
                        ["AWS/Lambda", "Errors", "FunctionName", "SecurityLogIngestion"],
                        ["...", "ThreatDetection"],
                        ["...", "DashboardAPI"]
                    ],
                    "period": 300,
                    "stat": "Sum",
                    "region": region,
                    "title": "Lambda Errors",
                    "yAxis": {
                        "left": {
                            "label": "Count"
                        }
                    }
                },
                "width": 12,
                "height": 6,
                "x": 12,
                "y": 12
            },
            {
                "type": "metric",
                "properties": {
                    "metrics": [
                        ["AWS/DynamoDB", "ConsumedReadCapacityUnits", "TableName", "SecurityEvents"],
                        [".", "ConsumedWriteCapacityUnits", ".", "."]
                    ],
                    "period": 300,
                    "stat": "Sum",
                    "region": region,
                    "title": "DynamoDB Capacity - Events Table",
                    "yAxis": {
                        "left": {
                            "label": "Units"
                        }
                    }
                },
                "width": 12,
                "height": 6,
                "x": 0,
                "y": 18
            },
            {
                "type": "metric",
                "properties": {
                    "metrics": [
                        ["AWS/DynamoDB", "ConsumedReadCapacityUnits", "TableName", "SecurityAlerts"],
                        [".", "ConsumedWriteCapacityUnits", ".", "."]
                    ],
                    "period": 300,
                    "stat": "Sum",
                    "region": region,
                    "title": "DynamoDB Capacity - Alerts Table",
                    "yAxis": {
                        "left": {
                            "label": "Units"
                        }
                    }
                },
                "width": 12,
                "height": 6,
                "x": 12,
                "y": 18
            }
        ]
    }

    try:
        response = cloudwatch.put_dashboard(
            DashboardName=f'{stack_name}-SecurityMonitoring',
            DashboardBody=json.dumps(dashboard_body)
        )

        print(f"✅ CloudWatch Dashboard created successfully!")
        print(f"Dashboard Name: {stack_name}-SecurityMonitoring")
        print(f"\nView it here: https://console.aws.amazon.com/cloudwatch/home?region={region}#dashboards:name={stack_name}-SecurityMonitoring")

        return response

    except Exception as e:
        print(f"❌ Error creating dashboard: {str(e)}")
        return None


def main():
    parser = argparse.ArgumentParser(
        description='Create CloudWatch Dashboard for Security Monitoring'
    )
    parser.add_argument(
        '--stack-name',
        default='security-monitoring',
        help='CloudFormation stack name (default: security-monitoring)'
    )
    parser.add_argument(
        '--region',
        default='us-east-1',
        help='AWS region (default: us-east-1)'
    )

    args = parser.parse_args()

    print(f"Creating CloudWatch Dashboard...")
    print(f"Stack Name: {args.stack_name}")
    print(f"Region: {args.region}\n")

    create_dashboard(args.stack_name, args.region)


if __name__ == '__main__':
    main()
