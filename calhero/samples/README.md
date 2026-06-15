# Sample Test Data

This directory contains sanitized sample data for testing the calendar parser without requiring real schedule screenshots.

## 📁 Files

- **`sample_schedule.png`** - Example schedule screenshot with dummy data (names, dates sanitized)
- **`sample_ground_truth.json`** - Expected parsing results for the sample screenshot

## 🚀 Quick Start Testing

Test the ML version with sample data immediately after cloning:

```bash
# Test OCR parsing with sample data
python test_ocr.py samples/sample_schedule.png --validate samples/sample_ground_truth.json

# Run full comparison test (ML + LLM)
python test_comparison.py --image samples/sample_schedule.png --ground-truth samples/sample_ground_truth.json

# Test with calhero_ml.py (requires copying to screenshots/ first)
mkdir -p screenshots
cp samples/sample_schedule.png screenshots/
python calhero_ml.py --dry-run
```

## 📸 Using Your Own Schedule Screenshots

For production use with your actual schedules:

### 1. Create Screenshots Directory

```bash
# Create directory for your personal screenshots (gitignored)
mkdir -p screenshots/processed
```

The `screenshots/` directory is gitignored to protect your privacy. Your personal schedule images will never be committed to version control.

### 2. Add Your Screenshots

```bash
# Place your schedule screenshots here
cp /path/to/your/schedule.png screenshots/

# Processed files will automatically go to screenshots/processed/
```

### 3. Create Your Personal Ground Truth (Optional)

For testing with your own data:

```bash
# Create your personal ground truth file (gitignored)
cp samples/sample_ground_truth.json my_ground_truth.json

# Edit my_ground_truth.json with your actual schedule data
# Then test:
python test_ocr.py screenshots/your_schedule.png --validate my_ground_truth.json
```

**Privacy Note:** Files like `ground_truth.json`, `my_ground_truth.json`, and `results.json` are gitignored to keep your personal schedule data private.

## 📊 Sample Data Format

### sample_ground_truth.json Structure

```json
{
  "shifts": [
    {
      "date": "2026-01-15",
      "day": "Wed",
      "shift_type": "Coverage",
      "start_time": "06:00",
      "end_time": "18:00"
    }
  ]
}
```

## 🎨 Creating Your Own Samples

If you want to contribute additional sample data:

1. **Sanitize a screenshot:**
   - Replace real names with generic ones ("John Doe", "Jane Smith")
   - Use future/past dates that aren't personally identifiable
   - Remove any workplace-specific information
   - Remove any identifying logos or headers

2. **Create corresponding ground truth:**
   - Match the sanitized screenshot exactly
   - Use the same date format and structure
   - Verify accuracy by running tests

3. **Submit a PR** with the new sample files in this directory

## 🧪 Running All Tests

```bash
# Test with sample data (safe to run anytime)
python test_ocr.py samples/sample_schedule.png

# Test with your data (requires screenshots/ directory)
python test_ocr.py screenshots/your_schedule.png --dry-run

# Full integration test with calendar creation (requires moving sample to screenshots/)
mkdir -p screenshots
cp samples/sample_schedule.png screenshots/
python calhero_ml.py --check-only
```

## 📚 Documentation

For more testing options and documentation:
- See `TESTING_GUIDE.md` for comprehensive testing instructions
- See `README.md` for setup and installation
- See `DEPLOYMENT_GUIDE.md` for production deployment

## ⚠️ Important Notes

- ✅ **Sample data** in this directory is safe to commit and share
- ❌ **Your personal data** in `screenshots/` and `ground_truth.json` is gitignored
- 🔒 **Never commit** real schedule screenshots with personal information
- 📁 **Create `screenshots/` directory** when ready to use with real data
- 📝 **Note:** `calhero_ml.py` expects images in `screenshots/` directory - copy sample files there for testing with that script
