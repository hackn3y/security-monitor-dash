#!/usr/bin/env python3
"""
Traffic Simulator for Security Monitoring Dashboard

This script generates realistic and suspicious traffic patterns
to test the security monitoring system.
"""

import requests
import random
import time
import json
from datetime import datetime
import argparse

class TrafficSimulator:
    """Simulates various types of network traffic for security testing."""

    def __init__(self, api_endpoint):
        self.api_endpoint = api_endpoint.rstrip('/') + '/ingest'
        self.session = requests.Session()

    def generate_normal_traffic(self, count=10):
        """Generates normal, legitimate traffic patterns."""
        print(f"\n[*] Generating {count} normal events...")

        source_ips = ['192.168.1.100', '192.168.1.101', '10.0.0.50']
        users = ['user1', 'user2', 'api_user']
        resources = ['/api/data', '/api/users', '/files/report.pdf']

        events = []
        for _ in range(count):
            event = {
                'eventType': random.choice(['api_request', 'file_access', 'authentication']),
                'action': random.choice(['GET', 'POST', 'login', 'read']),
                'sourceIp': random.choice(source_ips),
                'destinationIp': '10.0.0.100',
                'user': random.choice(users),
                'resource': random.choice(resources),
                'userAgent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'requestMethod': random.choice(['GET', 'POST']),
                'statusCode': 200,
                'responseTime': random.randint(50, 500),
                'bytesTransferred': random.randint(1000, 50000)
            }
            events.append(event)

        self._send_events(events)
        print(f"[+] Sent {len(events)} normal events")

    def simulate_brute_force_attack(self):
        """Simulates a brute force authentication attack."""
        print("\n[*] Simulating brute force attack...")

        attacker_ip = '45.142.120.10'
        target_users = ['admin', 'root', 'administrator']

        events = []
        for i in range(8):  # 8 failed attempts to trigger alert
            event = {
                'eventType': 'authentication',
                'action': 'login_failed',
                'sourceIp': attacker_ip,
                'destinationIp': '10.0.0.100',
                'user': random.choice(target_users),
                'resource': '/api/login',
                'userAgent': 'curl/7.68.0',
                'requestMethod': 'POST',
                'statusCode': 401,
                'responseTime': random.randint(100, 300),
                'bytesTransferred': 250
            }
            events.append(event)
            time.sleep(0.5)  # Slight delay between attempts

        self._send_events(events)
        print(f"[+] Sent {len(events)} brute force events")
        print("[!] This should trigger a BRUTE_FORCE_DETECTION alert")

    def simulate_suspicious_ip_access(self):
        """Simulates access from suspicious IP addresses."""
        print("\n[*] Simulating access from suspicious IPs...")

        suspicious_ips = ['185.220.101.5', '45.142.120.15']

        events = []
        for ip in suspicious_ips:
            event = {
                'eventType': 'api_request',
                'action': 'GET',
                'sourceIp': ip,
                'destinationIp': '10.0.0.100',
                'user': 'anonymous',
                'resource': random.choice(['/api/data', '/admin/settings']),
                'userAgent': 'Mozilla/5.0 (compatible; scanner/1.0)',
                'requestMethod': 'GET',
                'statusCode': 200,
                'responseTime': random.randint(50, 200),
                'bytesTransferred': random.randint(1000, 5000)
            }
            events.append(event)

        self._send_events(events)
        print(f"[+] Sent {len(events)} suspicious IP events")
        print("[!] This should trigger SUSPICIOUS_IP_DETECTION alerts")

    def simulate_port_scanning(self):
        """Simulates port scanning and directory traversal attempts."""
        print("\n[*] Simulating port scanning / directory traversal...")

        scanner_ip = '123.45.67.89'
        suspicious_paths = [
            '/.env', '/wp-admin', '/admin', '/config.php',
            '/.git/config', '/phpmyadmin', '/backup.sql'
        ]

        events = []
        for path in suspicious_paths:
            event = {
                'eventType': 'network',
                'action': 'probe',
                'sourceIp': scanner_ip,
                'destinationIp': '10.0.0.100',
                'user': 'anonymous',
                'resource': path,
                'userAgent': 'Mozilla/5.0 (compatible; scanner/1.0)',
                'requestMethod': 'GET',
                'statusCode': 404,
                'responseTime': random.randint(10, 50),
                'bytesTransferred': random.randint(100, 300)
            }
            events.append(event)

        self._send_events(events)
        print(f"[+] Sent {len(events)} scanning events")
        print("[!] This should trigger NETWORK_SCANNING and DIRECTORY_TRAVERSAL alerts")

    def simulate_privilege_escalation(self):
        """Simulates privilege escalation attempts."""
        print("\n[*] Simulating privilege escalation attempt...")

        events = [{
            'eventType': 'admin_action',
            'action': 'user_create',
            'sourceIp': '192.168.1.150',
            'destinationIp': '10.0.0.100',
            'user': 'user2',  # Non-admin user
            'resource': '/admin/users',
            'userAgent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
            'requestMethod': 'POST',
            'statusCode': 403,
            'responseTime': 150,
            'bytesTransferred': 500
        }]

        self._send_events(events)
        print(f"[+] Sent {len(events)} privilege escalation event")
        print("[!] This should trigger a PRIVILEGE_ESCALATION alert")

    def simulate_data_exfiltration(self):
        """Simulates large data transfer (potential exfiltration)."""
        print("\n[*] Simulating data exfiltration...")

        events = [{
            'eventType': 'file_access',
            'action': 'download',
            'sourceIp': '192.168.1.100',
            'destinationIp': '10.0.0.100',
            'user': 'user1',
            'resource': '/database/backup.sql',
            'userAgent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
            'requestMethod': 'GET',
            'statusCode': 200,
            'responseTime': 5000,
            'bytesTransferred': 15 * 1024 * 1024  # 15MB
        }]

        self._send_events(events)
        print(f"[+] Sent {len(events)} large transfer event")
        print("[!] This should trigger a DATA_EXFILTRATION alert")

    def simulate_anomalous_time_access(self):
        """Simulates access during unusual hours."""
        print("\n[*] Simulating access during unusual hours...")
        print("[Note: This requires the event timestamp to be in the 2-5 AM UTC range]")

        # Note: The Lambda function checks the timestamp, so we can just send the event
        # and let the detection logic handle it based on current time
        events = [{
            'eventType': 'file_access',
            'action': 'read',
            'sourceIp': '192.168.1.100',
            'destinationIp': '10.0.0.100',
            'user': 'user1',
            'resource': '/admin/config',
            'userAgent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
            'requestMethod': 'GET',
            'statusCode': 200,
            'responseTime': 200,
            'bytesTransferred': 5000
        }]

        self._send_events(events)
        print(f"[+] Sent {len(events)} off-hours access event")
        print("[!] May trigger ANOMALOUS_TIME_ACCESS alert if sent during 2-5 AM UTC")

    def run_full_simulation(self):
        """Runs a comprehensive simulation with all attack patterns."""
        print("="*60)
        print("Starting Full Security Monitoring Simulation")
        print("="*60)

        # Generate normal baseline traffic
        self.generate_normal_traffic(20)
        time.sleep(2)

        # Simulate various attacks
        self.simulate_brute_force_attack()
        time.sleep(2)

        self.simulate_suspicious_ip_access()
        time.sleep(2)

        self.simulate_port_scanning()
        time.sleep(2)

        self.simulate_privilege_escalation()
        time.sleep(2)

        self.simulate_data_exfiltration()
        time.sleep(2)

        self.simulate_anomalous_time_access()
        time.sleep(2)

        # More normal traffic
        self.generate_normal_traffic(15)

        print("\n" + "="*60)
        print("Simulation Complete!")
        print("="*60)
        print("\n[*] Check your dashboard for alerts and events")
        print("[*] Check your SNS email for HIGH and CRITICAL alert notifications")

    def _send_events(self, events):
        """Sends events to the ingestion API."""
        try:
            response = self.session.post(
                self.api_endpoint,
                json={'events': events},
                headers={'Content-Type': 'application/json'},
                timeout=10
            )

            if response.status_code == 200:
                return response.json()
            else:
                print(f"[!] Error: {response.status_code} - {response.text}")
                return None

        except Exception as e:
            print(f"[!] Failed to send events: {str(e)}")
            return None


def main():
    parser = argparse.ArgumentParser(
        description='Security Monitoring Traffic Simulator'
    )
    parser.add_argument(
        '--endpoint',
        required=True,
        help='API Gateway endpoint URL (e.g., https://xxx.execute-api.region.amazonaws.com/Prod/)'
    )
    parser.add_argument(
        '--scenario',
        choices=[
            'all', 'normal', 'brute-force', 'suspicious-ip',
            'scanning', 'privilege-escalation', 'exfiltration', 'anomalous-time'
        ],
        default='all',
        help='Simulation scenario to run'
    )
    parser.add_argument(
        '--count',
        type=int,
        default=20,
        help='Number of normal events to generate (for normal scenario)'
    )

    args = parser.parse_args()

    simulator = TrafficSimulator(args.endpoint)

    print(f"\n[*] Target Endpoint: {args.endpoint}")
    print(f"[*] Scenario: {args.scenario}\n")

    if args.scenario == 'all':
        simulator.run_full_simulation()
    elif args.scenario == 'normal':
        simulator.generate_normal_traffic(args.count)
    elif args.scenario == 'brute-force':
        simulator.simulate_brute_force_attack()
    elif args.scenario == 'suspicious-ip':
        simulator.simulate_suspicious_ip_access()
    elif args.scenario == 'scanning':
        simulator.simulate_port_scanning()
    elif args.scenario == 'privilege-escalation':
        simulator.simulate_privilege_escalation()
    elif args.scenario == 'exfiltration':
        simulator.simulate_data_exfiltration()
    elif args.scenario == 'anomalous-time':
        simulator.simulate_anomalous_time_access()


if __name__ == '__main__':
    main()
