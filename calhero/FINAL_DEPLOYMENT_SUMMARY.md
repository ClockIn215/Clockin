# Final Deployment Summary - Complete Setup

## ✅ What You Have Now

**Complete, flexible, environment-agnostic setup:**
- ✅ Apps Script + HTTP Server (simplest workflow)
- ✅ Calendar override from Apps Script (optional flexibility)
- ✅ Environment-agnostic Docker (works anywhere)
- ✅ Cost: $0/month for your usage
- ✅ Simple argument-based mode detection

---

## 🎯 Architecture

### Complete Flow

```
Shift worker emails schedule.png
    ↓
Gmail applies label "Schedule/ToProcess"
    ↓
Apps Script (every 5 min) checks Gmail
    ↓
Finds labeled email → extracts attachment
    ↓
HTTP POST to Cloud Run
  with optional ?calendar_id=... parameter
    ↓
Cloud Run starts container (no CLI arguments)
    ↓
entrypoint.sh: No args → HTTP Server mode
    ↓
cloud_run_service.py receives request
    ↓
Checks for calendar_id parameter:
  - If provided → uses it (Apps Script override)
  - If not → uses CALENDAR_ID env var (Cloud Run default)
    ↓
calhero_ml.py processes image with Tesseract
    ↓
Creates events in specified calendar
    ↓
Returns success to Apps Script
    ↓
Apps Script marks email as processed
    ↓
Done! ✅
```

### Mode Detection (Environment-Agnostic)

```bash
# entrypoint.sh
if [ $# -eq 0 ]; then
    # No arguments = HTTP server
    exec python cloud_run_service.py
else
    # Arguments = CLI mode
    exec python calhero_ml.py "$@"
fi
```

**Not Cloud Run-specific!** Works with:
- ✅ Cloud Run
- ✅ Kubernetes
- ✅ Local Docker
- ✅ Any container platform

---

## 📝 Configuration

### 1. Cloud Run Deployment

**Deploy with default calendar:**

```bash
# Build and push
docker build -t gcr.io/$PROJECT_ID/calhero .
docker push gcr.io/$PROJECT_ID/calhero

# Deploy
gcloud run deploy calhero \
  --image gcr.io/$PROJECT_ID/calhero \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars USE_LLM=false \
  --set-env-vars CALENDAR_ID=TEST_CAL_ID@group.calendar.google.com \
  --set-env-vars TIMEZONE=America/Chicago \
  --set-env-vars EVENT_PREFIX="MyPrefix " \
  --update-secrets /secrets/credentials/credentials.json=calendar-credentials:latest \
  --update-secrets /secrets/token/token.json=calendar-token:latest \
  --memory 1Gi \
  --timeout 300s \
  --min-instances 0 \
  --max-instances 1

# Get service URL
SERVICE_URL=$(gcloud run services describe calhero \
  --region us-central1 \
  --format='value(status.url)')

echo "Service URL: $SERVICE_URL"
```

### 2. Apps Script Configuration

**Edit `gmail_apps_script.js`:**

```javascript
// Required configuration
const CLOUD_RUN_URL = 'https://calhero-xxxxx-uc.a.run.app';  // Your URL
const ALLOWED_SENDER = 'sender@example.com';

// Optional: Override calendar ID
const CALENDAR_ID_OVERRIDE = '';  // Empty = use Cloud Run default

// Examples:
// const CALENDAR_ID_OVERRIDE = '';  // Use Cloud Run default
// const CALENDAR_ID_OVERRIDE = 'test-calendar@group.calendar.google.com';  // Override
```

---

## 🎚️ Calendar Priority System

The system uses this priority order:

### Priority 1: Apps Script Override (Highest)

```javascript
const CALENDAR_ID_OVERRIDE = 'test-calendar@group.calendar.google.com';
```

**Result:** Events go to `test-calendar@...` (ignores Cloud Run env var)

### Priority 2: Cloud Run Environment Variable

```bash
gcloud run deploy calhero \
  --set-env-vars CALENDAR_ID=prod-calendar@group.calendar.google.com
```

**Result:** If no override in Apps Script, uses `prod-calendar@...`

### Priority 3: Error

If neither is set, you get an error.

---

## 🔄 Use Cases

### Use Case 1: Normal Operation (Cloud Run Default)

**Apps Script:**
```javascript
const CALENDAR_ID_OVERRIDE = '';  // Empty
```

**Cloud Run:**
```bash
--set-env-vars CALENDAR_ID=prod-calendar@group.calendar.google.com
```

**Result:** Events go to `prod-calendar@...`

### Use Case 2: Testing (Apps Script Override)

**Apps Script:**
```javascript
const CALENDAR_ID_OVERRIDE = 'test-calendar@group.calendar.google.com';
```

**Cloud Run:**
```bash
--set-env-vars CALENDAR_ID=prod-calendar@group.calendar.google.com
```

**Result:** Events go to `test-calendar@...` (override wins!)

**Benefits:**
- ✅ Test without changing Cloud Run
- ✅ Just edit Apps Script and save
- ✅ Instant switch back to prod (clear override)

### Use Case 3: Multiple Users, One Deployment

**Person 1's Apps Script:**
```javascript
const CALENDAR_ID_OVERRIDE = 'person1-calendar@group.calendar.google.com';
```

**Person 2's Apps Script:**
```javascript
const CALENDAR_ID_OVERRIDE = 'person2-calendar@group.calendar.google.com';
```

**Cloud Run:**
```bash
# One deployment serves both!
--set-env-vars CALENDAR_ID=fallback-calendar@group.calendar.google.com
```

**Result:** Each person's events go to their own calendar

---

## 💰 Cost Analysis

**Your usage: 5 requests/week ≈ 20/month**

### Cloud Run Pricing

| Resource | Usage | Free Tier | Actual Cost |
|----------|-------|-----------|-------------|
| Requests | 20/month | 2M/month | **$0** |
| CPU | 40 vCPU-sec | 360,000/month | **$0** |
| Memory | 40 GiB-sec | 360,000/month | **$0** |
| Container idle | 0 (min-instances=0) | N/A | **$0** |

**Total: $0.00/month** ✅

### What Happens:

1. Email arrives → Apps Script waits 0-5 minutes (polling)
2. Apps Script sends HTTP request → Container starts (~3 seconds cold start)
3. Processes image → ~2-3 seconds
4. Container idles → Shuts down after ~15 minutes
5. **Container only runs ~5 seconds per email**

**Even at 100 requests/month: Still $0** (way under free tier)

---

## 🧪 Testing

### Test 1: Health Check

```bash
SERVICE_URL=$(gcloud run services describe calhero --format='value(status.url)')
curl $SERVICE_URL/health

# Expected:
# {"status":"healthy","parser":"ml","version":"1.0.0"}
```

### Test 2: Dry-Run Test

```bash
curl -X POST "$SERVICE_URL?dry_run=true" \
  -F "image=@screenshots/calendar_shifts.png"

# Expected:
# {"success":true,"mode":"dry-run","would_create":5}
```

### Test 3: Test with Calendar Override

```bash
curl -X POST "$SERVICE_URL?calendar_id=test-calendar@group.calendar.google.com" \
  -F "image=@screenshots/calendar_shifts.png"

# Expected:
# {"success":true,"shifts_created":5,"calendar_source":"CLI argument"}
```

### Test 4: Apps Script Configuration Test

In Apps Script editor, run:

```javascript
function testConfiguration() { ... }
```

**Expected logs:**
```
🔧 Configuration Test
====================
Cloud Run URL: https://calhero-xxxxx.run.app
Allowed sender: sender@example.com
Watch label: Schedule/ToProcess
Processed label: Schedule/Processed
Calendar override: test-calendar@group.calendar.google.com

Testing Cloud Run health endpoint...
✅ Health check passed: {"status":"healthy","parser":"ml"}
```

---

## 🔧 Common Operations

### Switch to Test Calendar (Quick!)

**In Apps Script, just edit one line:**

```javascript
// Switch to test
const CALENDAR_ID_OVERRIDE = 'test-calendar@group.calendar.google.com';
```

Save → Done! Next email goes to test calendar.

**No Cloud Run changes needed!**

### Switch Back to Production

```javascript
// Back to production
const CALENDAR_ID_OVERRIDE = '';  // Use Cloud Run default
```

Save → Done! Next email goes to prod calendar.

### Permanently Change Production Calendar

**Option A: Update Cloud Run (affects everyone):**

```bash
gcloud run services update calhero \
  --set-env-vars CALENDAR_ID=new-prod-calendar@group.calendar.google.com
```

Takes ~10 seconds, no rebuild needed.

**Option B: Override in Apps Script (just you):**

```javascript
const CALENDAR_ID_OVERRIDE = 'my-calendar@group.calendar.google.com';
```

Instant!

---

## 🐛 Troubleshooting

### Issue: Apps Script Returns 404

**Check:**
```javascript
// Verify URL is correct
function testCloudRunConnection() { ... }
```

**Fix:** Update `CLOUD_RUN_URL` with actual service URL

### Issue: Events Go to Wrong Calendar

**Check priority:**

1. Apps Script override set? → Uses that
2. Cloud Run `CALENDAR_ID` set? → Uses that
3. Neither set? → Error

**Debug:**
```javascript
// In Apps Script logs, look for:
Logger.log(`📅 Using calendar override: ...`);
// Or check Cloud Run response:
Logger.log(`📅 Calendar source: ...`);
```

### Issue: Container Crashes

**Check logs:**
```bash
gcloud run services logs read calhero --limit 50

# Look for:
# "Mode: HTTP Server" ← Should see this
# "Mode: CLI" ← Shouldn't see this (wrong mode)
```

**If you see "Mode: CLI":**
- Container is receiving arguments (shouldn't be)
- Check Cloud Run configuration

### Issue: Credentials Not Found

**Verify secrets are mounted:**

```bash
gcloud run services describe calhero --format=yaml | grep secrets

# Should see:
# secrets:
# - /app/credentials.json=calendar-credentials:latest
# - /app/token.json=calendar-token:latest
```

---

## 📊 Files Overview

### Configuration Files

| File | Purpose | You Need to Edit |
|------|---------|------------------|
| `gmail_apps_script.js` | Apps Script code | ✅ Yes (URL, email, calendar override) |
| `.env` | Local dev only | ⚠️ Optional (for local testing) |
| `Dockerfile` | Container build | ❌ No |
| `entrypoint.sh` | Mode detection | ❌ No |

### Runtime Files (in Docker)

| File | Purpose | Mode |
|------|---------|------|
| `cloud_run_service.py` | HTTP server | HTTP Server |
| `calhero_ml.py` | ML parser (CLI) | CLI |
| `calhero.py` | LLM parser (CLI) | CLI |
| `calendar_utils.py` | Shared utilities | Both |

### Documentation Files

| File | What It Covers |
|------|----------------|
| **FINAL_DEPLOYMENT_SUMMARY.md** | This file! Complete guide |
| **DEPLOYMENT_GUIDE.md** | Detailed deployment options |
| **CALENDAR_OVERRIDE_GUIDE.md** | Calendar override feature details |
| **OPTION3_DEPLOYMENT.md** | Step-by-step Apps Script setup |
| **ENV_CONFIGURATION_GUIDE.md** | Environment variables |
| **CREDENTIALS_GUIDE.md** | Getting Google credentials |

---

## ✅ Complete Deployment Checklist

### Prerequisites

- [ ] Google Cloud project created
- [ ] Calendar API enabled: `gcloud services enable calendar-json.googleapis.com`
- [ ] `credentials.json` downloaded from Google Cloud Console
- [ ] `token.json` generated (run `python calhero_ml.py --dry-run` locally)
- [ ] Calendar ID copied from Google Calendar settings
- [ ] Shift worker's email address

### Setup Cloud Run

- [ ] Build Docker image: `docker build -t gcr.io/$PROJECT_ID/calhero .`
- [ ] Push to GCR: `docker push gcr.io/$PROJECT_ID/calhero`
- [ ] Upload credentials to Secret Manager
- [ ] Deploy to Cloud Run with env vars and secrets
- [ ] Get service URL: `gcloud run services describe calhero ...`
- [ ] Test health endpoint: `curl $SERVICE_URL/health`
- [ ] Test with sample image: `curl -X POST $SERVICE_URL -F "image=@..."`

### Setup Apps Script

- [ ] Go to [script.google.com](https://script.google.com)
- [ ] Create new project: "Calendar Parser"
- [ ] Copy code from `gmail_apps_script.js`
- [ ] Update `CLOUD_RUN_URL` with your service URL
- [ ] Update `ALLOWED_SENDER` with shift worker's email
- [ ] Set `CALENDAR_ID_OVERRIDE` (optional, can leave empty)
- [ ] Run `testConfiguration()` function
- [ ] Verify health check passes

### Setup Gmail

- [ ] Create Gmail filter:
  - From: shift worker's email
  - Has attachment: Yes
  - Apply label: "Schedule/ToProcess"
- [ ] Verify filter is active

### Setup Trigger

- [ ] In Apps Script, go to Triggers (clock icon)
- [ ] Add trigger:
  - Function: `processScheduleEmails`
  - Event: Time-driven
  - Type: Minutes timer
  - Interval: Every 5 minutes
- [ ] Save trigger
- [ ] Authorize permissions

### Test End-to-End

- [ ] Send test email with schedule screenshot
- [ ] Wait up to 5 minutes (or run `testProcessing()` manually)
- [ ] Check Apps Script logs
- [ ] Verify events appear in Google Calendar
- [ ] Verify email has "Schedule/Processed" label

---

## 🎉 You're Done!

### What You Have:

✅ **Simple workflow** - Shift worker emails → Events in calendar  
✅ **Flexible** - Switch calendars without redeploying  
✅ **Free** - $0/month for your usage  
✅ **Reliable** - No watch expiry, no complex triggers  
✅ **Environment-agnostic** - Docker works anywhere  
✅ **Easy to maintain** - One Apps Script, one Cloud Run service  

### Quick Reference Commands:

```bash
# Check logs
gcloud run services logs read calhero --limit 20

# Update calendar
gcloud run services update calhero \
  --set-env-vars CALENDAR_ID=new-calendar@group.calendar.google.com

# Test health
curl $(gcloud run services describe calhero --format='value(status.url)')/health

# View Apps Script logs
# Go to script.google.com → View → Logs
```

---

## 📞 Support

If something doesn't work:

1. **Check Apps Script logs** - See what's being sent
2. **Check Cloud Run logs** - See what's being received
3. **Test health endpoint** - Verify service is running
4. **Verify credentials** - Check secrets are mounted
5. **Check calendar sharing** - Service account needs access

---

**Deployment complete! Your calendar automation is ready!** 🚀
