# Calendar Override Feature - Summary

## ✅ Your Question Answered

**Q:** Can Apps Script override `CALENDAR_ID` without updating the Cloud Run container?

**A:** YES! This feature is **already implemented** and ready to use! 🎉

---

## 🚀 How to Use It

### In Your Apps Script

Edit `gmail_apps_script.js` and add:

```javascript
// At line 43 (already added in the updated file)
const CALENDAR_ID_OVERRIDE = 'your-calendar-id@group.calendar.google.com';
```

That's it! No Cloud Run changes needed.

---

## 📝 What Was Updated

### 1. **gmail_apps_script.js** - Updated

**Added:**
- `CALENDAR_ID_OVERRIDE` configuration variable
- Automatic URL parameter construction
- Calendar source logging

**Changes:**
```javascript
// NEW: Configuration option
const CALENDAR_ID_OVERRIDE = '';

// NEW: Adds calendar_id to URL if override is set
let url = CLOUD_RUN_URL;
if (CALENDAR_ID_OVERRIDE) {
  url += `?calendar_id=${encodeURIComponent(CALENDAR_ID_OVERRIDE)}`;
  Logger.log(`  📅 Using calendar override: ${CALENDAR_ID_OVERRIDE}`);
}

// NEW: Logs calendar source in response
if (result.calendar_source) {
  Logger.log(`  📅 Calendar source: ${result.calendar_source}`);
}
```

### 2. **cloud_run_service.py** - Already Had This!

**Lines 149-152** already implemented:
```python
calendar_id_override = request.args.get('calendar_id')
try:
    calendar_id, source = Config.get_active_calendar_id(calendar_id_override)
    print(f"📅 Using calendar from {source}")
```

The backend was ready - we just exposed it in the Apps Script!

### 3. **CALENDAR_OVERRIDE_GUIDE.md** - New!

Complete guide covering:
- How it works
- Use cases (multi-user, test/prod, dynamic routing)
- Configuration examples
- Testing procedures
- Troubleshooting

### 4. **DEPLOYMENT_GUIDE.md** - Updated

Added section showing Apps Script override as recommended alternative to `gcloud run services update`.

### 5. **OPTION3_DEPLOYMENT.md** - Updated

Added `CALENDAR_ID_OVERRIDE` to configuration instructions.

---

## 🎯 Priority Order

The system determines which calendar to use:

1. **Apps Script Parameter** (highest) ← Your question!
2. **Cloud Run Env Var** (`CALENDAR_ID`)
3. **Error** if neither set

```
┌─────────────────────┐
│   Apps Script       │
│   CALENDAR_ID_      │  ← Overrides Cloud Run!
│   OVERRIDE = '...'  │
└──────────┬──────────┘
           │
           ↓
    ?calendar_id=...
           │
           ↓
┌──────────┴──────────┐
│   Cloud Run         │
│   receives request  │
│   with parameter    │
└──────────┬──────────┘
           │
           ↓
  Uses Apps Script calendar
  (ignores CALENDAR_ID env var)
```

---

## 💡 Use Cases

### Use Case 1: Your Exact Request

**Scenario:** You want to switch calendars without running `gcloud run services update`

**Solution:**
```javascript
// In Apps Script - just edit and save!
const CALENDAR_ID_OVERRIDE = 'test-calendar@group.calendar.google.com';

// Later, switch to production:
const CALENDAR_ID_OVERRIDE = 'prod-calendar@group.calendar.google.com';

// Or use Cloud Run default:
const CALENDAR_ID_OVERRIDE = '';
```

**No Cloud Run changes needed!** ✅

### Use Case 2: Multiple Users, One Deployment

**Scenario:** Multiple shift workers use the same Cloud Run, but different calendars

**Solution:**
- Worker 1's Apps Script: `CALENDAR_ID_OVERRIDE = 'worker1-calendar@...'`
- Worker 2's Apps Script: `CALENDAR_ID_OVERRIDE = 'worker2-calendar@...'`
- Cloud Run: One deployment serves both!

### Use Case 3: Dynamic Routing

**Scenario:** Route to different calendars based on email content

**Solution:**
```javascript
function determineCalendar(message) {
  const subject = message.getSubject().toLowerCase();
  if (subject.includes('personal')) return 'personal-cal@...';
  if (subject.includes('work')) return 'work-cal@...';
  return ''; // Cloud Run default
}

// Then use it in sendToCloudRun()
```

---

## 🆚 Comparison

| Method | Speed | Requires | Affects | Best For |
|--------|-------|----------|---------|----------|
| **Apps Script Override** | ⚡ Instant | Edit script | This script only | ✅ **Recommended!** |
| **gcloud update** | 🕐 Slow | gcloud CLI | All requests | Default/fallback |
| **Rebuild image** | 🐌 Very slow | Docker build | All requests | ❌ Not needed |

---

## 📊 Examples

### Example 1: Simple Override

**Cloud Run deployment:**
```bash
gcloud run deploy calhero \
  --set-env-vars CALENDAR_ID=default-calendar@group.calendar.google.com
```

**Apps Script:**
```javascript
const CALENDAR_ID_OVERRIDE = 'my-calendar@group.calendar.google.com';
```

**Result:** Events go to `my-calendar@...` (Apps Script wins!)

### Example 2: No Override

**Cloud Run:**
```bash
gcloud run deploy calhero \
  --set-env-vars CALENDAR_ID=production-calendar@group.calendar.google.com
```

**Apps Script:**
```javascript
const CALENDAR_ID_OVERRIDE = '';  // Empty
```

**Result:** Events go to `production-calendar@...` (Cloud Run default)

### Example 3: Testing Both

```javascript
// Test with override
const CALENDAR_ID_OVERRIDE = 'test-calendar@group.calendar.google.com';
// Run test email

// Then test without override
const CALENDAR_ID_OVERRIDE = '';
// Run another test email (uses Cloud Run default)
```

---

## 🧪 Testing

### Quick Test

1. **Update Apps Script:**
   ```javascript
   const CALENDAR_ID_OVERRIDE = 'your-test-calendar@group.calendar.google.com';
   ```

2. **Save** (Ctrl+S)

3. **Run test:**
   ```javascript
   function testConfiguration() { ... }
   ```

4. **Check logs:**
   ```
   Calendar override: your-test-calendar@group.calendar.google.com
   ```

5. **Send test email** and verify events appear in test calendar

6. **Change back:**
   ```javascript
   const CALENDAR_ID_OVERRIDE = '';  // Back to Cloud Run default
   ```

---

## ✅ Benefits

### For You:
- ✅ **No `gcloud` commands** - Just edit Apps Script
- ✅ **Instant switching** - Save and done
- ✅ **Easy testing** - Switch between test/prod calendars
- ✅ **Zero downtime** - No service restarts
- ✅ **Per-user calendars** - Different calendars per script

### Technical:
- ✅ **Already implemented** - No code changes needed
- ✅ **Works out-of-box** - Just set the variable
- ✅ **Priority system** - Apps Script > Cloud Run > Error
- ✅ **Logged** - Shows calendar source in logs
- ✅ **URL-safe** - Properly encoded

---

## 📚 Documentation Files

| File | Purpose |
|------|---------|
| **CALENDAR_OVERRIDE_GUIDE.md** | Complete feature guide |
| **gmail_apps_script.js** | Updated with override support |
| **DEPLOYMENT_GUIDE.md** | Shows override as option B |
| **OPTION3_DEPLOYMENT.md** | Configuration instructions |
| **cloud_run_service.py** | Backend implementation (unchanged) |

---

## 🎉 Summary

### What You Wanted:
> "Apps Script override CALENDAR_ID without updating gcloud run container"

### What You Got:
✅ **Feature is already implemented!**
✅ **Apps Script updated to use it**
✅ **Complete documentation**
✅ **Multiple use cases covered**
✅ **Testing procedures**

### To Use:
1. Open `gmail_apps_script.js`
2. Set `CALENDAR_ID_OVERRIDE = 'your-calendar@...'`
3. Save
4. Done!

**No Cloud Run changes ever needed!** 🚀

---

## 🔗 Quick Links

- **[CALENDAR_OVERRIDE_GUIDE.md](CALENDAR_OVERRIDE_GUIDE.md)** - Complete guide
- **[gmail_apps_script.js](gmail_apps_script.js)** - Updated script
- **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** - Deployment options

---

**Start using it now - the feature is ready!** 🎉
