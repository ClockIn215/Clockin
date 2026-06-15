# Environment Configuration Guide

This guide explains the new `.env` file-based configuration system for calendar IDs and API keys.

## 🎯 What Changed?

**Before:** Hardcoded values in `calendar_utils.py`
```python
GEMINI_API_KEY = "GKEY"
CALENDAR_ID = "PROD_CAL_ID@group.calendar.google.com"
TEST_CALENDAR_ID = "TEST_CAL_ID@group.calendar.google.com"
```

**After:** Environment variables loaded from `.env` file
```python
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
CALENDAR_ID = os.getenv('CALENDAR_ID')
TEST_CALENDAR_ID = os.getenv('TEST_CALENDAR_ID')
```

---

## 📋 Setup Instructions

### 1. Install Dependencies

```bash
# Activate your virtual environment
source calenv/bin/activate

# Install python-dotenv
pip install python-dotenv

# Or reinstall from requirements
pip install -r requirements.txt
```

### 2. Create Your `.env` File

```bash
# Copy the example file
cp .env.example .env
```

### 3. Edit `.env` with Your Values

Open `.env` in your editor and add your actual values:

```bash
# Required: Production calendar ID
CALENDAR_ID=PROD_CAL_ID@group.calendar.google.com

# Optional: Test calendar ID
TEST_CALENDAR_ID=TEST_CAL_ID@group.calendar.google.com

# Required (for LLM version): Gemini API key
GEMINI_API_KEY=GKEY

# Optional: Timezone (default: America/Chicago)
TIMEZONE=America/Chicago

# Optional: Event prefix (default: none)
EVENT_PREFIX=MyPrefix 
```

---

## 🚀 Usage

### Local Development

```bash
# Use production calendar (from .env)
python calhero.py

# Override with test calendar via CLI
python calhero.py --calendar-id "80745f24...@group.calendar.google.com"

# Same for ML version
python calhero_ml.py --calendar-id "80745f24...@group.calendar.google.com"
```

### Docker Deployment

```bash
# Pass environment variables to Docker
docker run \
  -e CALENDAR_ID="your-calendar-id@group.calendar.google.com" \
  -e GEMINI_API_KEY="your-api-key" \
  -v $(pwd)/screenshots:/app/screenshots \
  calhero

# Or use .env file
docker run --env-file .env \
  -v $(pwd)/screenshots:/app/screenshots \
  calhero

# Override at runtime
docker run \
  --env-file .env \
  -e CALENDAR_ID="test-calendar-id@group.calendar.google.com" \
  calhero
```

### Cloud Run Deployment

```bash
# Set environment variables during deployment
gcloud run deploy calhero \
  --source . \
  --set-env-vars CALENDAR_ID="your-id@group.calendar.google.com" \
  --set-env-vars GEMINI_API_KEY="your-key" \
  --allow-unauthenticated

# Or use secrets (recommended for production)
gcloud run deploy calhero \
  --source . \
  --update-secrets CALENDAR_ID=calendar-id:latest \
  --update-secrets GEMINI_API_KEY=gemini-key:latest
```

---

## 📊 Configuration Priority

The system uses this priority order (highest to lowest):

1. **Command-line argument** `--calendar-id`
2. **Environment variable** `CALENDAR_ID`
3. **Error if not set** (no hardcoded fallback)

### Examples

```bash
# Priority 1: CLI argument wins
CALENDAR_ID=prod-id python calhero.py --calendar-id test-id
# Uses: test-id

# Priority 2: Environment variable
CALENDAR_ID=prod-id python calhero.py
# Uses: prod-id

# No calendar ID configured
python calhero.py
# Error: "No calendar ID configured. Please set CALENDAR_ID in .env file or use --calendar-id argument"
```

---

## 🔒 Security Features

### 1. Calendar ID Logging (with Masking)

When you run the scripts, you'll see which calendar is being used:

```
📅 Using calendar: 2db8...c1b@group.calendar.google.com (from environment variable)
```

### 2. .gitignore Protection

The `.env` file is automatically excluded from git to prevent accidental commits:

```gitignore
# .gitignore
.env
credentials.json
token.json
```

### 3. Environment Variable Validation

If a required variable is missing, you get a clear error:

```
❌ Configuration Error: No calendar ID configured. Please set CALENDAR_ID in .env file or use --calendar-id argument
```

---

## 🧪 Testing Workflow

### Recommended Setup

1. **Production**: Use `CALENDAR_ID` in `.env`
2. **Testing**: Use `--calendar-id` argument to override

```bash
# Create test run script
cat > test_run.sh << 'EOF'
#!/bin/bash
# Run with test calendar
python calhero.py \
  --calendar-id "${TEST_CALENDAR_ID}" \
  --dry-run
EOF

chmod +x test_run.sh
./test_run.sh
```

### Environment-Based Testing

Create separate env files:

```bash
# .env.production
CALENDAR_ID=prod-calendar-id@group.calendar.google.com

# .env.test
CALENDAR_ID=test-calendar-id@group.calendar.google.com

# Use different env files
set -a
source .env.test
python calhero.py
```

---

## 🌐 Cloud/Docker Best Practices

### Use Secret Manager (Recommended)

**Google Cloud:**
```bash
# Store secrets
gcloud secrets create calendar-id --data-file=- <<< "your-id@group.calendar.google.com"
gcloud secrets create gemini-api-key --data-file=- <<< "your-api-key"

# Reference in Cloud Run
gcloud run deploy calhero \
  --source . \
  --update-secrets CALENDAR_ID=calendar-id:latest \
  --update-secrets GEMINI_API_KEY=gemini-api-key:latest
```

**Docker Compose:**
```yaml
# docker-compose.yml
version: '3.8'
services:
  calhero:
    build: .
    env_file: .env
    volumes:
      - ./screenshots:/app/screenshots
    environment:
      - CALENDAR_ID=${CALENDAR_ID}
      - GEMINI_API_KEY=${GEMINI_API_KEY}
```

---

## 📝 Available Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `CALENDAR_ID` | ✅ Yes | None | Production Google Calendar ID |
| `TEST_CALENDAR_ID` | ❌ No | None | Test calendar ID (for reference) |
| `GEMINI_API_KEY` | ⚠️ LLM only | None | Gemini API key for LLM version |
| `TIMEZONE` | ❌ No | `America/Chicago` | Timezone for events |
| `EVENT_PREFIX` | ❌ No | (none) | Prefix for event names |
| `GEMINI_MODEL` | ❌ No | `gemini-2.5-flash` | Gemini model to use |

---

## 🐛 Troubleshooting

### "No calendar ID configured" Error

**Problem:** Script exits with calendar ID error

**Solution:**
```bash
# Check if .env exists
ls -la .env

# Verify CALENDAR_ID is set
cat .env | grep CALENDAR_ID

# Test environment variable loading
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print(os.getenv('CALENDAR_ID'))"
```

### Environment Variables Not Loading

**Problem:** Changes to `.env` not taking effect

**Solution:**
```bash
# Make sure .env is in the same directory as your scripts
pwd
ls -la .env

# Verify python-dotenv is installed
pip show python-dotenv

# Restart your terminal/shell
```

### Docker Environment Issues

**Problem:** Docker can't read environment variables

**Solution:**
```bash
# Use --env-file flag
docker run --env-file .env calhero

# Or pass variables explicitly
docker run -e CALENDAR_ID="your-id" -e GEMINI_API_KEY="your-key" calhero

# Debug: Print env vars inside container
docker run --env-file .env calhero env | grep CALENDAR
```

---

## 🔄 Migration Checklist

- [x] Install `python-dotenv`: `pip install python-dotenv`
- [ ] Copy `.env.example` to `.env`: `cp .env.example .env`
- [ ] Fill in your actual values in `.env`
- [ ] Test locally: `python calhero.py --dry-run`
- [ ] Verify calendar ID logging shows correct calendar
- [ ] Update Docker/Cloud deployment scripts with new env vars
- [ ] Remove hardcoded values from any deployment docs

---

## 💡 Tips

1. **Keep `.env.example` updated** - When adding new env vars, update the example file
2. **Use different calendars for dev/staging/prod** - Set appropriate `CALENDAR_ID` in each environment
3. **Never commit `.env`** - It's already in `.gitignore`, but double-check
4. **Use Secret Manager in production** - Don't store secrets in plain env vars in cloud environments
5. **Log calendar selection** - The scripts now log which calendar is being used for easy debugging

---

## 📚 Related Files

- `.env.example` - Template for environment variables
- `.gitignore` - Excludes `.env` from git
- `calendar_utils.py` - Config class with env var loading
- `calhero.py` - LLM version with `--calendar-id` argument
- `calhero_ml.py` - ML version with `--calendar-id` argument
- `cloud_run_service.py` - Cloud Run HTTP service
- `cloud_function_entry.py` - Cloud Function entry point
