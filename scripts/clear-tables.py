#!/usr/bin/env python3
"""
Script to clear all items from DynamoDB tables for a fresh demo.
"""
import boto3
from decimal import Decimal

def clear_table(table_name, key_schema):
    """Delete all items from a DynamoDB table."""
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(table_name)

    print(f"[*] Clearing table: {table_name}")

    # Scan table and get all items (no projection, just get keys)
    response = table.scan()

    items = response.get('Items', [])
    deleted_count = 0

    # Delete items in batches
    with table.batch_writer() as batch:
        for item in items:
            # Build key from key schema
            key = {key_attr['AttributeName']: item[key_attr['AttributeName']]
                   for key_attr in key_schema}
            batch.delete_item(Key=key)
            deleted_count += 1

    # Handle pagination if there are more items
    while 'LastEvaluatedKey' in response:
        response = table.scan(
            ExclusiveStartKey=response['LastEvaluatedKey']
        )
        items = response.get('Items', [])

        with table.batch_writer() as batch:
            for item in items:
                key = {key_attr['AttributeName']: item[key_attr['AttributeName']]
                       for key_attr in key_schema}
                batch.delete_item(Key=key)
                deleted_count += 1

    print(f"[+] Deleted {deleted_count} items from {table_name}")
    return deleted_count

def main():
    print("\n" + "="*60)
    print("  DynamoDB Table Cleanup Script")
    print("="*60 + "\n")

    # Clear SecurityEvents table
    events_key_schema = [
        {'AttributeName': 'eventId'},
        {'AttributeName': 'timestamp'}
    ]
    events_deleted = clear_table('SecurityEvents', events_key_schema)

    # Clear SecurityAlerts table
    alerts_key_schema = [
        {'AttributeName': 'alertId'},
        {'AttributeName': 'timestamp'}
    ]
    alerts_deleted = clear_table('SecurityAlerts', alerts_key_schema)

    print("\n" + "="*60)
    print(f"  Total items deleted: {events_deleted + alerts_deleted}")
    print("  Dashboard is now clean and ready for demo!")
    print("="*60 + "\n")

if __name__ == '__main__':
    main()
