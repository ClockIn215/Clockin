# Deployment Guide - Cloud & Docker

This guide covers deploying the calendar parser as a cloud function or Docker container with email triggers.

## 🎯 Quick Navigation

| If you want... | Go to section | Best approach |
|---------------|---------------|---------------|
| **Email → Calendar (fastest!)** | [Quick Start](#-quick-start---email-to-calendar-ml-version) | Apps Script + Cloud Run |
| **ML version config** | [Quick Start](#-quick-start---email-to-calendar-ml-version) | Runtime env vars |
| **Docker setup** | [Docker Deployment](#-docker-deployment) | Build + deploy |
| **All env variables** | [Quick Start](#required-configuration-for-ml-version) | See table |
| **Test vs Prod calendars** | [Configuration Management](#-configuration-management) | Secret Manager |

## 📋 Required for ML Version

| Item | How to get it | Required? |
|------|---------------|-----------|
| `CALENDAR_ID` | Google Calendar settings → Integrate calendar | ✅ Required |
| `credentials.json` | [Google Cloud Console](https://console.cloud.google.com) | ✅ Required |
| `token.json` | Auto-generated after first auth | ✅ Auto-created |
| `USE_LLM=false` | Set environment variable | ✅ Required |
| `TIMEZONE` | Your timezone (e.g., `America/Chicago`) | ⚠️ Recommended |
| `GEMINI_API_KEY` | N/A for ML version | ❌ Not needed |

---

## 📋 Table of Contents

1. [Quick Start - Email to Calendar (ML Version)](#-quick-start---email-to-calendar-ml-version)
2. [Docker Deployment](#-docker-deployment)
3. [Google Cloud Functions](#-google-cloud-functions)
4. [Email Triggers](#-email-triggers)
5. [Alternative OCR Libraries](#-alternative-ocr-libraries)
6. [Production Considerations](#-production-considerations)

---

## 🐳 Docker Deployment

### Option 1: Full Image (LLM + ML/OCR)

Includes Tesseract OCR (adds ~150MB to image).

**Build:**
```bash
docker build -t calhero .
```

**Run locally (ML version):**
```bash
# Option 1: With environment variables (recommended)
docker run -it \
  -v $(pwd)/screenshots:/app/screenshots \
  -v $(pwd)/credentials.json:/app/credentials.json \
  -v $(pwd)/token.json:/app/token.json \
  -e USE_LLM=false \
  -e CALENDAR_ID=your-calendar-id@group.calendar.google.com \
  -e TIMEZONE=America/Chicago \
  calhero

# Option 2: With .env file
docker run -it \
  --env-file .env \
  -v $(pwd)/screenshots:/app/screenshots \
  -v $(pwd)/credentials.json:/app/credentials.json \
  -v $(pwd)/token.json:/app/token.json \
  calhero
```

**Run locally (LLM version):**
```bash
docker run -it \
  -v $(pwd)/screenshots:/app/screenshots \
  -v $(pwd)/credentials.json:/app/credentials.json \
  -v $(pwd)/token.json:/app/token.json \
  -e USE_LLM=true \
  -e GEMINI_API_KEY=your-api-key \
  -e CALENDAR_ID=your-calendar-id@group.calendar.google.com \
  calhero
```

**Image size:** ~800MB (Python + OpenCV + Tesseract)

### Option 2: Slim Image (LLM only)

No Tesseract, smaller and faster.

**Build:**
```bash
docker build -f Dockerfile.slim -t calhero-llm .
```

**Run:**
```bash
docker run -it \
  -v $(pwd)/screenshots:/app/screenshots \
  -v $(pwd)/credentials.json:/app/credentials.json \
  -e GEMINI_API_KEY="your_api_key" \
  calhero-llm
```

**Image size:** ~600MB (Python + minimal deps)

### Docker Compose Setup

Create `docker-compose.yml`:

**For ML Version (no API key needed):**
```yaml
version: '3.8'

services:
  calhero-ml:
    build: .
    volumes:
      - ./screenshots:/app/screenshots
      - ./credentials.json:/app/credentials.json:ro
      - ./token.json:/app/token.json
    environment:
      - USE_LLM=false
      - CALENDAR_ID=${CALENDAR_ID}
      - TIMEZONE=America/Chicago
      - EVENT_PREFIX=MyPrefix 
    restart: unless-stopped
    # Optional: Run as cron job
    command: |
      sh -c "while true; do 
        python calhero_ml.py
        sleep 3600
      done"
```

**For LLM Version:**
```yaml
version: '3.8'

services:
  calhero-llm:
    build: .
    volumes:
      - ./screenshots:/app/screenshots
      - ./credentials.json:/app/credentials.json:ro
      - ./token.json:/app/token.json
    environment:
      - USE_LLM=true
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - CALENDAR_ID=${CALENDAR_ID}
      - TIMEZONE=America/Chicago
    restart: unless-stopped
```

**Run:**
```bash
# Create .env file with your values first
echo "CALENDAR_ID=your-calendar-id@group.calendar.google.com" > .env
echo "GEMINI_API_KEY=your-key-if-using-llm" >> .env

# Start service
docker-compose up -d

# View logs
docker-compose logs -f
```

### Tesseract in Docker

Tesseract is **absolutely viable** for Docker! Here's why:

✅ **Pros:**
- Lightweight (adds ~150MB)
- Fast and battle-tested
- Easy to install via apt-get
- Works well in containers

❌ **Cons:**
- Requires system binary (not pure Python)
- Need to install language data files

**Installation in Dockerfile:**
```dockerfile
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libtesseract-dev \
    && rm -rf /var/lib/apt/lists/*
```

That's it! Very straightforward.

---

## ☁️ Google Cloud Functions

### Setup Steps

**1. Install Cloud SDK:**
```bash
# macOS
brew install google-cloud-sdk

# Or download from: https://cloud.google.com/sdk/docs/install
```

**2. Authenticate:**
```bash
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
```

**3. Deploy HTTP Function:**
```bash
gcloud functions deploy parse_calendar_screenshot \
  --gen2 \
  --runtime python311 \
  --trigger-http \
  --allow-unauthenticated \
  --entry-point parse_calendar_screenshot \
  --source . \
  --memory 1GB \
  --timeout 300s \
  --set-env-vars GEMINI_API_KEY=your_api_key
```

**4. Test:**
```bash
# Get function URL
FUNCTION_URL=$(gcloud functions describe parse_calendar_screenshot --format='value(url)')

# Test with curl
curl -X POST $FUNCTION_URL \
  -H "Content-Type: multipart/form-data" \
  -F "image=@screenshots/schedule.png" \
  -F "use_llm=false"
```

### Cloud Function with Tesseract

**Good news:** Cloud Functions support custom dependencies!

Create `requirements.txt`:
```txt
# Your requirements_cloud.txt content
pytesseract>=0.3.10
opencv-python-headless>=4.8.0
...
```

Tesseract binary is **automatically available** in Cloud Functions Gen2 runtime! 🎉

If not, use Cloud Run instead (supports Docker):

```bash
# Build and push to Container Registry
docker build -t gcr.io/YOUR_PROJECT/calhero .
docker push gcr.io/YOUR_PROJECT/calhero

# Deploy to Cloud Run
gcloud run deploy calhero \
  --image gcr.io/YOUR_PROJECT/calhero \
  --platform managed \
  --allow-unauthenticated \
  --memory 1Gi \
  --timeout 300
```

---

## 📧 Email Triggers

### Option 1: Gmail API + Cloud Pub/Sub (Recommended)

**Setup:**

1. **Enable Gmail API:**
   ```bash
   gcloud services enable gmail.googleapis.com
   ```

2. **Create Pub/Sub Topic:**
   ```bash
   gcloud pubsub topics create gmail-calendar-screenshots
   ```

3. **Set up Gmail Push Notifications:**
   ```python
   from googleapiclient.discovery import build
   
   service = build('gmail', 'v1', credentials=creds)
   
   request = {
       'labelIds': ['INBOX'],
       'topicName': 'projects/YOUR_PROJECT/topics/gmail-calendar-screenshots'
   }
   
   service.users().watch(userId='me', body=request).execute()
   ```

4. **Deploy Pub/Sub-triggered function:**
   ```bash
   gcloud functions deploy gmail_calendar_processor \
     --gen2 \
     --runtime python311 \
     --trigger-topic gmail-calendar-screenshots \
     --entry-point gmail_pubsub_trigger \
     --memory 1GB
   ```

**How it works:**
```
Shift worker emails → Gmail API → Pub/Sub → Cloud Function → Parse → Calendar
```

### Option 2: SendGrid Inbound Parse

**Setup:**

1. **Configure SendGrid:**
   - Add domain: `calendar.yourdomain.com`
   - Set webhook URL to your Cloud Function
   - Forward: `schedule@calendar.yourdomain.com`

2. **Shift worker emails to:** `schedule@calendar.yourdomain.com`

3. **SendGrid POSTs to your function** with attachment

**Pros:** Simple, reliable, free tier available

### Option 3: Mailgun Routes

Similar to SendGrid but with Mailgun:

```python
# Mailgun forwards email to Cloud Function
@app.route('/mailgun-webhook', methods=['POST'])
def mailgun_handler():
    # Extract attachment from request
    attachment = request.files.get('attachment-1')
    # Process...
```

### Option 4: Gmail Filter + Google Apps Script

Lightweight option without Cloud Functions:

1. **Create Gmail filter:**
   - From: sender@example.com
   - Subject contains: "schedule"
   - Has attachment
   - Forward to Apps Script webhook

2. **Apps Script calls your API**

---

## 🔄 Alternative OCR Libraries (Pure Python)

If you want **no binary dependencies**, here are alternatives:

### Option 1: EasyOCR (Recommended)

Pure Python, uses PyTorch deep learning models.

**Pros:**
- ✅ No system dependencies
- ✅ Very accurate (better than Tesseract for some cases)
- ✅ Supports 80+ languages
- ✅ GPU support

**Cons:**
- ❌ Much larger (downloads ~500MB models)
- ❌ Slower on CPU (~2-3x slower than Tesseract)
- ❌ Higher memory usage (needs ~1.5GB RAM)

**Installation:**
```bash
pip install easyocr
```

**Usage:**
```python
import easyocr

# Create reader (downloads model on first run)
reader = easyocr.Reader(['en'])

# Extract text
result = reader.readtext('image.png', detail=0)
text = ' '.join(result)
```

**Update `calhero_ml.py`:**
```python
def extract_text_from_image_easyocr(image_path: Path) -> str:
    """Alternative OCR using EasyOCR (pure Python)."""
    import easyocr
    
    # Initialize reader (cache this in production!)
    reader = easyocr.Reader(['en'], gpu=False)
    
    # Extract text
    results = reader.readtext(str(image_path), detail=0)
    text = '\n'.join(results)
    
    return text
```

### Option 2: PaddleOCR

Another pure Python option, very fast.

**Installation:**
```bash
pip install paddleocr
```

**Usage:**
```python
from paddleocr import PaddleOCR

ocr = PaddleOCR(use_angle_cls=True, lang='en')
result = ocr.ocr(str(image_path), cls=True)
```

### Option 3: Google Cloud Vision API

Cloud-based, most accurate but costs money.

**Pros:**
- ✅ Highest accuracy
- ✅ No local dependencies
- ✅ Handles any image quality

**Cons:**
- ❌ Costs $1.50 per 1000 images
- ❌ Requires internet
- ❌ Another API to manage

**Usage:**
```python
from google.cloud import vision

client = vision.ImageAnnotatorClient()

with open(image_path, 'rb') as f:
    content = f.read()

image = vision.Image(content=content)
response = client.text_detection(image=image)
text = response.text_annotations[0].description
```

### Comparison Table

| Library | Binary Deps | Size | Speed | Accuracy | Cost |
|---------|-------------|------|-------|----------|------|
| **Tesseract** | ⚠️ Yes | 150MB | Fast (1x) | Good (85-95%) | Free |
| **EasyOCR** | ✅ No | 500MB | Slow (3x) | Excellent (90-98%) | Free |
| **PaddleOCR** | ✅ No | 400MB | Medium (2x) | Very Good (88-96%) | Free |
| **Cloud Vision** | ✅ No | 0MB | Fast | Excellent (95-99%) | $1.50/1k |

### Recommendation

**For Docker/Cloud Run:**
- Use **Tesseract** - it's lightweight and fast

**For Cloud Functions (if Tesseract not available):**
- Use **EasyOCR** - pure Python, very accurate

**For serverless with cold starts:**
- Use **Gemini LLM** - no OCR needed, ~1s startup

---

## 🏗️ Production Considerations

### Architecture Options

#### Option A: Cloud Run + Email Trigger
```
Email → Cloud Scheduler → Cloud Run Service → Calendar
```
- ✅ Full Docker control
- ✅ Can use any library
- ✅ Auto-scaling
- 💰 Pay per request

#### Option B: Cloud Functions + Pub/Sub
```
Gmail → Pub/Sub → Cloud Function → Calendar
```
- ✅ Simplest setup
- ✅ Real-time processing
- ✅ Free tier generous
- ⚠️ May have cold starts

#### Option C: Hybrid (Recommended)
```
Email → Cloud Function (filter) → Cloud Run (process) → Calendar
```
- ✅ Fast initial response
- ✅ Heavy processing in Cloud Run
- ✅ Best of both worlds

### Cost Estimates

**Scenario:** 50 schedules/month

| Option | Cost/Month |
|--------|------------|
| Cloud Functions + Tesseract | $0 (free tier) |
| Cloud Run + Tesseract | $0-2 |
| Cloud Functions + Gemini | ~$0.05 |
| Cloud Vision API | ~$0.08 |

### Security

**Protect your credentials:**

1. **Use Secret Manager:**
   ```bash
   gcloud secrets create gemini-api-key --data-file=-
   # Paste key, press Ctrl+D
   
   gcloud functions deploy ... \
     --set-secrets="GEMINI_API_KEY=gemini-api-key:latest"
   ```

2. **Use IAM for Calendar:**
   - Create service account
   - Grant Calendar API access
   - Use service account in function

3. **Validate email sender:**
   ```python
   if sender != "sender@example.com":
       return "Unauthorized", 403
   ```

### Monitoring

**Set up logging:**
```python
import logging
from google.cloud import logging as cloud_logging

# Setup
cloud_logging_client = cloud_logging.Client()
cloud_logging_client.setup_logging()

# Use
logging.info(f"Processed {filename}: {created_count} shifts")
```

**Create alerts:**
```bash
gcloud monitoring policies create \
  --notification-channels=$CHANNEL_ID \
  --display-name="Calendar Parse Failures" \
  --condition-filter='resource.type="cloud_function"
    AND severity="ERROR"'
```

---

## 🚀 Quick Start - Email to Calendar (ML Version)

**Fastest path to production with ML parser (free, no API keys!):**

### 📋 Required Configuration for ML Version

**Environment Variables:**

| Variable | Required? | Purpose | Example |
|----------|-----------|---------|---------|
| `USE_LLM` | ✅ Yes | Select parser type | `false` (for ML) |
| `CALENDAR_ID` | ✅ Yes | Target calendar | `abc123...@group.calendar.google.com` |
| `TIMEZONE` | ⚠️ Recommended | Event timezone | `America/Chicago` |
| `EVENT_PREFIX` | ⚠️ Optional | Prefix for events | `MyPrefix ` |
| `TEST_CALENDAR_ID` | ⬜ Optional | Test calendar | `xyz789...@group.calendar.google.com` |

**Google Calendar API Authentication (BOTH ML and LLM need this!):**
- `credentials.json` - OAuth2 client credentials
- `token.json` - User access token (auto-generated)

**Additional for LLM Version Only:**
- `GEMINI_API_KEY` - Gemini API key for image parsing

**What You DON'T Need for ML Version:**
- ❌ `GEMINI_API_KEY` - Only needed for LLM version
- ❌ EasyOCR dependencies - Tesseract is included

---

### ⚠️ Important: Google Calendar Credentials for Cloud Run

**You're absolutely right!** Both ML and LLM versions need Google Calendar API access to create events.

For **Cloud Run deployment**, you have **three options** for handling credentials:

#### **Option 1: Service Account (✅ Recommended for Production)**

Use Cloud Run's built-in service account - **no `credentials.json` or `token.json` needed!**

```bash
# Step 1: Get your Cloud Run service account
PROJECT_ID=your-project-id
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format='value(projectNumber)')
SERVICE_ACCOUNT="$PROJECT_NUMBER-compute@developer.gserviceaccount.com"

# Step 2: Share your Google Calendar with the service account
# Go to Google Calendar → Settings → Share with specific people
# Add: [SERVICE_ACCOUNT email from above]
# Permission: "Make changes to events"

# Step 3: Update calendar_utils.py to use service account (see below)
# OR: Deploy with service account credentials automatically available

# Step 4: Deploy normally - no credentials.json needed!
gcloud run deploy calhero \
  --source . \
  --set-env-vars USE_LLM=false \
  --set-env-vars CALENDAR_ID=your-calendar-id@group.calendar.google.com \
  --allow-unauthenticated
```

**Note:** This requires a small code change to use service account auth instead of OAuth2 flow. See "Service Account Setup" section below.

#### **Option 2: Mount Credentials via Secret Manager (✅ Works Out-of-Box)**

Store `credentials.json` and `token.json` as secrets:

```bash
# Step 1: Create token.json locally first
# Run locally once to generate token.json:
python calhero_ml.py --dry-run  # This will create token.json

# Step 2: Upload credentials to Secret Manager
gcloud secrets create calendar-credentials \
  --data-file=credentials.json

gcloud secrets create calendar-token \
  --data-file=token.json

# Step 3: Grant Cloud Run access
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format='value(projectNumber)')
gcloud secrets add-iam-policy-binding calendar-credentials \
  --member="serviceAccount:$PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

gcloud secrets add-iam-policy-binding calendar-token \
  --member="serviceAccount:$PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

# Step 4: Mount secrets as files in Cloud Run
gcloud run deploy calhero \
  --source . \
  --set-env-vars USE_LLM=false \
  --set-env-vars CALENDAR_ID=your-calendar-id@group.calendar.google.com \
  --set-secrets=/app/credentials.json=calendar-credentials:latest \
  --set-secrets=/app/token.json=calendar-token:latest \
  --allow-unauthenticated
```

**This approach works immediately with no code changes!** ✅

#### **Option 3: Bake into Docker Image (⚠️ Not Recommended)**

```bash
# Build image with credentials (less secure!)
docker build -t gcr.io/$PROJECT_ID/calhero .
docker push gcr.io/$PROJECT_ID/calhero

# Deploy
gcloud run deploy calhero \
  --image gcr.io/$PROJECT_ID/calhero \
  --set-env-vars USE_LLM=false,CALENDAR_ID=your-calendar-id@group.calendar.google.com
```

**⚠️ Security Risk:** Credentials are in image layers (anyone with image access can extract them)

---

### 🔑 For LLM Version: Adding GEMINI_API_KEY

If you're using `USE_LLM=true`, add the Gemini API key the same way:

#### Via Environment Variable (Recommended):
```bash
gcloud run deploy calhero \
  --image gcr.io/$PROJECT_ID/calhero \
  --set-env-vars USE_LLM=true \
  --set-env-vars GEMINI_API_KEY=your-gemini-api-key \
  --set-env-vars CALENDAR_ID=your-calendar-id@group.calendar.google.com \
  --set-secrets=/app/credentials.json=calendar-credentials:latest \
  --set-secrets=/app/token.json=calendar-token:latest
```

#### Via Secret Manager (More Secure):
```bash
# Create secret
echo -n "your-gemini-api-key" | gcloud secrets create gemini-api-key --data-file=-

# Grant access
gcloud secrets add-iam-policy-binding gemini-api-key \
  --member="serviceAccount:$PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

# Deploy with secret
gcloud run deploy calhero \
  --source . \
  --set-env-vars USE_LLM=true \
  --update-secrets GEMINI_API_KEY=gemini-api-key:latest \
  --set-secrets=/app/credentials.json=calendar-credentials:latest \
  --set-secrets=/app/token.json=calendar-token:latest
```

---

### 🎯 Deployment Approaches

You have **two main approaches** for passing configuration:

#### **Approach 1: Runtime Environment Variables (Recommended)**

✅ **Pros:**
- Change configuration without rebuilding
- Switch between test/prod calendars easily
- Secure (no secrets in image)
- Can use Google Secret Manager

```bash
# Step 1: Build generic Docker image (no secrets)
docker build -t gcr.io/$PROJECT_ID/calhero .
docker push gcr.io/$PROJECT_ID/calhero

# Step 2: Deploy with environment variables
gcloud run deploy calhero \
  --image gcr.io/$PROJECT_ID/calhero \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars USE_LLM=false \
  --set-env-vars CALENDAR_ID=your-calendar-id@group.calendar.google.com \
  --set-env-vars TIMEZONE=America/Chicago \
  --set-env-vars EVENT_PREFIX="MyPrefix " \
  --memory 1Gi \
  --timeout 300s \
  --min-instances 0 \
  --max-instances 3

# Step 3: Change configuration anytime without rebuild
gcloud run services update calhero \
  --set-env-vars CALENDAR_ID=different-calendar@group.calendar.google.com
```

#### **Approach 2: Baked-In Configuration**

⚠️ **Pros:**
- Simpler deployment command
- Configuration travels with image

❌ **Cons:**
- Need to rebuild to change config
- Secrets stored in image (less secure)
- Can't easily switch calendars

```bash
# Step 1: Create .env file in project root
cat > .env << EOF
USE_LLM=false
CALENDAR_ID=your-calendar-id@group.calendar.google.com
TIMEZONE=America/Chicago
EVENT_PREFIX=MyPrefix 
EOF

# Step 2: Build with build args (if Dockerfile supports it)
# OR: Copy .env into image
docker build -t gcr.io/$PROJECT_ID/calhero .
docker push gcr.io/$PROJECT_ID/calhero

# Step 3: Deploy (config already in image)
gcloud run deploy calhero \
  --image gcr.io/$PROJECT_ID/calhero \
  --allow-unauthenticated \
  --memory 1Gi
```

**⚠️ Security Note:** For baked-in approach, ensure `.env` is in your `.dockerignore` if using Secret Manager instead.

---

### 📱 Complete Apps Script Deployment (Recommended)

This uses **Approach 1** for maximum flexibility:

**1. Deploy to Cloud Run with ML parser:**
```bash
# Get your calendar ID from Google Calendar settings
# Share calendar → "Integrate calendar" → copy Calendar ID

gcloud run deploy calhero \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars USE_LLM=false,CALENDAR_ID=your-calendar-id@group.calendar.google.com,TIMEZONE=America/Chicago \
  --memory 1Gi \
  --timeout 300s \
  --min-instances 0
```

**2. Get the service URL:**
```bash
SERVICE_URL=$(gcloud run services describe calhero \
  --platform managed \
  --region us-central1 \
  --format 'value(status.url)')

echo "Your Cloud Run URL: $SERVICE_URL"
# Copy this URL - you'll need it for Apps Script!
```

**3. Set up Gmail + Apps Script forwarding:**

📖 **See complete step-by-step guide:** [OPTION3_DEPLOYMENT.md](OPTION3_DEPLOYMENT.md)

**Quick summary:**
- Create Gmail filter (from shift worker's email, has attachment)
- Apps Script checks email every 5 minutes
- Extracts screenshot, sends to Cloud Run
- Cloud Run parses and adds to calendar
- Apps Script marks email as processed

**4. Done!** Shift worker emails schedule → Gmail → Apps Script → Cloud Run → Calendar ✅

---

### 🧪 Testing Your Deployment

```bash
# Test health endpoint
curl $SERVICE_URL/health

# Expected response:
# {"status":"healthy","parser":"ml","version":"1.0.0"}

# Test with dry-run (no calendar events created)
curl -X POST $SERVICE_URL \
  -F "image=@screenshots/processed/schedule.png" \
  -F "dry_run=true"

# Expected: JSON with detected shifts but no events created

# Test actual event creation
curl -X POST $SERVICE_URL \
  -F "image=@screenshots/processed/schedule.png"

# Check your Google Calendar - events should appear!

# Test with calendar override (uses different calendar)
curl -X POST "$SERVICE_URL?calendar_id=different-calendar@group.calendar.google.com" \
  -F "image=@screenshots/processed/schedule.png"
```

---

### 🔧 Configuration Management

#### Using Google Secret Manager (Production Recommended)

```bash
# Step 1: Create secrets
echo -n "your-calendar-id@group.calendar.google.com" | \
  gcloud secrets create calendar-id --data-file=-

# Step 2: Grant Cloud Run access
gcloud secrets add-iam-policy-binding calendar-id \
  --member="serviceAccount:PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

# Step 3: Deploy with secrets
gcloud run deploy calhero \
  --source . \
  --update-secrets CALENDAR_ID=calendar-id:latest \
  --set-env-vars USE_LLM=false,TIMEZONE=America/Chicago
```

#### Switching Between Test and Production

**Option A: Update Cloud Run (Affects All Requests)**

```bash
# Use test calendar
gcloud run services update calhero \
  --set-env-vars CALENDAR_ID=test-calendar@group.calendar.google.com

# Switch back to production
gcloud run services update calhero \
  --set-env-vars CALENDAR_ID=prod-calendar@group.calendar.google.com

# No rebuild needed! ✨
```

**Option B: Override in Apps Script (Recommended!)**

No Cloud Run changes needed! Just edit your Apps Script:

```javascript
// In gmail_apps_script.js
const CALENDAR_ID_OVERRIDE = 'test-calendar@group.calendar.google.com';

// To switch back to production:
const CALENDAR_ID_OVERRIDE = '';  // Uses Cloud Run default
```

**Benefits:**
- ✅ Instant changes (just save Apps Script)
- ✅ No `gcloud` commands needed
- ✅ Different calendars per user/script
- ✅ Zero downtime

📖 **See:** [CALENDAR_OVERRIDE_GUIDE.md](CALENDAR_OVERRIDE_GUIDE.md) for complete guide

---

---

### 🎯 Complete End-to-End Deployment Example

Here's the **complete deployment** using Option 2 (Secret Manager for credentials):

#### For ML Version (Recommended):

```bash
# ============================================
# STEP 1: Local Setup (One-time)
# ============================================

# Install dependencies
pip install -r requirements_ml.txt

# Run once locally to generate token.json
# This will open browser for Google auth
python calhero_ml.py --dry-run

# Verify you now have both files:
ls credentials.json token.json

# ============================================
# STEP 2: Set Variables
# ============================================

export PROJECT_ID=your-project-id
export REGION=us-central1
export CALENDAR_ID=your-calendar-id@group.calendar.google.com

# Get project number
export PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format='value(projectNumber)')
export SERVICE_ACCOUNT="$PROJECT_NUMBER-compute@developer.gserviceaccount.com"

# ============================================
# STEP 3: Upload Credentials to Secret Manager
# ============================================

# Create secrets
gcloud secrets create calendar-credentials --data-file=credentials.json
gcloud secrets create calendar-token --data-file=token.json

# Grant Cloud Run access
gcloud secrets add-iam-policy-binding calendar-credentials \
  --member="serviceAccount:$SERVICE_ACCOUNT" \
  --role="roles/secretmanager.secretAccessor"

gcloud secrets add-iam-policy-binding calendar-token \
  --member="serviceAccount:$SERVICE_ACCOUNT" \
  --role="roles/secretmanager.secretAccessor"

# ============================================
# STEP 4: Build and Push Docker Image
# ============================================

# Build
docker build -t gcr.io/$PROJECT_ID/calhero .

# Push to Google Container Registry
docker push gcr.io/$PROJECT_ID/calhero

# ============================================
# STEP 5: Deploy to Cloud Run
# ============================================

gcloud run deploy calhero \
  --image gcr.io/$PROJECT_ID/calhero \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --set-env-vars USE_LLM=false \
  --set-env-vars CALENDAR_ID=$CALENDAR_ID \
  --set-env-vars TIMEZONE=America/Chicago \
  --set-env-vars EVENT_PREFIX="MyPrefix " \
  --set-secrets=/app/credentials.json=calendar-credentials:latest \
  --set-secrets=/app/token.json=calendar-token:latest \
  --memory 1Gi \
  --timeout 300s \
  --min-instances 0 \
  --max-instances 3

# ============================================
# STEP 6: Get Service URL and Test
# ============================================

export SERVICE_URL=$(gcloud run services describe calhero \
  --region $REGION \
  --format='value(status.url)')

echo "Service URL: $SERVICE_URL"

# Test health
curl $SERVICE_URL/health

# Test with image
curl -X POST $SERVICE_URL \
  -F "image=@screenshots/processed/calendar_shifts.png" \
  -F "dry_run=true"
```

#### For LLM Version:

Add Gemini API key to the deployment:

```bash
# Upload Gemini API key
echo -n "your-gemini-api-key-here" | \
  gcloud secrets create gemini-api-key --data-file=-

# Grant access
gcloud secrets add-iam-policy-binding gemini-api-key \
  --member="serviceAccount:$SERVICE_ACCOUNT" \
  --role="roles/secretmanager.secretAccessor"

# Deploy with LLM enabled
gcloud run deploy calhero \
  --image gcr.io/$PROJECT_ID/calhero \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --set-env-vars USE_LLM=true \
  --set-env-vars CALENDAR_ID=$CALENDAR_ID \
  --set-env-vars TIMEZONE=America/Chicago \
  --update-secrets GEMINI_API_KEY=gemini-api-key:latest \
  --set-secrets=/app/credentials.json=calendar-credentials:latest \
  --set-secrets=/app/token.json=calendar-token:latest \
  --memory 1Gi
```

---

### 📋 Summary: What Goes Where

| Item | Local Dev | Docker Build | Cloud Run Deploy | Purpose |
|------|-----------|--------------|------------------|---------|
| **Environment Variables** |||
| `USE_LLM` | .env file | - | `--set-env-vars` | Select parser |
| `CALENDAR_ID` | .env file | - | `--set-env-vars` | Target calendar |
| `TIMEZONE` | .env file | - | `--set-env-vars` | Event timezone |
| `GEMINI_API_KEY` (LLM only) | .env file | - | `--update-secrets` or `--set-env-vars` | Gemini API |
| **OAuth2 Files** |||
| `credentials.json` | Local file | ❌ Don't include | `--set-secrets` mount | Calendar OAuth2 |
| `token.json` | Auto-generated | ❌ Don't include | `--set-secrets` mount | Access token |
| **Code/Dependencies** |||
| `calhero_ml.py` | ✅ | ✅ Included | - | ML parser |
| `calhero.py` | ✅ | ✅ Included | - | LLM parser |
| `requirements*.txt` | ✅ | ✅ Installed | - | Dependencies |

**Key Points:**
- ✅ **DO** pass environment variables at deploy time (`--set-env-vars`)
- ✅ **DO** mount credentials as secrets (`--set-secrets`)
- ❌ **DON'T** bake credentials into Docker image
- ❌ **DON'T** commit credentials to git

---

### 📚 Additional Documentation

- **[OPTION3_DEPLOYMENT.md](OPTION3_DEPLOYMENT.md)** - Complete Gmail + Apps Script setup
- **[ENV_CONFIGURATION_GUIDE.md](ENV_CONFIGURATION_GUIDE.md)** - All environment variables explained
- **[CREDENTIALS_GUIDE.md](CREDENTIALS_GUIDE.md)** - How to set up Google Calendar API credentials

---

## 📚 Additional Resources

- [Google Cloud Run Docs](https://cloud.google.com/run/docs)
- [Cloud Functions Python Quickstart](https://cloud.google.com/functions/docs/quickstart-python)
- [Gmail Push Notifications](https://developers.google.com/gmail/api/guides/push)
- [Tesseract Docker Examples](https://github.com/tesseract-ocr/tesseract/wiki/Docker-Containers)

---

## 💡 Summary

**Best Approach for Your Use Case:**

1. **Use Docker with Tesseract** - Most flexible, full control
2. **Deploy to Cloud Run** - Easy scaling, supports Docker
3. **Gmail API + Pub/Sub** - For email triggers
4. **ML/OCR version** - Free, fast enough for your volume

**Sample deployment:**
```bash
# One-line deploy!
gcloud run deploy calhero \
  --source . \
  --allow-unauthenticated \
  --memory 1Gi
```

Tesseract is absolutely the right choice here! 🎉
