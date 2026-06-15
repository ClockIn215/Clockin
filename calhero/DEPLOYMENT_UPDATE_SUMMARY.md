# Deployment Guide Updates Summary

## What Was Updated

In response to your questions about:
1. How to pass `GEMINI_API_KEY` when `USE_LLM=true`
2. Where to specify `token.json` and `credentials.json` for Cloud Run
3. Clarification that BOTH versions need Calendar API credentials

---

## 📝 Files Updated

### 1. **DEPLOYMENT_GUIDE.md** - Major Updates

#### Added Critical Section: "Google Calendar Credentials for Cloud Run"

**Three approaches explained:**

**✅ Option 1: Service Account (Production)**
- No credentials.json/token.json needed
- Share calendar with Cloud Run service account
- Most secure for production

**✅ Option 2: Secret Manager (Recommended - Works Out-of-Box!)**
- Mount credentials as files via `--set-secrets`
- No code changes needed
- Highly secure

**⚠️ Option 3: Baked into Image**
- Not recommended (security risk)
- Credentials in image layers

#### Added Section: "For LLM Version: Adding GEMINI_API_KEY"

Shows how to pass Gemini API key via:
- Environment variables (`--set-env-vars`)
- Secret Manager (`--update-secrets`)

#### Added: "Complete End-to-End Deployment Example"

Full bash script showing:
- Local setup
- Secret Manager upload
- Docker build and push
- Cloud Run deployment
- Testing

For **both ML and LLM versions**

#### Added: "Summary: What Goes Where" Table

Complete reference showing where every item goes:
- Environment variables
- OAuth2 files
- Code/dependencies
- What to include in Docker vs. deploy time

### 2. **CLOUD_RUN_CREDENTIALS_GUIDE.md** - New File!

Complete guide directly answering your three questions:

**Q1: How to pass GEMINI_API_KEY?**
- Via `--set-env-vars` (simple)
- Via `--update-secrets` (secure)
- Code examples for both

**Q2: Where to specify credentials.json/token.json?**
- Three detailed options
- Complete commands
- Security comparison

**Q3: ML version needs credentials too?**
- YES! Confirmed
- Comparison table ML vs LLM
- Both need Calendar API access

**Plus:**
- Complete step-by-step for your use case
- Troubleshooting section
- Security best practices
- Quick checklist

### 3. **DEPLOYMENT_ML_SUMMARY.md** - Updated

Added clarification about credentials requirement for ML version.

---

## 🎯 Direct Answers to Your Questions

### Q1: How do I pass GEMINI_API_KEY when USE_LLM=true?

```bash
# Option A: Environment variable
gcloud run deploy calhero \
  --image gcr.io/$PROJECT_ID/calhero \
  --set-env-vars USE_LLM=true \
  --set-env-vars GEMINI_API_KEY=your-key-here

# Option B: Secret Manager (more secure)
gcloud run deploy calhero \
  --image gcr.io/$PROJECT_ID/calhero \
  --set-env-vars USE_LLM=true \
  --update-secrets GEMINI_API_KEY=gemini-api-key:latest
```

### Q2: Where do I specify token.json and credentials.json?

**Best approach: Mount via Secret Manager**

```bash
# 1. Upload to Secret Manager
gcloud secrets create calendar-credentials --data-file=credentials.json
gcloud secrets create calendar-token --data-file=token.json

# 2. Deploy with secrets mounted as files
gcloud run deploy calhero \
  --image gcr.io/$PROJECT_ID/calhero \
  --set-secrets=/app/credentials.json=calendar-credentials:latest \
  --set-secrets=/app/token.json=calendar-token:latest
```

### Q3: Don't I need those files even for ML version?

**YES! You're absolutely correct!** 🎯

Both ML and LLM versions need `credentials.json` and `token.json` for Google Calendar API access.

**The only difference:**
- ML version: Doesn't need `GEMINI_API_KEY`
- LLM version: Also needs `GEMINI_API_KEY`

**But both need Calendar credentials to create events!**

---

## 🚀 Your Recommended Deployment

For **ML version** with **Docker image** on **Cloud Run**:

```bash
# ============================================
# ONE-TIME SETUP
# ============================================

# 1. Generate token.json locally
python calhero_ml.py --dry-run

# 2. Set variables
export PROJECT_ID=your-project-id
export PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format='value(projectNumber)')
export SERVICE_ACCOUNT="$PROJECT_NUMBER-compute@developer.gserviceaccount.com"

# 3. Upload credentials
gcloud secrets create calendar-credentials --data-file=credentials.json
gcloud secrets create calendar-token --data-file=token.json

# 4. Grant access
gcloud secrets add-iam-policy-binding calendar-credentials \
  --member="serviceAccount:$SERVICE_ACCOUNT" \
  --role="roles/secretmanager.secretAccessor"

gcloud secrets add-iam-policy-binding calendar-token \
  --member="serviceAccount:$SERVICE_ACCOUNT" \
  --role="roles/secretmanager.secretAccessor"

# ============================================
# BUILD AND DEPLOY
# ============================================

# 5. Build Docker image
docker build -t gcr.io/$PROJECT_ID/calhero .
docker push gcr.io/$PROJECT_ID/calhero

# 6. Deploy to Cloud Run
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

# 7. Test
SERVICE_URL=$(gcloud run services describe calhero --region us-central1 --format='value(status.url)')
curl $SERVICE_URL/health
```

---

## 📊 What Goes Where: Complete Reference

| Item | Local Dev | Docker Image | Cloud Run Deploy |
|------|-----------|--------------|------------------|
| **Environment Variables** |||
| `USE_LLM` | .env | ❌ No | ✅ `--set-env-vars` |
| `CALENDAR_ID` | .env | ❌ No | ✅ `--set-env-vars` |
| `TIMEZONE` | .env | ❌ No | ✅ `--set-env-vars` |
| `GEMINI_API_KEY` (LLM) | .env | ❌ No | ✅ `--update-secrets` |
| **Credentials (BOTH ML & LLM)** |||
| `credentials.json` | ✅ Local file | ❌ No | ✅ `--set-secrets` mount |
| `token.json` | ✅ Auto-generated | ❌ No | ✅ `--set-secrets` mount |
| **Code** |||
| `calhero_ml.py` | ✅ | ✅ | - |
| `requirements_ml.txt` | ✅ | ✅ | - |
| Tesseract | System install | ✅ apt-get | - |

**Key Principle:** 
- ✅ **DO** build generic Docker image
- ✅ **DO** pass secrets at deploy time
- ❌ **DON'T** bake secrets into image

---

## 🔄 Easy Configuration Changes

```bash
# Switch between test/prod calendars (no rebuild!)
gcloud run services update calhero \
  --set-env-vars CALENDAR_ID=test-calendar@group.calendar.google.com

# Switch to LLM version (no rebuild!)
gcloud run services update calhero \
  --set-env-vars USE_LLM=true \
  --update-secrets GEMINI_API_KEY=gemini-api-key:latest

# Update credentials (if they expire)
gcloud secrets versions add calendar-token --data-file=token.json
# Cloud Run uses new version automatically
```

---

## 📚 Where to Find More Information

| Topic | Document | Section |
|-------|----------|---------|
| Complete deployment steps | **DEPLOYMENT_GUIDE.md** | "Quick Start - Email to Calendar" |
| Credentials handling | **CLOUD_RUN_CREDENTIALS_GUIDE.md** | "Your Questions Answered" |
| Apps Script setup | **OPTION3_DEPLOYMENT.md** | Complete guide |
| Environment variables | **ENV_CONFIGURATION_GUIDE.md** | All variables explained |
| Getting credentials | **CREDENTIALS_GUIDE.md** | OAuth2 setup |

---

## ✅ Key Takeaways

1. **GEMINI_API_KEY**: Pass via `--set-env-vars` or `--update-secrets` (not in image)

2. **credentials.json/token.json**: Mount via `--set-secrets` from Secret Manager

3. **Both ML and LLM need Calendar credentials**: The only difference is Gemini API key

4. **Build once, configure at deploy**: Generic Docker image + runtime configuration

5. **No code changes needed**: Secret Manager approach works out-of-box

6. **Easy updates**: Change config without rebuilding

---

## 🎉 You're All Set!

The deployment guide now has complete instructions for:
- ✅ Passing GEMINI_API_KEY for LLM version
- ✅ Mounting credentials.json/token.json via Secret Manager
- ✅ Clear explanation that BOTH versions need Calendar credentials
- ✅ Complete end-to-end deployment example
- ✅ Security best practices
- ✅ Troubleshooting guide

**Start here:** [CLOUD_RUN_CREDENTIALS_GUIDE.md](CLOUD_RUN_CREDENTIALS_GUIDE.md)

Then follow the complete deployment in: [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
