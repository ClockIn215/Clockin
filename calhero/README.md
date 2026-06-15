# Calhero - Calendar Screenshot Parser

Automatically extract work shifts from schedule screenshots and sync to Google Calendar.

## 📦 Two Versions + Shared Utilities

### Core Files
- **`calendar_utils.py`** - Shared utilities (authentication, duplicate checking, file management)
- **`calhero.py`** - LLM version using Google Gemini Vision API
- **`calhero_ml.py`** - ML/OCR version using Tesseract + OpenCV
- **`test_comparison.py`** - Compare accuracy of both versions

### LLM Version Features
- ✅ Highest accuracy (95-99%)
- ✅ Handles complex/varied layouts
- ⚠️ Requires API key (~$0.001/image)

### ML/OCR Version Features
- ✅ Free, runs locally
- ✅ Great for learning ML concepts
- ✅ Faster processing (2x speed)
- ⚠️ Requires Tesseract OCR installation

📖 **[Read detailed comparison](COMPARISON.md)** | 🧪 **[Testing guide](TESTING_GUIDE.md)**

---

## 🚀 Quick Start

### 1. Clone and Setup

```bash
git clone <repository-url>
cd calhero
python3 -m venv calheroenv
source calheroenv/bin/activate
pip install -r requirements_ml.txt  # For ML version
```

### 2. Test with Sample Data (No Setup Required!)

Test immediately with provided sample data:

```bash
# Test ML/OCR parser with sample screenshot
python test_ocr.py samples/sample_schedule.png

# Test with ground truth validation
python test_ocr.py samples/sample_schedule.png --validate samples/sample_ground_truth.json

# Test with calhero_ml.py (requires copying to screenshots/ first)
mkdir -p screenshots
cp samples/sample_schedule.png screenshots/
python calhero_ml.py --dry-run
```

See `samples/README.md` for more details on sample data.

### 3. Setup for Production Use

For use with your actual schedule screenshots:

```bash
# Create directory for your screenshots (gitignored for privacy)
mkdir -p screenshots/processed

# Setup Google Calendar credentials
# See CREDENTIALS_GUIDE.md for detailed instructions

# Test with your screenshot (calhero_ml.py reads from screenshots/ directory)
python calhero_ml.py --dry-run
```

### Setup (LLM Version - Requires API Key)
```bash
pip install -r requirements.txt
export GEMINI_API_KEY=your-api-key

# Copy sample to screenshots/ directory
mkdir -p screenshots
cp samples/sample_schedule.png screenshots/
python calhero.py --dry-run
```

📖 **[Read full ML guide](ML_GUIDE.md)** | 📸 **[Sample data guide](samples/README.md)**

---

## 📁 Folder Structure
```
screenshots/          # Put your schedule screenshots here
screenshots/processed/  # Processed images move here
credentials.json      # Google Calendar OAuth credentials
token.json           # Auto-generated auth token
```

---

## 🎯 Usage Examples

### Basic run (LLM)
```bash
python calhero.py
```

### Preview mode (ML)
```bash
python calhero_ml.py --dry-run
```

### Debug OCR output
```bash
python calhero_ml.py --debug
```

### Compare both versions
```bash
python test_comparison.py
```

### Test ML parser only
```bash
# Quick ML debugging and testing
python test_ocr.py screenshots/schedule.png

# With ground truth validation (no LLM needed!)
python test_ocr.py screenshots/schedule.png --validate ground_truth.json
```

### Test specific images
```bash
python test_comparison.py --images screenshots/processed/*.png
```

---

## 📚 Documentation

- **[TESTING_GUIDE.md](TESTING_GUIDE.md)** - How to test and compare both versions
- **[ML_GUIDE.md](ML_GUIDE.md)** - Complete ML tutorial with exercises
- **[COMPARISON.md](COMPARISON.md)** - LLM vs ML detailed comparison
- **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - Command cheat sheet

---

## 🛠️ Requirements

**Both versions need:**
- Python 3.8+
- Google Calendar API credentials (`credentials.json`)

**ML version additionally needs:**
- Tesseract OCR engine

---

## 💡 Which Version Should I Use?

**Choose LLM** if you want:
- Maximum accuracy (95-99%)
- Quick setup
- Production-ready solution

**Choose ML** if you want:
- Learn computer vision & ML
- Free/local processing
- Full control and transparency
- Faster processing (2x speed)

**Not sure?** Run the test comparison:
```bash
python test_comparison.py
```

This will show you accuracy metrics and recommend which version to use for your specific images.

---

## 🚀 Cloud Deployment

Deploy as a serverless function or Docker container with email triggers!

### Quick Deploy Options

**Docker (Local or Cloud):**
```bash
docker build -t calhero .
docker run -v $(pwd)/screenshots:/app/screenshots calhero
```

**Google Cloud Run (One command!):**
```bash
gcloud run deploy calhero --source . --allow-unauthenticated --memory 1Gi
```

**Email Trigger Workflow:**
```
Email with schedule → Gmail API → Cloud Function → Parse → Calendar ✅
```

### OCR Engine Options

| Engine | Setup | Size | Best For |
|--------|-------|------|----------|
| **Tesseract** (default) | System binary | ~150MB | Docker, Cloud Run |
| **EasyOCR** (pure Python) | pip only | ~500MB | Cloud Functions, Lambda |
| **Gemini LLM** | API key only | ~0MB | Serverless, quick deploys |

📖 **Deployment Guides:**
- **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** - Complete deployment overview
- **[DOCKER_PARAMETERIZATION.md](DOCKER_PARAMETERIZATION.md)** - Build args & runtime switching
- **[OPTION3_DEPLOYMENT.md](OPTION3_DEPLOYMENT.md)** - Gmail → Apps Script → Cloud Run (easiest!)

### Quick Deploy Script

```bash
# Deploy to Cloud Run with ML parser
./deploy.sh --type cloudrun --parser ml --project-id my-project

# Switch between parsers at runtime (no rebuild!)
gcloud run services update calhero --set-env-vars USE_LLM=true
```
