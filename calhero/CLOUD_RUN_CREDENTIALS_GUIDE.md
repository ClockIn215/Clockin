# Cloud Run Credentials Guide

## Your Questions Answered

### Q1: How do I pass GEMINI_API_KEY when USE_LLM=true with a Docker image on Cloud Run?

**Answer:** Pass it via `--set-env-vars` or `--update-secrets` at deploy time (same as other env vars).

```bash
# Option A: Via environment variable
gcloud run deploy calhero \
  --image gcr.io/$PROJECT_ID/calhero \
  --set-env-vars USE_LLM=true \
  --set-env-vars GEMINI_API_KEY=your-api-key-here \
  --set-env-vars CALENDAR_ID=your-calendar-id@group.calendar.google.com

# Option B: Via Secret Manager (more secure)
echo -n "your-api-key" | gcloud secrets create gemini-api-key --data-file=-
gcloud run deploy calhero \
  --image gcr.io/$PROJECT_ID/calhero \
  --set-env-vars USE_LLM=true \
  --update-secrets GEMINI_API_KEY=gemini-api-key:latest
```

**Key Point:** You DON'T bake the API key into the Docker image. Pass it at deployment time!

---

### Q2: Where do I specify token.json and credentials.json for Cloud Run?

**Answer:** Both ML and LLM versions need these files for Google Calendar API access. You have 3 options:

#### ✅ **Option 1: Service Account (Best for Production)**

No `credentials.json` or `token.json` needed!

```bash
# 1. Share your calendar with Cloud Run's service account
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format='value(projectNumber)')
SERVICE_ACCOUNT="$PROJECT_NUMBER-compute@developer.gserviceaccount.com"

# 2. Go to Google Calendar → Settings → Share with specific people
# Add: [SERVICE_ACCOUNT from above]
# Permission: "Make changes to events"

# 3. Deploy normally
gcloud run deploy calhero --source . --set-env-vars USE_LLM=false
```

**Note:** Requires small code change to use service account auth (see below).

#### ✅ **Option 2: Secret Manager (Works Out-of-Box!)**

Mount files as secrets:

```bash
# 1. Generate token.json locally first
python calhero_ml.py --dry-run  # Opens browser, creates token.json

# 2. Upload to Secret Manager
gcloud secrets create calendar-credentials --data-file=credentials.json
gcloud secrets create calendar-token --data-file=token.json

# 3. Grant access
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format='value(projectNumber)')
SERVICE_ACCOUNT="$PROJECT_NUMBER-compute@developer.gserviceaccount.com"

gcloud secrets add-iam-policy-binding calendar-credentials \
  --member="serviceAccount:$SERVICE_ACCOUNT" \
  --role="roles/secretmanager.secretAccessor"

gcloud secrets add-iam-policy-binding calendar-token \
  --member="serviceAccount:$SERVICE_ACCOUNT" \
  --role="roles/secretmanager.secretAccessor"

# 4. Deploy with secrets mounted as files
gcloud run deploy calhero \
  --image gcr.io/$PROJECT_ID/calhero \
  --set-secrets=/app/credentials.json=calendar-credentials:latest \
  --set-secrets=/app/token.json=calendar-token:latest \
  --set-env-vars USE_LLM=false,CALENDAR_ID=your-id@group.calendar.google.com
```

**This is the recommended approach!** No code changes needed. ✅

#### ⚠️ **Option 3: Bake into Docker Image (Not Recommended)**

```dockerfile
# In Dockerfile (insecure!)
COPY credentials.json /app/
COPY token.json /app/
```

**Security Risk:** Anyone with image access can extract credentials from layers.

---

### Q3: Don't I need credentials.json/token.json even for ML version to create calendar events?

**Answer:** YES! You're absolutely correct! 🎯

**Both ML and LLM versions need Google Calendar API credentials** to:
- Check for duplicate events
- Create calendar events

The difference between versions:

| Feature | ML Version | LLM Version |
|---------|------------|-------------|
| **Calendar API** | ✅ Required | ✅ Required |
| `credentials.json` | ✅ Required | ✅ Required |
| `token.json` | ✅ Required | ✅ Required |
| **Gemini API** | ❌ Not needed | ✅ Required |
| `GEMINI_API_KEY` | ❌ Not needed | ✅ Required |
| **OCR Engine** | Tesseract (built-in) | Gemini Vision |

---

## 🎯 Recommended Setup for Your Use Case

**ML Version with Docker Image on Cloud Run:**

### Complete Step-by-Step

```bash
# ============================================
# STEP 1: Local Setup (One-time)
# ============================================

# Generate token.json locally
python calhero_ml.py --dry-run

# ============================================
# STEP 2: Upload Credentials to Secret Manager
# ============================================

export PROJECT_ID=your-project-id
export PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format='value(projectNumber)')
export SERVICE_ACCOUNT="$PROJECT_NUMBER-compute@developer.gserviceaccount.com"

# Create secrets
gcloud secrets create calendar-credentials --data-file=credentials.json
gcloud secrets create calendar-token --data-file=token.json

# Grant access
gcloud secrets add-iam-policy-binding calendar-credentials \
  --member="serviceAccount:$SERVICE_ACCOUNT" \
  --role="roles/secretmanager.secretAccessor"

gcloud secrets add-iam-policy-binding calendar-token \
  --member="serviceAccount:$SERVICE_ACCOUNT" \
  --role="roles/secretmanager.secretAccessor"

# ============================================
# STEP 3: Build Docker Image
# ============================================

docker build -t gcr.io/$PROJECT_ID/calhero .
docker push gcr.io/$PROJECT_ID/calhero

# ============================================
# STEP 4: Deploy to Cloud Run
# ============================================

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
  --timeout 300s

# ============================================
# STEP 5: Test
# ============================================

export SERVICE_URL=$(gcloud run services describe calhero --region us-central1 --format='value(status.url)')
curl $SERVICE_URL/health
curl -X POST $SERVICE_URL -F "image=@screenshots/calendar_shifts.png" -F "dry_run=true"
```

---

## 📊 What Goes Where: Complete Reference

### Environment Variables

| Variable | Where to set | For ML? | For LLM? |
|----------|-------------|---------|----------|
| `USE_LLM` | `--set-env-vars` | ✅ (=false) | ✅ (=true) |
| `CALENDAR_ID` | `--set-env-vars` | ✅ Required | ✅ Required |
| `TIMEZONE` | `--set-env-vars` | ⚠️ Recommended | ⚠️ Recommended |
| `EVENT_PREFIX` | `--set-env-vars` | ⬜ Optional | ⬜ Optional |
| `GEMINI_API_KEY` | `--update-secrets` or `--set-env-vars` | ❌ Not needed | ✅ Required |

### Files/Credentials

| File | Where to set | For ML? | For LLM? |
|------|-------------|---------|----------|
| `credentials.json` | `--set-secrets` mount | ✅ Required | ✅ Required |
| `token.json` | `--set-secrets` mount | ✅ Required | ✅ Required |

### Docker Image Contents

| Item | Included in image? | Notes |
|------|-------------------|-------|
| Python code | ✅ Yes | `calhero_ml.py`, `calhero.py`, etc. |
| Dependencies | ✅ Yes | From `requirements*.txt` |
| Tesseract | ✅ Yes | Installed via apt-get |
| `credentials.json` | ❌ No | Mount via secrets |
| `token.json` | ❌ No | Mount via secrets |
| `.env` file | ❌ No | Use `--set-env-vars` |

---

## 🔄 Switching Between ML and LLM

```bash
# Switch to ML (no rebuild needed!)
gcloud run services update calhero \
  --set-env-vars USE_LLM=false \
  --region us-central1

# Switch to LLM (add API key if not already set)
gcloud run services update calhero \
  --set-env-vars USE_LLM=true \
  --update-secrets GEMINI_API_KEY=gemini-api-key:latest \
  --region us-central1

# Both versions use the SAME credentials.json and token.json!
```

---

## 🆚 Quick Comparison: Credential Approaches

| Approach | Complexity | Security | Code Changes | Best For |
|----------|------------|----------|--------------|----------|
| **Service Account** | 🟡 Medium | ✅ Excellent | Yes (small) | Production |
| **Secret Manager** | 🟢 Easy | ✅ Excellent | ❌ None | **Recommended!** |
| **Baked in Image** | 🟢 Easy | ⚠️ Poor | ❌ None | Dev/testing only |

**Our recommendation:** Use Secret Manager (Option 2) - works immediately, highly secure, no code changes!

---

## 🔒 Security Best Practices

### ✅ DO:
- Store credentials in Secret Manager
- Pass environment variables at deploy time
- Use service accounts for production
- Rotate secrets periodically
- Use `--update-secrets` for API keys

### ❌ DON'T:
- Commit credentials to git
- Bake secrets into Docker images
- Use hardcoded API keys in code
- Share credentials in plain text
- Include `.env` in Docker image

---

## 🐛 Troubleshooting

### "credentials.json not found" in Cloud Run

**Cause:** Secrets not mounted properly

**Fix:**
```bash
# Verify secrets exist
gcloud secrets list

# Verify IAM permissions
gcloud secrets get-iam-policy calendar-credentials

# Redeploy with correct mount path
gcloud run services update calhero \
  --set-secrets=/app/credentials.json=calendar-credentials:latest
```

### "Token expired" errors

**Cause:** `token.json` is old or invalid

**Fix:**
```bash
# Regenerate token locally
rm token.json
python calhero_ml.py --dry-run

# Update secret
gcloud secrets versions add calendar-token --data-file=token.json

# Cloud Run will use new version automatically
```

### "Calendar API has not been enabled"

**Cause:** Calendar API not enabled in project

**Fix:**
```bash
gcloud services enable calendar-json.googleapis.com --project=$PROJECT_ID
```

---

## 📚 Related Documentation

- **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** - Complete deployment guide (updated!)
- **[CREDENTIALS_GUIDE.md](CREDENTIALS_GUIDE.md)** - Getting Google credentials
- **[ENV_CONFIGURATION_GUIDE.md](ENV_CONFIGURATION_GUIDE.md)** - All environment variables
- **[OPTION3_DEPLOYMENT.md](OPTION3_DEPLOYMENT.md)** - Apps Script email trigger setup

---

## ✅ Quick Checklist

Before deploying to Cloud Run with Docker image:

- [ ] `credentials.json` obtained from Google Cloud Console
- [ ] `token.json` generated locally (run `python calhero_ml.py --dry-run`)
- [ ] Secrets created in Secret Manager (`calendar-credentials`, `calendar-token`)
- [ ] IAM permissions granted to Cloud Run service account
- [ ] Docker image built and pushed to gcr.io
- [ ] Environment variables ready (`USE_LLM`, `CALENDAR_ID`, etc.)
- [ ] For LLM: `GEMINI_API_KEY` ready in Secret Manager

During deploy:

- [ ] `--set-env-vars` for configuration
- [ ] `--set-secrets` for credentials files
- [ ] `--update-secrets` for API keys (LLM only)
- [ ] Test health endpoint after deploy
- [ ] Test with dry-run image upload

---

## 🎉 Summary

**Your Questions:**
1. ✅ Pass `GEMINI_API_KEY` via `--set-env-vars` or `--update-secrets` (not in image!)
2. ✅ Mount `credentials.json`/`token.json` via `--set-secrets` (Secret Manager)
3. ✅ YES! Both ML and LLM versions need Calendar API credentials

**Best Approach:**
- Build Docker image (no secrets inside)
- Store credentials in Secret Manager
- Mount as files via `--set-secrets`
- Pass config via `--set-env-vars`
- No code changes needed!

**One Command Deploy:**
```bash
gcloud run deploy calhero \
  --image gcr.io/$PROJECT_ID/calhero \
  --set-env-vars USE_LLM=false,CALENDAR_ID=your-id@group.calendar.google.com \
  --set-secrets=/app/credentials.json=calendar-credentials:latest \
  --set-secrets=/app/token.json=calendar-token:latest
```

Done! 🚀
