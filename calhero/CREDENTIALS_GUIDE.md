# Credentials Guide

Complete guide to understanding and setting up credentials for the calendar parser.

---

## 🔑 Two Types of Credentials

The calendar parser uses **two different Google services**, each requiring different credentials:

### 1. Google Calendar API (OAuth2)
- **Files:** `credentials.json` + `token.json`
- **Purpose:** Access your Google Calendar to check/create events
- **Used by:** Both LLM and ML versions
- **When needed:** Normal mode, check-only mode
- **NOT needed:** Dry-run mode

### 2. Google Gemini API (API Key)
- **File:** `GEMINI_API_KEY` in `.env`
- **Purpose:** Process images using Gemini LLM
- **Used by:** LLM version only (`calhero.py`)
- **When needed:** All modes (including dry-run!)
- **NOT needed:** ML version (`calhero_ml.py`)

---

## 📊 Quick Reference: What's Needed When

| Script | Mode | credentials.json | GEMINI_API_KEY |
|--------|------|-----------------|----------------|
| `calhero_ml.py` | --dry-run | ❌ | ❌ |
| `calhero_ml.py` | --check-only | ✅ | ❌ |
| `calhero_ml.py` | normal | ✅ | ❌ |
| `calhero.py` | --dry-run | ❌ | ✅ |
| `calhero.py` | --check-only | ✅ | ✅ |
| `calhero.py` | normal | ✅ | ✅ |

---

## 📁 Part 1: Google Calendar API Setup

### What You Need

1. **credentials.json** - OAuth2 client credentials (you download this)
2. **token.json** - Your personal access token (auto-generated on first run)

### Step-by-Step Setup

#### Step 1: Get credentials.json

1. **Go to Google Cloud Console**
   - Visit: https://console.cloud.google.com/apis/credentials

2. **Create or Select Project**
   ```
   Click "Select a project" → "New Project"
   Name: "Calendar Parser" (or any name)
   Click "Create"
   ```

3. **Enable Google Calendar API**
   ```
   Go to: https://console.cloud.google.com/apis/library
   Search: "Google Calendar API"
   Click on it → Click "Enable"
   ```

4. **Create OAuth2 Credentials**
   ```
   Go to: https://console.cloud.google.com/apis/credentials
   Click: "Create Credentials" → "OAuth client ID"
   
   If prompted to configure consent screen:
     → Click "Configure Consent Screen"
     → Choose "External" (unless you have Google Workspace)
     → Fill in app name: "Calendar Parser"
     → Add your email
     → Save and continue through steps
     → Add scope: "../auth/calendar"
     → Add yourself as test user
     → Back to credentials
   
   Application type: "Desktop app"
   Name: "Calendar Parser Desktop"
   Click "Create"
   ```

5. **Download credentials.json**
   ```
   Click the download icon (⬇️) next to your newly created credentials
   Save as: credentials.json
   Move to: /path/to/calhero/credentials.json
   ```

#### Step 2: First Run (Creates token.json)

```bash
# Run the script
python calhero_ml.py

# What happens:
# 1. Browser opens automatically
# 2. You see Google login screen
# 3. Log in with your Google account
# 4. Warning: "Google hasn't verified this app" → Click "Advanced" → "Go to Calendar Parser (unsafe)"
# 5. Click "Allow" to grant calendar access
# 6. Browser shows "The authentication flow has completed"
# 7. token.json is created automatically ✅
```

#### Step 3: Verify Setup

```bash
# Check files exist
ls -la credentials.json token.json

# Should see:
# -rw-r--r--  credentials.json
# -rw-r--r--  token.json
```

### Understanding token.json

**What's inside:**
```json
{
  "token": "ya29.a0AfH6SMB...",           // Access token (expires in ~1 hour)
  "refresh_token": "1//0gXXX...",          // Refresh token (long-lived)
  "token_uri": "https://oauth2.googleapis.com/token",
  "client_id": "xxx.apps.googleusercontent.com",
  "scopes": ["https://www.googleapis.com/auth/calendar"]
}
```

**How it works:**
- Access token expires every hour
- Script automatically uses refresh_token to get new access token
- You never need to manually edit this file
- If corrupted, just delete it and run script again (browser will reopen)

**Security:**
- ⚠️ **NEVER share this file** - it grants access to YOUR calendar!
- Already in `.gitignore`
- If leaked, revoke access at: https://myaccount.google.com/permissions

---

## 🔑 Part 2: Gemini API Key Setup

### What You Need

- **GEMINI_API_KEY** - API key for Gemini LLM

### Step-by-Step Setup

#### Step 1: Get API Key

1. **Go to Google AI Studio**
   - Visit: https://aistudio.google.com/app/apikey

2. **Create API Key**
   ```
   Click "Create API key"
   Select project (or create new)
   Copy the key (looks like: AIzaSyC_AiusDqdpr3HiLP6iaqf...)
   ```

#### Step 2: Add to .env File

```bash
# Open .env file
nano .env

# Add this line:
GEMINI_API_KEY=GKEY

# Save and exit
```

#### Step 3: Verify Setup

```bash
# Test that it's loaded
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('✅ Key loaded' if os.getenv('GEMINI_API_KEY') else '❌ Key missing')"
```

### Security Notes

- ⚠️ **NEVER commit .env to git**
- Already in `.gitignore`
- If leaked, regenerate at: https://aistudio.google.com/app/apikey
- Free tier: 60 requests/minute, 1500 requests/day

---

## 🔄 How They Work Together

### Normal LLM Run

```
1. Load GEMINI_API_KEY from .env
   ↓
2. Create Gemini client
   ↓
3. Load credentials.json
   ↓
4. Load or refresh token.json
   ↓
5. Process image with Gemini API
   ↓
6. Check calendar for duplicates (uses token.json)
   ↓
7. Create events in calendar (uses token.json)
```

### Dry-Run LLM Mode

```
1. Load GEMINI_API_KEY from .env
   ↓
2. Create Gemini client
   ↓
3. Process image with Gemini API
   ↓
4. Show results (no calendar access needed)
```

### Normal ML Run

```
1. Load credentials.json
   ↓
2. Load or refresh token.json
   ↓
3. Process image with Tesseract OCR (local, no API)
   ↓
4. Check calendar for duplicates (uses token.json)
   ↓
5. Create events in calendar (uses token.json)
```

### Dry-Run ML Mode

```
1. Process image with Tesseract OCR (local)
   ↓
2. Show results (no credentials needed at all!)
```

---

## 🚨 Troubleshooting

### Error: "credentials.json not found"

**Problem:**
```
FileNotFoundError: credentials.json not found
```

**Solution:**
1. Download from Google Cloud Console (see Part 1)
2. Save as `credentials.json` in same directory as scripts
3. Verify: `ls -la credentials.json`

---

### Error: "GEMINI_API_KEY not set"

**Problem:**
```
❌ Gemini API Key Missing
```

**Solution:**
1. Get API key from https://aistudio.google.com/app/apikey
2. Add to `.env` file: `GEMINI_API_KEY=your-key-here`
3. Verify: Check `.env` file exists and contains the key

---

### Browser Opens But Shows Error

**Problem:**
```
"Google hasn't verified this app"
```

**Solution:**
This is normal for personal projects!
1. Click "Advanced"
2. Click "Go to Calendar Parser (unsafe)"
3. Click "Allow"

The app only accesses YOUR calendar, not others.

---

### Token Expired / Invalid Grant

**Problem:**
```
google.auth.exceptions.RefreshError: invalid_grant
```

**Solution:**
```bash
# Delete token and re-authorize
rm token.json
python calhero.py
# Browser will open for fresh login
```

---

### Works Locally But Not in Docker

**Problem:**
Browser can't open in Docker environment

**Solutions:**

**Option 1: Generate token locally, then copy**
```bash
# On local machine
python calhero.py  # Creates token.json
docker cp token.json container:/app/token.json
```

**Option 2: Use service account (advanced)**
- Create service account in Google Cloud
- Download JSON key
- Use different auth method (not covered here)

---

## 📋 Complete Setup Checklist

### For ML Version (calhero_ml.py)

- [ ] Download `credentials.json` from Google Cloud Console
- [ ] Place in project directory
- [ ] Run script once (browser opens)
- [ ] Grant calendar access
- [ ] Verify `token.json` created
- [ ] Test: `python calhero_ml.py --dry-run` (should work!)

### For LLM Version (calhero.py)

- [ ] All steps from ML version above
- [ ] Get Gemini API key from https://aistudio.google.com/app/apikey
- [ ] Add to `.env`: `GEMINI_API_KEY=your-key`
- [ ] Test: `python calhero.py --dry-run` (should work!)

---

## 🔒 Security Best Practices

### What to Keep Secret

| File | Security Level | In .gitignore? |
|------|----------------|----------------|
| `credentials.json` | ⚠️ Medium | ✅ Yes |
| `token.json` | 🔴 High | ✅ Yes |
| `.env` | 🔴 High | ✅ Yes |

### If Credentials Leak

**credentials.json leaked:**
1. Go to: https://console.cloud.google.com/apis/credentials
2. Delete the OAuth client
3. Create new one, download new credentials.json

**token.json leaked:**
1. Go to: https://myaccount.google.com/permissions
2. Find "Calendar Parser"
3. Click "Remove access"
4. Delete `token.json` and re-authorize

**GEMINI_API_KEY leaked:**
1. Go to: https://aistudio.google.com/app/apikey
2. Delete compromised key
3. Create new key
4. Update `.env` file

---

## 💡 Tips

1. **Keep credentials.json forever** - It doesn't expire
2. **token.json refreshes automatically** - Don't worry about expiration
3. **Test with --dry-run first** - Verify image processing works
4. **Use test calendar initially** - Set TEST_CALENDAR_ID in .env
5. **Backup token.json** - Saves re-authorization if lost

---

## 📚 Related Documentation

- `ENV_CONFIGURATION_GUIDE.md` - Environment variables setup
- `MODES_USAGE_GUIDE.md` - Operating modes explanation
- `README.md` - General project overview

---

**Last Updated:** January 20, 2026  
**Version:** 1.0
