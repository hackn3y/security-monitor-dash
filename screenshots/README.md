# Screenshots

## How to Take Dashboard Screenshot

Since the stack is currently deleted, you have two options:

### Option 1: Open Dashboard Locally (Quick)

1. Open `dashboard/index.html` in your browser (just double-click the file)
2. It will show the layout but say "No data" - that's fine for a screenshot
3. Take a screenshot showing the dashboard interface
4. Save as `dashboard.png` in this directory

### Option 2: Redeploy Temporarily (Best Quality)

1. Redeploy the stack:
   ```powershell
   sam build && sam deploy
   ```

2. Get the dashboard URL:
   ```powershell
   aws cloudformation describe-stacks --stack-name security-monitoring --query 'Stacks[0].Outputs[?OutputKey==`DashboardURL`].OutputValue' --output text
   ```

3. Open in browser, configure API endpoint, let it load data

4. Take screenshot with Windows Snipping Tool:
   - Press `Windows + Shift + S`
   - Select area to capture
   - Screenshot is copied to clipboard
   - Open Paint (`mspaint`) and paste (Ctrl+V)
   - Save as `dashboard.png` in this directory

5. Delete stack when done:
   ```powershell
   aws cloudformation delete-stack --stack-name security-monitoring
   ```

### Taking the Screenshot

**What to capture:**
- Full browser window showing the dashboard
- Include the stats cards at top (Total Events, Alerts, etc.)
- Include at least one alert in the timeline
- Include the event table at bottom

**Tools:**
- **Windows Snipping Tool**: `Windows + Shift + S`
- **Full Screenshot**: `Windows + PrtScn` (saves to Pictures/Screenshots)
- **Browser DevTools**: F12 → Device toolbar → Responsive view

### After You Have the Screenshot

1. Save it as `dashboard.png` in this `screenshots/` folder
2. Commit and push:
   ```powershell
   git add screenshots/dashboard.png
   git commit -m "Add dashboard screenshot"
   git push
   ```

The README will automatically show it!
