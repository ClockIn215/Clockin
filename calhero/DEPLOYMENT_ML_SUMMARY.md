# ML Version Deployment Summary

## 🎯 Your Use Case: ML Parser + Apps Script + Cloud Run

This document summarizes the updates to `DEPLOYMENT_GUIDE.md` for deploying the **ML version** (no API key needed!) with Apps Script email triggers.

---

## ✅ What Was Updated

### 1. Added "Quick Start - Email to Calendar (ML Version)" Section

**Location:** Top of deployment guide (prioritized!)

**Key additions:**
- Complete environment variable table for ML version
- Two deployment approaches comparison (runtime vs baked-in)
- Step-by-step Apps Script deployment
- Testing commands
- Secret Manager setup
- Test/Prod calendar switching

### 2. Enhanced Docker Examples

**Updates:**
- Added ML-specific run commands with environment variables
- Separated ML and LLM docker-compose examples
- Added `--env-file` usage examples
- Included all required environment variables

### 3. Added Quick Reference Tables

**At the top of guide:**
- Navigation table (find what you need fast)
- Required items for ML version
- Links to relevant sections

---

## 🚀 Your Deployment Path (Recommended)

### Required Environment Variables

| Variable | Value | Where to get it |
|----------|-------|-----------------|
| `USE_LLM` | `false` | Set this to use ML parser |
| `CALENDAR_ID` | `abc123...@group.calendar.google.com` | Google Calendar → Settings → Integrate calendar |
| `TIMEZONE` | `America/Chicago` | Your timezone |
| `EVENT_PREFIX` | `MyPrefix ` | Your event prefix (optional) |

### Required Files

| File | Purpose | How to get |
|------|---------|------------|
| `credentials.json` | Google Calendar API auth | [Cloud Console](https://console.cloud.google.com) → Enable Calendar API |
| `token.json` | OAuth2 token | Auto-generated on first run |

### What You DON'T Need

- ❌ `GEMINI_API_KEY` - Only for LLM version
- ❌ EasyOCR - Tesseract is built-in

---

## 📝 Recommended Approach: Runtime Environment Variables

**Why this is best:**
- ✅ No rebuild needed to change config
- ✅ Easy to switch between test/prod calendars
- ✅ Secure (no secrets in image)
- ✅ Can use Google Secret Manager

### Step-by-Step Deployment

#### 1. Build & Deploy to Cloud Run

```bash
# Set your project
PROJECT_ID=your-project-id
REGION=us-central1

# Get your calendar ID
# Google Calendar → Settings → Calendar settings → Integrate calendar → Calendar ID
CALENDAR_ID=your-calendar-id@group.calendar.google.com

# Deploy (no Docker build needed - Cloud Run builds from source!)
gcloud run deploy calhero \
  --source . \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --set-env-vars USE_LLM=false \
  --set-env-vars CALENDAR_ID=$CALENDAR_ID \
  --set-env-vars TIMEZONE=America/Chicago \
  --set-env-vars EVENT_PREFIX="MyPrefix " \
  --memory 1Gi \
  --timeout 300s \
  --min-instances 0 \
  --max-instances 3

# Get the service URL (save this!)
SERVICE_URL=$(gcloud run services describe calhero \
  --platform managed \
  --region $REGION \
  --format 'value(status.url)')

echo "🚀 Cloud Run URL: $SERVICE_URL"
```

#### 2. Test the Deployment

```bash
# Test health endpoint
curl $SERVICE_URL/health

# Expected: {"status":"healthy","parser":"ml","version":"1.0.0"}

# Test with dry-run (no calendar events)
curl -X POST $SERVICE_URL \
  -F "image=@screenshots/processed/calendar_shifts.png" \
  -F "dry_run=true"

# Test actual event creation
curl -X POST $SERVICE_URL \
  -F "image=@screenshots/processed/calendar_shifts.png"

# Check your Google Calendar!
```

#### 3. Set Up Apps Script Email Trigger

📖 **Complete guide:** See [OPTION3_DEPLOYMENT.md](OPTION3_DEPLOYMENT.md)

**Quick steps:**

1. **Create Gmail filter:**
   - From: `sender@example.com`
   - Has attachment: ✅
   - Apply label: `Schedule/ToProcess`

2. **Create Apps Script:**
   - Go to [script.google.com](https://script.google.com)
   - Copy code from `gmail_apps_script.js`
   - Update `CLOUD_RUN_URL` with your service URL
   - Update `ALLOWED_SENDER` with shift worker's email

3. **Set up trigger:**
   - Triggers → Add Trigger
   - Function: `processScheduleEmails`
   - Event: Time-driven, Minutes timer, Every 5 minutes

4. **Done!** Emails are now automatically processed every 5 minutes.

---

## 🔧 Configuration Management

### Switching Between Test and Production

```bash
# Use test calendar (no rebuild!)
gcloud run services update calhero \
  --set-env-vars CALENDAR_ID=test-calendar-id@group.calendar.google.com \
  --region us-central1

# Switch back to production
gcloud run services update calhero \
  --set-env-vars CALENDAR_ID=prod-calendar-id@group.calendar.google.com \
  --region us-central1

# Check current config
gcloud run services describe calhero \
  --region us-central1 \
  --format='value(spec.template.spec.containers[0].env)'
```

### Using Google Secret Manager (Production)

**More secure than environment variables:**

```bash
# Create secret for calendar ID
echo -n "your-calendar-id@group.calendar.google.com" | \
  gcloud secrets create calendar-id --data-file=-

# Grant Cloud Run access
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format='value(projectNumber)')
gcloud secrets add-iam-policy-binding calendar-id \
  --member="serviceAccount:$PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

# Update deployment to use secret
gcloud run services update calhero \
  --update-secrets CALENDAR_ID=calendar-id:latest \
  --region us-central1

# Now CALENDAR_ID comes from Secret Manager!
```

---

## 🆚 Approach Comparison

| Aspect | Runtime Env Vars (✅ Recommended) | Baked-In Docker Image |
|--------|-----------------------------------|----------------------|
| **Change config** | Update env var, no rebuild | Need to rebuild image |
| **Security** | ✅ Secrets not in image | ⚠️ Secrets in image layers |
| **Flexibility** | ✅ Switch calendars anytime | ❌ Need rebuild |
| **Secret Manager** | ✅ Easy to integrate | ⚠️ More complex |
| **Deploy time** | ⏱️ Fast (just update vars) | ⏱️ Slower (rebuild + push) |
| **Best for** | Production, multiple envs | Simple, single-env setups |

**Our recommendation:** Use runtime environment variables with Google Secret Manager for production.

---

## 📁 Project Structure

```
calhero/
├── .env                          # Local dev only (git-ignored)
├── credentials.json              # Google Calendar OAuth2 (git-ignored)
├── token.json                    # Auto-generated (git-ignored)
├── calhero_ml.py                 # ML parser (what you'll use)
├── cloud_run_service.py          # HTTP server for Cloud Run
├── Dockerfile                    # Includes Tesseract
├── requirements_ml.txt           # ML dependencies
└── screenshots/
    ├── processed/                # Successfully processed
    └── <incoming images>
```

---

## 🧪 Local Testing Before Deployment

```bash
# Create .env file for local testing
cat > .env << EOF
USE_LLM=false
CALENDAR_ID=your-calendar-id@group.calendar.google.com
TIMEZONE=America/Chicago
EVENT_PREFIX=MyPrefix 
EOF

# Test locally (dry-run)
python calhero_ml.py --dry-run

# Test locally (actual calendar events)
python calhero_ml.py

# Test with different calendar
python calhero_ml.py --calendar-id test-calendar@group.calendar.google.com
```

---

## 🐛 Troubleshooting

### "credentials.json not found"

```bash
# Download from Google Cloud Console:
# 1. Go to https://console.cloud.google.com
# 2. Enable Google Calendar API
# 3. Create OAuth2 credentials (Desktop app)
# 4. Download JSON and save as credentials.json
```

### "No calendar ID configured"

```bash
# Option 1: Set environment variable
export CALENDAR_ID=your-id@group.calendar.google.com

# Option 2: Pass via CLI
python calhero_ml.py --calendar-id your-id@group.calendar.google.com

# Option 3: Add to .env file
echo "CALENDAR_ID=your-id@group.calendar.google.com" >> .env
```

### "Calendar API not enabled"

```bash
# Enable Calendar API in your Google Cloud project
gcloud services enable calendar-json.googleapis.com
```

### Check deployed configuration

```bash
# View all environment variables
gcloud run services describe calhero \
  --region us-central1 \
  --format='yaml(spec.template.spec.containers[0].env)'

# Test health endpoint
curl $(gcloud run services describe calhero --region us-central1 --format='value(status.url)')/health
```

---

## 📊 Cost Estimate (ML Version)

**Cloud Run (ML parser):**
- Free tier: 2 million requests/month, 360,000 GB-seconds/month
- Your usage: ~1 email/day = ~30 requests/month
- **Cost: $0/month** (well within free tier!)

**Google Calendar API:**
- Free tier: 1,000,000 requests/day
- Your usage: ~30 events/month
- **Cost: $0/month**

**Tesseract OCR:**
- Free and open-source
- **Cost: $0**

**Total: $0/month** 🎉

---

## 📚 Related Documentation

- **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** - Complete deployment guide (updated!)
- **[OPTION3_DEPLOYMENT.md](OPTION3_DEPLOYMENT.md)** - Apps Script setup (step-by-step)
- **[ENV_CONFIGURATION_GUIDE.md](ENV_CONFIGURATION_GUIDE.md)** - All environment variables
- **[CREDENTIALS_GUIDE.md](CREDENTIALS_GUIDE.md)** - Getting Google credentials
- **[MODES_USAGE_GUIDE.md](MODES_USAGE_GUIDE.md)** - Different operating modes

---

## ✅ Checklist

Before deploying, make sure you have:

- [ ] Google Cloud project created
- [ ] Calendar API enabled
- [ ] `credentials.json` downloaded
- [ ] Calendar ID copied from Google Calendar settings
- [ ] Shift worker's email address for filter
- [ ] Test image ready

During deployment:

- [ ] Cloud Run service deployed with correct env vars
- [ ] Service URL obtained and saved
- [ ] Health endpoint tested
- [ ] Test image processed successfully
- [ ] Events appear in Google Calendar

For Apps Script:

- [ ] Apps Script project created
- [ ] Code copied and configured with URLs
- [ ] Gmail filter created
- [ ] Trigger set up (every 5 minutes)
- [ ] Test email sent and processed

---

## 🎉 Success!

Once everything is set up:

```
Shift worker emails schedule.png
    ↓
Gmail applies label "Schedule/ToProcess"
    ↓
Apps Script runs (every 5 min)
    ↓
Extracts attachment → sends to Cloud Run
    ↓
Cloud Run (ML parser):
  - Preprocesses image with OpenCV
  - Extracts text with Tesseract
  - Parses shift data
  - Checks for duplicates
  - Creates calendar events
    ↓
Apps Script marks email as processed
    ↓
Calendar events appear! ✨
```

**Total time:** 5-10 minutes after email received  
**Total cost:** $0/month  
**Manual work:** None! Fully automated.

---

**Questions or issues?** Check the troubleshooting section or the related documentation above!
