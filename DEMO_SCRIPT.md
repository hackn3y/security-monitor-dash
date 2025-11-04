# Demo Video Script (3 minutes)

## Pre-Recording Setup

```powershell
# 1. Deploy the stack
sam build && sam deploy

# 2. Get endpoints
$API = aws cloudformation describe-stacks --stack-name security-monitoring --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' --output text
$DASHBOARD = aws cloudformation describe-stacks --stack-name security-monitoring --query 'Stacks[0].Outputs[?OutputKey==`DashboardURL`].OutputValue' --output text

# 3. Open dashboard and configure API endpoint
start $DASHBOARD

# 4. Open Slack workspace in another tab
# 5. Have PowerShell ready with traffic simulator commands
# 6. Start recording (Windows + G)
```

---

## Video Script (2:30 duration)

### **Scene 1: Introduction (0:00-0:20)**

**[Show GitHub repo page]**

**Say:**
> "Hi, I'm [your name], and this is my serverless security monitoring dashboard. It's built entirely on AWS using Lambda, DynamoDB, and API Gateway. The system detects 11 different types of security threats in real-time and sends alerts via Slack."

**[Scroll through README briefly showing badges and architecture diagram]**

---

### **Scene 2: Dashboard Overview (0:20-0:45)**

**[Switch to Dashboard tab]**

**Say:**
> "Here's the live dashboard. It's already processing events - you can see total events, alerts, and critical alerts updating in real-time. The system auto-generates simulated traffic for testing, but it can ingest events from any source via the REST API."

**[Point to/hover over each section]:**
- Stats cards at top
- Recent alerts section
- Event analytics charts
- Event table at bottom

---

### **Scene 3: Threat Detection Demo (0:45-1:45)**

**[Switch to PowerShell]**

**Say:**
> "Let me demonstrate the threat detection. I'll run my traffic simulator to generate a brute force attack."

**Run command:**
```powershell
python scripts/traffic-simulator.py --endpoint $API --scenario brute-force
```

**[Show output as it runs]**

**Say:**
> "The simulator just sent 8 failed login attempts from the same IP address within 5 minutes. The detection Lambda is analyzing these events in real-time using DynamoDB Streams..."

**[Switch to Dashboard - refresh if needed]**

**Say:**
> "And here we go - a HIGH severity brute force attack detected. You can see the alert details: the source IP, number of failed attempts, and the time window. This alert was created automatically by analyzing event patterns."

**[Click or highlight the brute force alert]**

---

### **Scene 4: Slack Integration (1:45-2:10)**

**[Switch to Slack tab]**

**Say:**
> "Because this is a HIGH severity alert, it was also sent to Slack. Here's the notification with color-coded severity, the detection rule that triggered, source IP, username targeted, and all the event details. This would notify the security team immediately."

**[Show the Slack alert message]**

---

### **Scene 5: More Attack Types (2:10-2:30)**

**[Switch back to PowerShell]**

**Say:**
> "Let me show you another attack type - SQL injection detection."

**Run command:**
```powershell
python scripts/traffic-simulator.py --endpoint $API --scenario scanning
```

**[Switch to Dashboard]**

**Say:**
> "Within seconds, we're detecting directory traversal and scanning attempts. The system currently has 11 detection rules including SQL injection, credential stuffing, API rate limiting, privilege escalation, and data exfiltration - all running serverless and costing only $15 to $40 per month."

**[Show new alerts appearing]**

---

### **Scene 6: Closing (2:30-2:45)**

**[Show GitHub repo again or CloudWatch dashboard]**

**Say:**
> "The entire infrastructure is defined as code using AWS SAM. You can deploy it to your own AWS account in about 10 minutes. All the code, documentation, and deployment scripts are on GitHub. Thanks for watching!"

**[End with GitHub repo URL on screen]**

---

## Recording Tips

### **Tools:**
- **Windows Game Bar**: Press `Windows + G` to start recording
- **OBS Studio**: Free, more professional (download from obsproject.com)
- **Loom**: Easy browser-based recording (loom.com)

### **Setup:**
- Use 1920x1080 resolution
- Close unnecessary tabs/windows
- Turn on "Do Not Disturb"
- Have a quiet environment
- Use headphones/mic for better audio

### **Editing:**
- Windows Photos app (free, built-in)
- DaVinci Resolve (free, professional)
- Just trim beginning/end if needed

### **Browser Tips:**
```
Zoom dashboard: Ctrl + (to make stats more visible)
Full screen: F11 (hides browser UI)
DevTools responsive mode: F12 → device toolbar → set to 1920x1080
```

---

## Alternative: Shorter Version (90 seconds)

If you want super quick:

1. **Dashboard overview** (20s) - "Here's the live dashboard processing events"
2. **Run attack** (30s) - "Running brute force simulator... alert detected"
3. **Show Slack** (20s) - "HIGH severity alert sent to Slack"
4. **Close** (20s) - "11 detection rules, fully serverless, $15/month, code on GitHub"

---

## After Recording

### **Upload to YouTube:**

1. Make it **Unlisted** (not public, only people with link can view)
2. Title: "AWS Serverless Security Monitoring Dashboard - Live Demo"
3. Description:
```
Real-time security threat detection using AWS Lambda, DynamoDB Streams, and API Gateway.

Features:
✅ 11 threat detection rules (brute force, SQL injection, credential stuffing, etc.)
✅ Event-driven architecture with DynamoDB Streams
✅ Slack + SNS notifications
✅ Real-time dashboard
✅ Infrastructure as Code (AWS SAM)
✅ $15-40/month on AWS

GitHub: https://github.com/hackn3y/security-monitor-dash

Tech Stack: Python, AWS Lambda, DynamoDB, API Gateway, CloudWatch, SNS, Slack
```

4. Add to README:
```markdown
## 🎥 Live Demo

Watch the system in action: [3-minute demo video](https://youtu.be/YOUR_VIDEO_ID)

See real-time threat detection, Slack notifications, and the complete workflow from event ingestion to alert generation.
```

---

## Cleanup After Recording

```powershell
# Delete the stack
aws cloudformation delete-stack --stack-name security-monitoring

# Empty and delete buckets
aws s3 rb s3://security-monitoring-dashboard-ACCOUNT-ID --force
aws s3 rb s3://security-monitoring-deploy-BUCKET-NAME --force
```

---

## Pro Tips

✨ **Keep it natural** - Don't read word-for-word, just hit the key points
✨ **Show, don't tell** - Let the visuals do most of the work
✨ **Energy** - Sound enthusiastic but professional
✨ **Practice once** - Do a dry run to get timing right
✨ **Mistakes are OK** - You can edit or just keep going

**Total recording time: 10-15 minutes including setup**

Good luck! 🎬
