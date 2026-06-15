# Quick Credentials Reference

## 🔑 What You Need

### ML Version (calhero_ml.py)
```bash
# Dry-run mode
python calhero_ml.py --dry-run
# Needs: NOTHING! 🎉

# Normal/Check-only mode
python calhero_ml.py
# Needs: credentials.json (Google Calendar OAuth2)
```

### LLM Version (calhero.py)
```bash
# Dry-run mode
python calhero.py --dry-run
# Needs: GEMINI_API_KEY (in .env)

# Normal/Check-only mode
python calhero.py
# Needs: credentials.json + GEMINI_API_KEY
```

---

## 📊 Quick Comparison

| Version | Mode | credentials.json | GEMINI_API_KEY |
|---------|------|-----------------|----------------|
| ML | --dry-run | ❌ | ❌ |
| ML | --check-only | ✅ | ❌ |
| ML | normal | ✅ | ❌ |
| LLM | --dry-run | ❌ | ✅ |
| LLM | --check-only | ✅ | ✅ |
| LLM | normal | ✅ | ✅ |

---

## 🚀 Setup Links

**credentials.json:**
- Get from: https://console.cloud.google.com/apis/credentials
- Type: OAuth 2.0 Client ID (Desktop app)

**GEMINI_API_KEY:**
- Get from: https://aistudio.google.com/app/apikey
- Add to: `.env` file

---

## 📚 Full Guide

See **CREDENTIALS_GUIDE.md** for complete step-by-step setup!
