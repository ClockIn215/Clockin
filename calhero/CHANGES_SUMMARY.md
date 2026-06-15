# Configuration Changes Summary

## 🎯 What Was Done

Implemented **Option B: Explicit Calendar ID Override** with `.env` file pattern for better security and configuration management.

---

## 📦 Files Modified

### 1. **Dependencies**
- ✅ `requirements.txt` - Added `python-dotenv`
- ✅ `requirements_ml.txt` - Added `python-dotenv`

### 2. **Core Configuration**
- ✅ `calendar_utils.py` - Major updates:
  - Import and load `python-dotenv`
  - Changed Config class to load from environment variables
  - Added `get_active_calendar_id(cli_override)` method
  - Added `log_calendar_selection(calendar_id, source)` method
  - Updated function docstrings for clarity
  - Added validation errors when calendar ID not configured

### 3. **Main Scripts**
- ✅ `calhero.py` - Updated to:
  - Add `--calendar-id` CLI argument
  - Get active calendar ID with Config.get_active_calendar_id()
  - Log calendar selection at startup
  - Pass calendar_id to all event functions
  
- ✅ `calhero_ml.py` - Updated to:
  - Add `--calendar-id` CLI argument
  - Get active calendar ID with Config.get_active_calendar_id()
  - Log calendar selection at startup
  - Pass calendar_id to all event functions

### 4. **Cloud/Service Files**
- ✅ `cloud_run_service.py` - Updated to:
  - Support `calendar_id` query parameter
  - Get active calendar ID before processing
  - Pass calendar_id to process functions
  - Return calendar source in response
  
- ✅ `cloud_function_entry.py` - Updated to:
  - Support `calendar_id` in request payload
  - Get active calendar ID before processing
  - Pass calendar_id to process functions
  - Return calendar source in response

### 5. **New Files Created**
- ✅ `.env.example` - Template with all configuration options
- ✅ `.gitignore` - Excludes .env, credentials, and other sensitive files
- ✅ `ENV_CONFIGURATION_GUIDE.md` - Comprehensive setup and usage guide
- ✅ `CHANGES_SUMMARY.md` - This file

---

## 🔧 Configuration Priority

**Highest to Lowest:**
1. Command-line argument (`--calendar-id`)
2. Environment variable (`CALENDAR_ID`)
3. Error if not configured (no hardcoded fallback)

---

## 📋 Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `CALENDAR_ID` | ✅ Yes | None | Production Google Calendar ID |
| `TEST_CALENDAR_ID` | ❌ No | None | Test calendar ID |
| `GEMINI_API_KEY` | ⚠️ LLM only | None | Gemini API key |
| `TIMEZONE` | ❌ No | `America/Chicago` | Event timezone |
| `EVENT_PREFIX` | ❌ No | (none) | Event name prefix |
| `GEMINI_MODEL` | ❌ No | `gemini-2.5-flash` | LLM model |

---

## ✨ New Features

### 1. **Calendar ID Logging**
Scripts now show which calendar is being used:
```
📅 Using calendar: 2db8...c1b@group.calendar.google.com (from environment variable)
```

### 2. **Security Enhancements**
- No hardcoded secrets in code
- Sensitive values masked in logs
- `.env` file excluded from git

### 3. **Flexible Configuration**
- Override via CLI for quick testing
- Environment variables for Docker/Cloud
- Clear error messages when misconfigured

---

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Setup Environment
```bash
cp .env.example .env
# Edit .env with your values
```

### 3. Run
```bash
# Use production calendar (from .env)
python calhero.py

# Override with test calendar
python calhero.py --calendar-id "your-test-id@group.calendar.google.com"
```

---

## 🐳 Docker Usage

```bash
# Build
docker build -t calhero .

# Run with .env file
docker run --env-file .env -v $(pwd)/screenshots:/app/screenshots calhero

# Run with explicit env vars
docker run \
  -e CALENDAR_ID="your-id@group.calendar.google.com" \
  -e GEMINI_API_KEY="your-key" \
  -v $(pwd)/screenshots:/app/screenshots \
  calhero

# Override calendar at runtime
docker run --env-file .env \
  -e CALENDAR_ID="test-id@group.calendar.google.com" \
  calhero
```

---

## ☁️ Cloud Deployment

### Cloud Run
```bash
gcloud run deploy calhero \
  --source . \
  --set-env-vars CALENDAR_ID="your-id@group.calendar.google.com" \
  --set-env-vars GEMINI_API_KEY="your-key" \
  --allow-unauthenticated
```

### Using Secret Manager (Recommended)
```bash
# Create secrets
echo -n "your-id@group.calendar.google.com" | gcloud secrets create calendar-id --data-file=-
echo -n "your-api-key" | gcloud secrets create gemini-key --data-file=-

# Deploy with secrets
gcloud run deploy calhero \
  --source . \
  --update-secrets CALENDAR_ID=calendar-id:latest \
  --update-secrets GEMINI_API_KEY=gemini-key:latest
```

---

## 🧪 Testing Workflow

```bash
# Create .env with production calendar
cat > .env << 'EOL'
CALENDAR_ID=prod-calendar-id@group.calendar.google.com
TEST_CALENDAR_ID=test-calendar-id@group.calendar.google.com
GEMINI_API_KEY=your-api-key
EOL

# Test with test calendar (doesn't modify .env)
python calhero.py --calendar-id "${TEST_CALENDAR_ID}" --dry-run

# Deploy to production (uses .env CALENDAR_ID)
python calhero.py
```

---

## 🔒 Security Improvements

### Before
- API keys and calendar IDs hardcoded in source code
- Committed to git (potential security risk)
- Difficult to switch between test/prod

### After
- All secrets in `.env` file (excluded from git)
- Easy to rotate keys without code changes
- Calendar ID masked in logs for privacy
- Clear error messages for missing configuration

---

## 🎓 Next Steps

1. **Create your `.env` file:**
   ```bash
   cp .env.example .env
   # Edit .env with your actual values
   ```

2. **Test locally:**
   ```bash
   python calhero.py --dry-run
   ```

3. **Verify calendar selection:**
   - Check the log output shows correct calendar
   - Verify source (CLI argument, environment variable, or error)

4. **Update deployment scripts:**
   - Add environment variables to Docker/Cloud Run configs
   - Use Secret Manager for production secrets

5. **Read the guide:**
   - See `ENV_CONFIGURATION_GUIDE.md` for detailed instructions

---

## 📚 Documentation

- `ENV_CONFIGURATION_GUIDE.md` - Complete setup and usage guide
- `.env.example` - Template for environment variables
- `README.md` - Project overview (may need updating)

---

## ✅ Testing Checklist

Before deploying to production:

- [ ] Created `.env` file with all required values
- [ ] Tested local run: `python calhero.py --dry-run`
- [ ] Verified calendar ID logging shows correct calendar
- [ ] Tested CLI override: `python calhero.py --calendar-id "test-id"`
- [ ] Tested Docker build and run with env vars
- [ ] Updated cloud deployment scripts (if applicable)
- [ ] Verified `.env` is in `.gitignore`
- [ ] Removed any hardcoded secrets from documentation

---

## 🆘 Support

If you encounter issues:

1. Check `ENV_CONFIGURATION_GUIDE.md` - Troubleshooting section
2. Verify `.env` file exists and has correct values
3. Test env var loading: `python -c "from dotenv import load_dotenv; import os; load_dotenv(); print(os.getenv('CALENDAR_ID'))"`
4. Check logs for calendar selection output

---

**Implementation Date:** January 20, 2026  
**Status:** ✅ Complete - Ready for testing
