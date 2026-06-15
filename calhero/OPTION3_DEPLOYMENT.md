# Option 3 Deployment Guide: Gmail → Apps Script → Cloud Run

Complete step-by-step guide for the simplest email trigger setup.

## 🎯 Architecture Overview

```
Shift worker sends email with screenshot
    ↓
Gmail filter applies label "Schedule/ToProcess"
    ↓
Apps Script (runs every 5 min) checks for labeled emails
    ↓
Extracts attachment and sends to Cloud Run
    ↓
Cloud Run parses schedule and adds to calendar
    ↓
Apps Script marks email as processed
    ↓
Done! ✨
```

**Pros:**
- ✅ Simple setup (no Gmail API configuration)
- ✅ Works immediately after deployment
- ✅ Easy to debug (see logs in Apps Script)
- ✅ Can reply to sender with confirmation
- ✅ Free (within Gmail API limits)

**Cons:**
- ⚠️ Up to 5-minute delay (trigger interval)
- ⚠️ Not truly "real-time"

---

## 📋 Prerequisites

- [x] Google Cloud account
- [x] Gmail account (same as Calendar)
- [x] Cloud Run service deployed (see below)
- [x] Shift worker's email address

---

## Step 1: Deploy Cloud Run Service

### Option A: Quick Deploy (Recommended)

```bash
# Clone/navigate to your calhero directory
cd /path/to/calhero

# Deploy with ML parser (free, no API key needed)
gcloud run deploy calhero \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars USE_LLM=false \
  --memory 1Gi \
  --timeout 300s \
  --min-instances 0 \
  --max-instances 3
```

### Option B: Deploy with LLM Parser

```bash
gcloud run deploy calhero \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars USE_LLM=true,GEMINI_API_KEY=your_api_key_here \
  --memory 1Gi \
  --timeout 300s
```

### Option C: Build Docker First (More Control)

```bash
# Build with both parsers
docker build -t gcr.io/YOUR_PROJECT_ID/calhero .

# Push to Container Registry
docker push gcr.io/YOUR_PROJECT_ID/calhero

# Deploy
gcloud run deploy calhero \
  --image gcr.io/YOUR_PROJECT_ID/calhero \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars USE_LLM=false
```

### Get Your Service URL

After deployment:

```bash
# Get the URL
SERVICE_URL=$(gcloud run services describe calhero \
  --platform managed \
  --region us-central1 \
  --format 'value(status.url)')

echo "Your Cloud Run URL: $SERVICE_URL"
```

**Copy this URL** - you'll need it for Apps Script!

### Test the Service

```bash
# Test health endpoint
curl $SERVICE_URL/health

# Should return:
# {"status":"healthy","parser":"ml","version":"1.0.0"}

# Test with an image
curl -X POST $SERVICE_URL \
  -F "image=@screenshots/processed/schedule.png" \
  -F "dry_run=true"
```

---

## Step 2: Set Up Google Apps Script

### 2.1 Create New Project

1. Go to [script.google.com](https://script.google.com)
2. Click **"New Project"**
3. Name it: `Calendar Parser - Email Processor`

### 2.2 Add the Code

1. Delete the default `myFunction()` code
2. Copy **all** code from `gmail_apps_script.js`
3. Paste into the editor

### 2.3 Update Configuration

Find these lines at the top and update:

```javascript
// IMPORTANT: Replace with your Cloud Run service URL
const CLOUD_RUN_URL = 'https://calhero-xxxxx-uc.a.run.app';  // ← YOUR URL HERE

// Sender email (shift worker's email address)
const ALLOWED_SENDER = 'sender@example.com';  // ← SHIFT WORKER EMAIL HERE

// OPTIONAL: Override calendar ID (leave empty to use Cloud Run default)
// This lets you change calendars without updating Cloud Run!
const CALENDAR_ID_OVERRIDE = '';  // ← ADD YOUR CALENDAR ID HERE (optional)
```

**💡 Pro Tip:** Use `CALENDAR_ID_OVERRIDE` to:
- Switch between test/production calendars instantly
- Use different calendars per user without updating Cloud Run
- See [CALENDAR_OVERRIDE_GUIDE.md](CALENDAR_OVERRIDE_GUIDE.md) for details

### 2.4 Test Configuration

1. In the Apps Script editor, select function: `testConfiguration`
2. Click **Run** (▶️ button)
3. **First time:** You'll be asked to authorize
   - Click "Review Permissions"
   - Select your Google account
   - Click "Advanced" → "Go to Calendar Parser (unsafe)"
   - Click "Allow"
4. Check the logs (View → Logs or Ctrl+Enter)

**Expected output:**
```
🔧 Configuration Test
====================
Cloud Run URL: https://calhero-xxxxx.run.app
Allowed sender: sender@example.com
Watch label: Schedule/ToProcess
Processed label: Schedule/Processed

Testing Cloud Run health endpoint...
✅ Health check passed: {"status":"healthy","parser":"ml"}

Checking labels...
✅ Labels ready: Schedule/ToProcess, Schedule/Processed
```

---

## Step 3: Create Gmail Filter

### 3.1 Open Gmail Filter Settings

1. Go to [Gmail](https://mail.google.com)
2. Click ⚙️ (Settings) → "See all settings"
3. Go to "Filters and Blocked Addresses" tab
4. Click "Create a new filter"

### 3.2 Configure Filter

**Filter criteria:**
- **From:** `sender@example.com` (shift worker's email)
- **Has attachment:** ✅ (check this box)
- **Subject:** `schedule` (optional - keyword in subject)

Click "Create filter"

**Filter actions:**
- ✅ **Apply the label:** Select "New label..." → Create `Schedule/ToProcess`
- ✅ **Skip the Inbox** (optional - keeps inbox clean)
- ⬜ **Mark as read** (optional - your preference)

Click "Create filter"

### 3.3 Verify Filter

The filter should look like:
```
Matches: from:(sender@example.com) has:attachment subject:(schedule)
Do this: Apply label "Schedule/ToProcess"
```

---

## Step 4: Set Up Automatic Trigger

### 4.1 Create Time-Based Trigger

1. In Apps Script editor, click **Triggers** (⏰ clock icon on left)
2. Click **"+ Add Trigger"** (bottom right)

**Configure trigger:**
- Choose function: `processScheduleEmails`
- Choose deployment: `Head`
- Select event source: `Time-driven`
- Select type: `Minutes timer`
- Select interval: `Every 5 minutes`

Click **Save**

### 4.2 Authorize Trigger

First time authorization:
1. Click "Advanced"
2. Click "Go to Calendar Parser (unsafe)"
3. Click "Allow"

**Note:** This is safe - it's your own script!

---

## Step 5: Test End-to-End

### 5.1 Send Test Email

Have the shift worker send a test email:

**To:** Your Gmail address  
**Subject:** `My schedule for next week`  
**Attachment:** Screenshot of schedule  
**Body:** (anything)

### 5.2 Option A: Manual Test (Immediate)

Don't want to wait 5 minutes? Run manually:

1. Go to Apps Script editor
2. Select function: `testProcessing`
3. Click **Run** (▶️)
4. Check logs (Ctrl+Enter)

**Expected logs:**
```
🔍 Checking for new schedule emails...
📧 Found 1 email(s) to process
  📨 Processing: "My schedule for next week" from sender@example.com
  📎 Found image: schedule.png
  🚀 Sending to Cloud Run...
  📡 Response code: 200
  ✅ Success! Created 5 shift(s)
  📊 Parser used: ML/OCR (Tesseract)
  💌 Sent success reply to sender
✅ Processing complete!
```

### 5.3 Option B: Wait for Trigger

If you prefer to test the automatic trigger:
1. Wait up to 5 minutes
2. Check Apps Script logs: View → Executions
3. Should see successful execution

### 5.4 Verify Results

Check three things:

1. **Gmail:**
   - Email should have `Schedule/Processed` label
   - Email should be removed from `Schedule/ToProcess` label

2. **Calendar:**
   - Open Google Calendar
   - Look for new events (with your configured EVENT_PREFIX)

3. **Reply Email** (optional):
   - Shift worker should receive confirmation email with results

---

## 🐛 Troubleshooting

### Problem: "Cloud Run returned 404"

**Solution:** Check your CLOUD_RUN_URL
```javascript
// In Apps Script, run:
function testCloudRunConnection() { ... }
```

### Problem: "No emails found"

**Checklist:**
- ✅ Email is from correct sender?
- ✅ Email has attachment?
- ✅ Gmail filter applied label?
- ✅ Email is less than 24 hours old?

**Debug:**
```javascript
// In Apps Script, check query:
function debugQuery() {
  const query = `from:${ALLOWED_SENDER} has:attachment label:${WATCH_LABEL}`;
  Logger.log(query);
  const threads = GmailApp.search(query);
  Logger.log(`Found ${threads.length} threads`);
}
```

### Problem: "Permission denied"

**Solution:** Re-authorize the script
1. Go to script.google.com
2. Open your project
3. Run any function
4. Click "Review Permissions" → Allow

### Problem: "Cloud Run timeout"

**Solution:** Increase timeout
```bash
gcloud run services update calhero \
  --timeout 600s \
  --memory 2Gi
```

### Problem: "Labels not found"

**Solution:** Run `testConfiguration()` to create labels automatically

---

## 📊 Monitoring

### View Execution History

1. Go to Apps Script editor
2. Click **Executions** (📊 icon on left)
3. See all runs with status and duration

### View Detailed Logs

1. Click on any execution
2. See detailed logs for that run

### Enable Error Notifications

Apps Script automatically emails you if:
- Script fails 3+ times in a row
- Trigger fails to run

Plus, the script includes custom error notifications:
```javascript
function sendErrorNotification(error) {
  // Sends email to script owner with error details
}
```

### Monitor Cloud Run

```bash
# View recent logs
gcloud run services logs read calhero --limit 50

# Stream live logs
gcloud run services logs tail calhero
```

---

## 🔧 Customization Options

### Change Processing Interval

In Apps Script triggers, change interval:
- Every 1 minute (fastest, uses more quota)
- Every 5 minutes (recommended)
- Every 10 minutes (slower but more conservative)

### Add Custom Reply Message

Edit `sendSuccessReply()` function:
```javascript
const replyBody = `
Hey babe! Your schedule is updated! 💕

I found ${result.shifts_created} shifts and added them to our calendar.

Love you! 😘
`.trim();
```

### Filter by Subject Keyword

Update Gmail filter to require specific subject:
```
from:sender@example.com has:attachment subject:"my schedule"
```

### Process All Emails (No Filter)

Remove the label requirement in Apps Script:
```javascript
const query = `from:${ALLOWED_SENDER} has:attachment -label:${PROCESSED_LABEL}`;
```

### Use LLM Parser Instead

Update Cloud Run env variable:
```bash
gcloud run services update calhero \
  --set-env-vars USE_LLM=true,GEMINI_API_KEY=your_key
```

---

## 💰 Cost Analysis

**Typical usage: 50 schedules/month**

| Component | Cost |
|-----------|------|
| Gmail API (Apps Script) | Free (well within limits) |
| Cloud Run (ML parser) | $0-1 (mostly free tier) |
| Cloud Run (LLM parser) | +$0.05 (Gemini API) |
| **Total** | **~$0-1/month** |

**Gmail API Limits:**
- 20,000 requests/day (you'll use ~100/day)
- 2,000 emails/day (you'll use ~2/day)

---

## 🎉 You're Done!

**What happens now:**

1. Shift worker takes screenshot on phone
2. Emails to you with "schedule" in subject
3. Gmail auto-labels it
4. Within 5 minutes, Apps Script processes it
5. Cloud Run parses and adds to calendar
6. Sender gets confirmation email
7. Schedule appears in shared calendar

**Total time:** ~5 minutes from email to calendar ✨

---

## 📚 Additional Resources

- [Apps Script Documentation](https://developers.google.com/apps-script)
- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Gmail Filter Guide](https://support.google.com/mail/answer/6579)

---

## 🔄 Updates & Maintenance

### Update Apps Script Code

1. Edit code in Apps Script editor
2. Save (Ctrl+S)
3. Changes take effect immediately

### Update Cloud Run Service

```bash
# Redeploy with changes
gcloud run deploy calhero --source .

# Or update env variables only
gcloud run services update calhero \
  --set-env-vars USE_LLM=true
```

### Disable Temporarily

**Disable trigger:**
1. Go to Apps Script → Triggers
2. Click ⋮ (three dots) next to trigger
3. Click "Delete"

**Re-enable later:**
- Add trigger again (same steps as before)

---

**Questions?** Check the logs first! Both Apps Script and Cloud Run have detailed logging.
