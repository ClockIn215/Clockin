# Operating Modes Guide

The calendar parser now supports three distinct operating modes for different testing and production scenarios.

---

## 📊 Mode Comparison Matrix

| Mode | Process Image | Check Duplicates | Create Events | Move Files | credentials.json | GEMINI_API_KEY |
|------|--------------|------------------|---------------|------------|-----------------|----------------|
| **Normal** | ✅ | ✅ | ✅ | ✅ | ✅ Required | ⚠️ LLM only |
| **--dry-run** | ✅ | ❌ | ❌ | ❌ | ❌ Not needed | ⚠️ LLM only |
| **--check-only** | ✅ | ✅ | ❌ | ❌ | ✅ Required | ⚠️ LLM only |

**Note:** ⚠️ = GEMINI_API_KEY only required when using LLM version (`calhero.py`), not needed for ML version (`calhero_ml.py`)

---

## 🔑 Credential Requirements by Version

### ML Version (calhero_ml.py)

| Mode | credentials.json | GEMINI_API_KEY | Why |
|------|-----------------|----------------|-----|
| **--dry-run** | ❌ | ❌ | Only local OCR, no API calls |
| **--check-only** | ✅ | ❌ | Needs calendar access for duplicate check |
| **normal** | ✅ | ❌ | Needs calendar access to create events |

### LLM Version (calhero.py)

| Mode | credentials.json | GEMINI_API_KEY | Why |
|------|-----------------|----------------|-----|
| **--dry-run** | ❌ | ✅ | Uses Gemini to process image (no calendar) |
| **--check-only** | ✅ | ✅ | Uses Gemini + calendar duplicate check |
| **normal** | ✅ | ✅ | Uses Gemini + calendar operations |

**Key Insight:** Even in `--dry-run` mode, LLM version needs GEMINI_API_KEY to process images!

📖 **Detailed setup:** See `CREDENTIALS_GUIDE.md`

---

## 🎯 Mode Descriptions

### 1. Normal Mode (Production)

**Purpose:** Full production operation

**What it does:**
- Processes images with OCR/LLM
- Checks for duplicate events in calendar
- Creates new events
- Moves processed files to `screenshots/processed/`

**When to use:**
- Production runs
- When you want to actually create calendar events

**Example:**
```bash
python calhero.py
python calhero_ml.py
```

**Output:**
```
🔧 Mode: NORMAL
📅 Using calendar: 2db8...c1b@group.calendar.google.com (from environment variable)
📷 Analyzing: schedule.png...
  ✅ Created: MyPrefix Coverage for 2026-01-12T06:00:00
  ⏩ Duplicate skipped: MyPrefix Training
  📦 Moved to: schedule.png

--- Processing Complete ---
Files processed: 1
Shifts created: 1
```

---

### 2. Dry-Run Mode (Test Processing)

**Purpose:** Test image processing without any calendar operations

**What it does:**
- ✅ Processes images with OCR/LLM
- ✅ Extracts and parses shifts
- ❌ No calendar API calls (doesn't check duplicates)
- ❌ Doesn't create events
- ❌ Doesn't move files
- ❌ Doesn't require calendar ID

**When to use:**
- Testing image processing accuracy
- Debugging OCR/LLM extraction
- Testing without calendar credentials
- Quick validation of shift extraction

**Example:**
```bash
# No calendar ID required!
python calhero.py --dry-run
python calhero_ml.py --dry-run --debug
```

**Output:**
```
🔧 Mode: DRY-RUN
   No calendar operations will be performed
📷 Analyzing: schedule.png...
  [DRY RUN] Would create: MyPrefix Coverage at 2026-01-12T06:00:00
  [DRY RUN] Would create: MyPrefix Training at 2026-01-13T14:00:00

--- Processing Complete ---
Files processed: 1
Would create: 2 shifts (dry-run mode)
```

---

### 3. Check-Only Mode (Read-Only Validation)

**Purpose:** Validate duplicate detection without creating events

**What it does:**
- ✅ Processes images with OCR/LLM
- ✅ Checks calendar for duplicates (read-only)
- ✅ Shows what would be created vs skipped
- ❌ Doesn't create events
- ❌ Doesn't move files
- ✅ Requires calendar ID

**When to use:**
- Testing duplicate detection logic
- Auditing what would happen before committing
- Safe testing with production calendar
- Validating time window logic (5-minute tolerance)
- Previewing batch imports

**Example:**
```bash
python calhero.py --check-only
python calhero_ml.py --check-only

# With test calendar
python calhero.py --check-only --calendar-id "test-id@group.calendar.google.com"
```

**Output:**
```
🔧 Mode: CHECK-ONLY (Read-only - will check duplicates but not create events)
📅 Using calendar: 2db8...c1b@group.calendar.google.com (from environment variable)
📷 Analyzing: schedule.png...
  🔍 Duplicate found: MyPrefix Coverage
  [CHECK ONLY] Would create: MyPrefix Training at 2026-01-13T14:00:00

--- Processing Complete ---
Files processed: 1
Would create: 1 shifts (check-only mode - no events created)
```

---

## 🚀 Usage Examples

### Local Development

```bash
# 1. Test image processing (no calendar needed)
python calhero.py --dry-run

# 2. Check what would be created (requires calendar)
python calhero.py --check-only

# 3. Create events (production)
python calhero.py

# 4. Force create even if duplicates exist
python calhero.py --force
```

### Testing Workflow

```bash
# Step 1: Test processing without calendar
python calhero_ml.py --dry-run --debug

# Step 2: Check duplicates with test calendar
python calhero.py --check-only --calendar-id "${TEST_CALENDAR_ID}"

# Step 3: If satisfied, create events
python calhero.py --calendar-id "${TEST_CALENDAR_ID}"

# Step 4: Deploy to production
python calhero.py  # Uses CALENDAR_ID from .env
```

### Docker Usage

```bash
# Dry-run (no calendar needed)
docker run --env-file .env calhero --dry-run

# Check-only with test calendar
docker run \
  -e CALENDAR_ID="test-id@group.calendar.google.com" \
  -e GEMINI_API_KEY="your-key" \
  -v $(pwd)/screenshots:/app/screenshots \
  calhero --check-only

# Production run
docker run --env-file .env \
  -v $(pwd)/screenshots:/app/screenshots \
  calhero
```

### Cloud Run HTTP API

```bash
# Dry-run mode
curl -X POST https://your-service.run.app \
  -F "image=@schedule.png" \
  -F "dry_run=true"

# Check-only mode
curl -X POST https://your-service.run.app \
  -F "image=@schedule.png" \
  -F "check_only=true"

# Normal mode
curl -X POST https://your-service.run.app \
  -F "image=@schedule.png"

# With specific calendar
curl -X POST "https://your-service.run.app?calendar_id=test-id@group.calendar.google.com" \
  -F "image=@schedule.png" \
  -F "check_only=true"
```

---

## ⚠️ Flag Combinations

### Valid Combinations

```bash
# Normal run with force
python calhero.py --force

# Check-only with test calendar
python calhero.py --check-only --calendar-id "test-id@group.calendar.google.com"

# Dry-run with debug (ML version)
python calhero_ml.py --dry-run --debug
```

### Invalid Combinations

```bash
# ❌ Cannot use both --dry-run and --check-only
python calhero.py --dry-run --check-only
# Error: Cannot use --dry-run and --check-only together

# ⚠️ --force has no effect in dry-run
python calhero.py --dry-run --force
# Warning: --force has no effect in --dry-run mode
```

---

## 📋 Mode Selection Decision Tree

```
Do you want to test image processing only?
├─ YES → Use --dry-run
│         - No calendar needed
│         - Fast testing
│         - No API calls
│
└─ NO → Do you want to actually create events?
        ├─ YES → Use normal mode (no flags)
        │         - Production run
        │         - Creates events
        │         - Moves files
        │
        └─ NO → Use --check-only
                  - Checks duplicates
                  - No event creation
                  - Safe for production calendar
```

---

## 🎓 Use Case Scenarios

### Scenario 1: Debugging OCR Issues

**Problem:** OCR not extracting shifts correctly

**Solution:** Use `--dry-run` with `--debug`

```bash
python calhero_ml.py --dry-run --debug
```

**Why:** See raw OCR output without touching calendar

---

### Scenario 2: Testing Against Production Calendar

**Problem:** Want to verify duplicate detection works correctly

**Solution:** Use `--check-only` with production calendar

```bash
python calhero.py --check-only
```

**Why:** Reads from production calendar safely, shows what would be created

---

### Scenario 3: Batch Import Validation

**Problem:** Have 20 screenshots to import, want to preview first

**Solution:** Run `--check-only` first, then normal mode

```bash
# Preview what would be created
python calhero.py --check-only

# Review output, then run for real
python calhero.py
```

---

### Scenario 4: Testing Without Calendar Credentials

**Problem:** Setting up CI/CD pipeline, no calendar access yet

**Solution:** Use `--dry-run` in CI

```bash
# In CI pipeline
python calhero.py --dry-run
# Validates image processing works
```

---

### Scenario 5: Testing Time Zone Logic

**Problem:** Verifying 5-minute duplicate detection window

**Solution:** Use `--check-only` to see duplicate detection

```bash
# Check what's detected as duplicate
python calhero.py --check-only --calendar-id "test-calendar@group.calendar.google.com"

# Manually verify in Google Calendar
```

---

## 🔍 Output Interpretation

### Normal Mode Output
```
  ✅ Created: Event name       # Event was created
  ⏩ Duplicate skipped: Event  # Event already exists
```

### Dry-Run Mode Output
```
  [DRY RUN] Would create: Event  # Would create if not in dry-run
```

### Check-Only Mode Output
```
  🔍 Duplicate found: Event           # Event exists in calendar
  [CHECK ONLY] Would create: Event    # Event doesn't exist, would create
```

---

## 🛠️ Environment Variables & Credentials by Mode

### Environment Variables (.env file)

| Mode | Requires CALENDAR_ID | Requires GEMINI_API_KEY |
|------|---------------------|------------------------|
| Normal | ✅ Yes | ⚠️ LLM only |
| --dry-run | ❌ No | ⚠️ LLM only |
| --check-only | ✅ Yes | ⚠️ LLM only |

### OAuth2 Files (Google Calendar API)

| Mode | Requires credentials.json | Auto-creates token.json |
|------|--------------------------|------------------------|
| Normal | ✅ Yes | ✅ Yes (on first run) |
| --dry-run | ❌ No | ❌ No |
| --check-only | ✅ Yes | ✅ Yes (on first run) |

**Note:** credentials.json is for Google Calendar API access (different from GEMINI_API_KEY)

---

## 📚 Related Documentation

- **`CREDENTIALS_GUIDE.md`** - **Complete credentials setup guide** ⭐
- `ENV_CONFIGURATION_GUIDE.md` - Environment variable setup
- `README.md` - General project overview
- `DEPLOYMENT_GUIDE.md` - Cloud deployment instructions
- `ML_GUIDE.md` - ML/OCR version details

---

## 💡 Tips

1. **Always test with --dry-run first** when developing new features
2. **Use --check-only before batch imports** to preview changes
3. **Combine --check-only with test calendar** for safe validation
4. **Use --dry-run in CI/CD** for automated testing
5. **Check-only is perfect for auditing** existing calendar state

---

## 🐛 Troubleshooting

### "Cannot use --dry-run and --check-only together"

**Problem:** Tried to use both flags

**Solution:** Choose one:
- `--dry-run` for testing processing only
- `--check-only` for testing duplicate detection

### "Configuration Error: No calendar ID configured"

**Problem:** Used `--check-only` without setting CALENDAR_ID

**Solution:** Set calendar ID:
```bash
# In .env file
CALENDAR_ID=your-id@group.calendar.google.com

# Or via CLI
python calhero.py --check-only --calendar-id "your-id@group.calendar.google.com"
```

### Dry-run works but normal mode fails

**Problem:** CALENDAR_ID not configured

**Solution:** Create `.env` file with CALENDAR_ID
```bash
cp .env.example .env
# Edit .env with your calendar ID
```

### "credentials.json not found"

**Problem:** Google Calendar API credentials missing

**Solution:** This is separate from GEMINI_API_KEY!
```bash
# Get credentials.json from Google Cloud Console
# See CREDENTIALS_GUIDE.md for step-by-step setup

# Quick link:
# https://console.cloud.google.com/apis/credentials
```

**Tip:** Not needed for `--dry-run` mode

### "Gemini API Key Missing"

**Problem:** LLM version needs GEMINI_API_KEY (even in dry-run!)

**Solution:**
```bash
# Get API key from Google AI Studio
# https://aistudio.google.com/app/apikey

# Add to .env file
echo "GEMINI_API_KEY=your-key-here" >> .env
```

**Alternative:** Use ML version instead:
```bash
python calhero_ml.py --dry-run  # No API key needed!
```

---

**Last Updated:** January 20, 2026  
**Version:** 2.0 - Enhanced modes with --check-only
