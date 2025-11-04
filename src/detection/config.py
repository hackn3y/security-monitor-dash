"""
Security Monitoring Configuration
Adjust these thresholds to fine-tune detection sensitivity
"""

# Brute Force Detection
BRUTE_FORCE_THRESHOLD = 5  # Failed attempts
BRUTE_FORCE_TIME_WINDOW = 300  # seconds (5 minutes)

# Data Exfiltration Detection
DATA_EXFILTRATION_THRESHOLD = 10 * 1024 * 1024  # 10MB in bytes

# Rate Limiting
API_RATE_LIMIT_THRESHOLD = 100  # requests per minute
API_RATE_LIMIT_TIME_WINDOW = 60  # seconds

# Credential Stuffing
CREDENTIAL_STUFFING_THRESHOLD = 10  # unique usernames
CREDENTIAL_STUFFING_TIME_WINDOW = 300  # seconds (5 minutes)

# Anomalous Time Access
ANOMALOUS_HOURS_START = 2  # 2 AM UTC
ANOMALOUS_HOURS_END = 5  # 5 AM UTC

# Sensitive Resources (for anomalous time detection)
SENSITIVE_RESOURCES = ['/admin', '/database', '/config', '/system', '/api/admin']

# Privileged Accounts (for failed auth monitoring)
PRIVILEGED_ACCOUNTS = ['admin', 'root', 'administrator', 'superuser', 'sysadmin']

# SQL Injection Patterns
SQL_INJECTION_PATTERNS = [
    "' or '1'='1", "' or 1=1", "union select", "drop table",
    "insert into", "delete from", "exec(", "execute(",
    "'; --", "' --", "/*", "*/", "xp_cmdshell", "0x", "char(",
    "concat(", "@@version", "information_schema"
]

# High Risk IP Ranges (Tor exit nodes, known malicious hosting)
HIGH_RISK_IP_RANGES = [
    '185.220.',  # Tor exit nodes
    '45.142.',   # High-risk hosting
    '123.45.',   # Example suspicious range
]

# Directory Traversal / Scanning Patterns
SUSPICIOUS_PATHS = [
    '/.env', '/wp-admin', '/admin', '/config.php',
    '/.git', '/phpmyadmin', '/backup.sql', '/.aws',
    '/etc/passwd', '../', '..\\', '/wp-config.php'
]

# Slack Webhook Configuration (optional)
# Set this environment variable to enable Slack notifications
SLACK_WEBHOOK_URL = None  # Will be loaded from environment variable

# Alert Severity Thresholds
ALERT_SEVERITIES = {
    'LOW': {
        'send_slack': False,
        'send_email': False,
    },
    'MEDIUM': {
        'send_slack': True,
        'send_email': False,
    },
    'HIGH': {
        'send_slack': True,
        'send_email': False,  # Changed from True to disable emails
    },
    'CRITICAL': {
        'send_slack': True,
        'send_email': False,  # Changed from True to disable emails
    }
}
