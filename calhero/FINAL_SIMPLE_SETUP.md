# Final Simple Setup - Apps Script + Docker + Cloud Run

## ✅ What You Have Now

**Simple, environment-agnostic Docker container that:**
- ✅ Runs HTTP server when no arguments (for Cloud Run/Apps Script)
- ✅ Runs CLI mode when arguments provided (for local use)
- ✅ Not tied to Cloud Run (works anywhere)
- ✅ No calendar override from Apps Script (uses env var only)
- ✅ **Cost: $0/month** for your usage

---

## 🎯 How It Works

### Mode Detection (Environment-Agnostic)

```bash
# entrypoint.sh logic:
if [ $# -eq 0 ]; then
    # No arguments = HTTP server
    exec python cloud_run_service.py
else
    # Arguments = CLI mode
    exec python calhero_ml.py "$@"
fi
```

**Why this is better:**
- ✅ No Cloud Run-specific code (no PORT detection)
- ✅ Works with Cloud Run, Kubernetes, local, anywhere
- ✅ Simple logic: arguments = CLI, no arguments = HTTP

### Architecture Flow

```
Shift worker sends email with schedule
    ↓
Gmail applies label "Schedule/ToProcess"
    ↓
Apps Script (every 5 min) detects email
    ↓
Extracts attachment → HTTP POST to Cloud Run
    ↓
Cloud Run starts container (no arguments)
    ↓
entrypoint.sh: No args → HTTP server mode
    ↓
cloud_run_service.py receives request
    ↓
Uses CALENDAR_ID from environment variable
    ↓
calhero_ml.py processes image (Tesseract OCR)
    ↓
Creates calendar events
    ↓
Apps Script marks email processed
    ↓
Done! ✅
```

---

## 📝 Configuration

### Cloud Run Deployment

**Set calendar once, forget about it:**

```bash
# Build
docker build -t gcr.io/$PROJECT_ID/calhero .
docker push gcr.io/$PROJECT_ID/calhero

# Deploy
gcloud run deploy calhero \
  --image gcr.io/$PROJECT_ID/calhero \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars USE_LLM=false \
  --set-env-vars CALENDAR_ID=your-calendar-id@group.calendar.google.com \
  --set-env-vars TIMEZONE=America/Chicago \
  --set-secrets=/app/credentials.json=calendar-credentials:latest \
  --set-secrets=/app/token.json=calendar-token:latest \
  --memory 1Gi \
  --timeout 300s \
  --min-instances 0 \
  --max-instances 1
```

**That's it!** Calendar ID is set in Cloud Run, not passed from Apps Script.

### Apps Script Configuration

**Simple - just set the URL:**

```javascript
// gmail_apps_script.js

const CLOUD_RUN_URL = 'https://calhero-xxxxx-uc.a.run.app';
const ALLOWED_SENDER = 'sender@example.com';

// No calendar override - it's set in Cloud Run!
```

---

## 🧪 Testing

### Test 1: HTTP Server Mode (Cloud Run)

```bash
# Run without arguments = HTTP server
docker run -p 8080:8080 \
  -e USE_LLM=false \
  -e CALENDAR_ID=test@group.calendar.google.com \
  -e PORT=8080 \
  calhero

# Output:
# 🚀 Calendar Parser Starting...
#    Mode: HTTP Server
#    Port: 8080
#    Starting Flask HTTP server...

# Test it:
curl http://localhost:8080/health
# {"status":"healthy","parser":"ml"}
```

### Test 2: CLI Mode (Local)

```bash
# Run WITH arguments = CLI mode
docker run -it \
  -v $(pwd)/screenshots:/app/screenshots \
  -e USE_LLM=false \
  calhero --dry-run

# Output:
# 🚀 Calendar Parser Starting...
#    Mode: CLI (processing files)
#    Using: ML/OCR Parser (Tesseract)
```

### Test 3: Cloud Run Deployment

```bash
# Deploy
gcloud run deploy calhero --image gcr.io/$PROJECT_ID/calhero \
  --set-env-vars USE_LLM=false,CALENDAR_ID=test@group.calendar.google.com

# Get URL
SERVICE_URL=$(gcloud run services describe calhero --format='value(status.url)')

# Test health
curl $SERVICE_URL/health

# Test with image
curl -X POST $SERVICE_URL \
  -F "image=@screenshots/schedule.png" \
  -F "dry_run=true"
```

---

## 💰 Cost Analysis

**Your usage: 5 requests/week ≈ 20/month**

| Resource | Monthly Usage | Free Tier | Cost |
|----------|---------------|-----------|------|
| Requests | 20 | 2 million | **$0** |
| CPU | 40 vCPU-seconds | 360,000 | **$0** |
| Memory | 40 GiB-seconds | 360,000 | **$0** |
| Container running | Only during requests | N/A | **$0** |

**Total: $0/month** ✅

With `--min-instances 0`:
- Container starts on-demand
- Runs for ~2 seconds per request
- Shuts down after inactivity
- No idle charges

---

## 🔧 How to Change Calendar

### Option 1: Update Cloud Run (Recommended)

```bash
# Change calendar anytime
gcloud run services update calhero \
  --set-env-vars CALENDAR_ID=new-calendar@group.calendar.google.com
```

No rebuild needed! Takes ~10 seconds.

### Option 2: Rebuild (If changing other things)

```bash
docker build -t gcr.io/$PROJECT_ID/calhero .
docker push gcr.io/$PROJECT_ID/calhero

gcloud run services update calhero \
  --image gcr.io/$PROJECT_ID/calhero
```

---

## 📊 What's Simple About This

### Removed Complexity:
- ❌ No PORT detection (Cloud Run-specific)
- ❌ No calendar_id parameter from Apps Script
- ❌ No URL construction with query parameters
- ❌ No calendar override logic

### What Remains (Essential):
- ✅ HTTP server for Apps Script requests
- ✅ Calendar ID from environment variable
- ✅ Simple argument detection (args = CLI, no args = HTTP)

### Lines of Code:
- **entrypoint.sh**: 37 lines (was 57)
- **Apps Script changes**: Removed ~15 lines
- **Simpler, cleaner, environment-agnostic**

---

## 🎯 Use Cases

### Use Case 1: Your Setup (Apps Script + Cloud Run)

```bash
# Deploy once
gcloud run deploy calhero --set-env-vars CALENDAR_ID=prod@...

# Apps Script just works
# No parameters needed
```

### Use Case 2: Local Testing

```bash
# Process local files
docker run -v $(pwd)/screenshots:/app/screenshots calhero --dry-run

# HTTP server locally
docker run -p 8080:8080 calhero
curl http://localhost:8080/health
```

### Use Case 3: Kubernetes/Other Platforms

```yaml
# Works on any container platform
apiVersion: v1
kind: Pod
spec:
  containers:
  - name: calhero
    image: gcr.io/project/calhero
    env:
    - name: CALENDAR_ID
      value: "calendar@group.calendar.google.com"
    # No arguments = HTTP server mode
```

---

## ✅ Verification Checklist

After deployment, verify:

- [ ] Container starts successfully
- [ ] Logs show "Mode: HTTP Server"
- [ ] Health endpoint returns 200
- [ ] Apps Script can send requests
- [ ] Events appear in correct calendar
- [ ] Email gets marked as processed

```bash
# Check logs
gcloud run services logs read calhero --limit 20

# Should see:
# 🚀 Calendar Parser Starting...
#    Mode: HTTP Server
#    Port: 8080
#    Starting Flask HTTP server...
```

---

## 📚 Files Changed

| File | What Changed |
|------|--------------|
| **entrypoint.sh** | Simplified: argument-based mode detection (not PORT) |
| **gmail_apps_script.js** | Removed: CALENDAR_ID_OVERRIDE feature |
| **cloud_run_service.py** | No changes (still accepts calendar_id param, just not used) |
| **Dockerfile** | No changes |

---

## 🎉 Summary

### What You Have:
- ✅ Simple, environment-agnostic Docker container
- ✅ HTTP server for Apps Script integration
- ✅ Calendar ID from environment variable
- ✅ No unnecessary complexity
- ✅ $0/month cost
- ✅ Works anywhere (Cloud Run, Kubernetes, local)

### What You Don't Have:
- ❌ Cloud Run-specific code (PORT detection)
- ❌ Calendar override from Apps Script
- ❌ Complex URL parameter passing

### To Deploy:

```bash
# 1. Build
docker build -t gcr.io/$PROJECT_ID/calhero .
docker push gcr.io/$PROJECT_ID/calhero

# 2. Deploy
gcloud run deploy calhero \
  --image gcr.io/$PROJECT_ID/calhero \
  --set-env-vars USE_LLM=false,CALENDAR_ID=your-calendar@... \
  --set-secrets=/app/credentials.json=calendar-credentials:latest \
  --set-secrets=/app/token.json=calendar-token:latest

# 3. Update Apps Script with SERVICE_URL

# 4. Send test email

# Done! ✅
```

---

**This is the sweet spot: Simple, flexible, environment-agnostic, and free.** 🚀
