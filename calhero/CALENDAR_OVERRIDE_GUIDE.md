# Calendar Override Feature Guide

## Overview

The calendar override feature allows **Apps Script to override the `CALENDAR_ID`** set in Cloud Run, without needing to update or redeploy the Cloud Run service!

**Benefits:**
- ✅ Switch calendars instantly (no `gcloud` commands needed!)
- ✅ Different users can target different calendars
- ✅ Easy A/B testing between calendars
- ✅ Flexible configuration at the Apps Script level

---

## 🎯 How It Works

### Priority Order

The system determines which calendar to use in this order:

1. **Apps Script Parameter** (highest priority) ← New feature!
2. **Cloud Run Environment Variable** (`CALENDAR_ID`)
3. **Error** if neither is set

```
Apps Script passes calendar_id
    ↓
Cloud Run receives it as query parameter
    ↓
Overrides CALENDAR_ID environment variable
    ↓
Events created in Apps Script's calendar!
```

---

## 📝 Implementation

### Already Implemented!

This feature is **already built into the code**:

**In `cloud_run_service.py` (line 149):**
```python
calendar_id_override = request.args.get('calendar_id')
try:
    calendar_id, source = Config.get_active_calendar_id(calendar_id_override)
    print(f"📅 Using calendar from {source}")
```

**In `gmail_apps_script.js` (updated):**
```javascript
// New configuration option
const CALENDAR_ID_OVERRIDE = 'your-calendar-id@group.calendar.google.com';

// Automatically adds to URL
if (CALENDAR_ID_OVERRIDE) {
  url += `?calendar_id=${encodeURIComponent(CALENDAR_ID_OVERRIDE)}`;
}
```

---

## 🚀 Usage

### Option 1: Set in Apps Script Configuration

**Edit `gmail_apps_script.js`:**

```javascript
// At the top of the file
const CALENDAR_ID_OVERRIDE = 'your-calendar-id@group.calendar.google.com';
```

That's it! All emails processed by this Apps Script will now use this calendar.

**To switch calendars:**
1. Update the `CALENDAR_ID_OVERRIDE` value in Apps Script
2. Save
3. Done! Next email will use the new calendar
4. **No Cloud Run changes needed!**

### Option 2: Dynamic Per-Email Override

**For advanced use cases**, modify the `sendToCloudRun` function:

```javascript
function sendToCloudRun(attachment, message) {
  // ... existing code ...
  
  // Determine calendar based on email content
  let calendarId = '';
  const subject = message.getSubject().toLowerCase();
  
  if (subject.includes('personal')) {
    calendarId = 'personal-calendar@group.calendar.google.com';
  } else if (subject.includes('work')) {
    calendarId = 'work-calendar@group.calendar.google.com';
  }
  // else: use Cloud Run default
  
  // Build URL with calendar override
  let url = CLOUD_RUN_URL;
  if (calendarId) {
    url += `?calendar_id=${encodeURIComponent(calendarId)}`;
    Logger.log(`  📅 Using calendar: ${calendarId}`);
  }
  
  // ... rest of function ...
}
```

---

## 💡 Use Cases

### Use Case 1: Multiple Users, One Cloud Run Service

**Scenario:** Two people share one Cloud Run deployment, but want events in different calendars.

**Solution:**
- Person 1's Apps Script: `CALENDAR_ID_OVERRIDE = 'person1-calendar@...'`
- Person 2's Apps Script: `CALENDAR_ID_OVERRIDE = 'person2-calendar@...'`
- Both use the same Cloud Run URL!

### Use Case 2: Test vs Production Calendars

**Scenario:** Want to test with a test calendar, then switch to production.

**Solution:**
```javascript
// Testing phase
const CALENDAR_ID_OVERRIDE = 'test-calendar@group.calendar.google.com';

// After testing, change to:
const CALENDAR_ID_OVERRIDE = 'production-calendar@group.calendar.google.com';
```

**No Cloud Run update needed!**

### Use Case 3: Multiple Calendars Based on Content

**Scenario:** Different schedules go to different calendars based on email subject.

**Solution:**
```javascript
function determineCalendar(message) {
  const subject = message.getSubject().toLowerCase();
  
  if (subject.includes('morning')) {
    return 'morning-shifts@group.calendar.google.com';
  } else if (subject.includes('evening')) {
    return 'evening-shifts@group.calendar.google.com';
  }
  
  return ''; // Use Cloud Run default
}

function sendToCloudRun(attachment, message) {
  const calendarId = determineCalendar(message);
  let url = CLOUD_RUN_URL;
  
  if (calendarId) {
    url += `?calendar_id=${encodeURIComponent(calendarId)}`;
  }
  
  // ... rest of function ...
}
```

### Use Case 4: Fallback Pattern

**Scenario:** Try test calendar first, fall back to production if test is unavailable.

**Solution:**
```javascript
// In Cloud Run, set: CALENDAR_ID=production-calendar@...
// In Apps Script:
const CALENDAR_ID_OVERRIDE = 'test-calendar@group.calendar.google.com';

// If test calendar has issues, comment out the override:
// const CALENDAR_ID_OVERRIDE = '';  // Now uses production from Cloud Run
```

---

## 🆚 Comparison: Cloud Run vs Apps Script Override

| Aspect | Cloud Run Env Var | Apps Script Override |
|--------|-------------------|---------------------|
| **Change Process** | `gcloud run services update` | Edit Apps Script |
| **Speed** | Slow (redeploy) | ⚡ Instant (just save) |
| **Affects** | All requests | Only this Apps Script |
| **Best For** | Default calendar | User-specific calendars |
| **Requires** | gcloud CLI | Just a browser |
| **Downtime** | Brief during update | ❌ None |

**Recommendation:** 
- Set a **safe default** in Cloud Run (`CALENDAR_ID`)
- Use **Apps Script override** for flexibility

---

## 📊 Configuration Examples

### Example 1: Simple Override

**Cloud Run:**
```bash
gcloud run deploy calhero \
  --set-env-vars CALENDAR_ID=default-calendar@group.calendar.google.com
```

**Apps Script:**
```javascript
const CALENDAR_ID_OVERRIDE = 'my-personal-calendar@group.calendar.google.com';
```

**Result:** Events go to `my-personal-calendar@...` (Apps Script wins!)

### Example 2: No Override (Use Default)

**Cloud Run:**
```bash
gcloud run deploy calhero \
  --set-env-vars CALENDAR_ID=production-calendar@group.calendar.google.com
```

**Apps Script:**
```javascript
const CALENDAR_ID_OVERRIDE = '';  // Empty = use Cloud Run default
```

**Result:** Events go to `production-calendar@...` (Cloud Run default)

### Example 3: Testing via curl

```bash
# Use Cloud Run default
curl -X POST $SERVICE_URL -F "image=@schedule.png"

# Override to test calendar
curl -X POST "$SERVICE_URL?calendar_id=test-calendar@group.calendar.google.com" \
  -F "image=@schedule.png"

# Override to different calendar
curl -X POST "$SERVICE_URL?calendar_id=other-calendar@group.calendar.google.com" \
  -F "image=@schedule.png"
```

---

## 🔧 How to Enable This Feature

### Already Enabled!

No changes needed to Cloud Run! The feature is already implemented.

### To Use in Apps Script:

1. **Open your Apps Script** (script.google.com)

2. **Find the configuration section** (around line 30)

3. **Add your calendar ID:**
   ```javascript
   const CALENDAR_ID_OVERRIDE = 'your-calendar-id@group.calendar.google.com';
   ```

4. **Save** (Ctrl+S or Cmd+S)

5. **Test:**
   ```javascript
   // Run this function
   function testConfiguration() { ... }
   ```

6. **Check logs:**
   - Should show: `Calendar override: your-calendar-id@...`

7. **Done!** Next email will use your calendar.

---

## 🧪 Testing the Override

### Test 1: Verify Configuration

```javascript
function testConfiguration() {
  Logger.log('Calendar override: ' + CALENDAR_ID_OVERRIDE);
  // Should show your calendar ID
}
```

### Test 2: Check Cloud Run Response

```javascript
function testCloudRunWithOverride() {
  const testUrl = CLOUD_RUN_URL + '/health';
  
  // Test default
  Logger.log('Testing default:');
  const response1 = UrlFetchApp.fetch(testUrl);
  Logger.log(response1.getContentText());
  
  // Test with override
  Logger.log('Testing with override:');
  const calendarId = 'test-calendar@group.calendar.google.com';
  const response2 = UrlFetchApp.fetch(
    `${testUrl}?calendar_id=${encodeURIComponent(calendarId)}`
  );
  Logger.log(response2.getContentText());
}
```

### Test 3: Send Test Email

1. Send test email with schedule
2. Check Apps Script logs:
   ```
   📅 Using calendar override: your-calendar@...
   ✅ Success! Created 5 shift(s)
   📅 Calendar source: CLI argument
   ```
3. Verify events appear in the override calendar

---

## 🔍 Troubleshooting

### Issue: Override Not Working

**Symptom:** Events still go to Cloud Run default calendar

**Check:**
1. Verify `CALENDAR_ID_OVERRIDE` is not empty
2. Check Apps Script logs for calendar override message
3. Verify calendar ID format (must include `@group.calendar.google.com`)

**Debug:**
```javascript
function debugCalendarOverride() {
  Logger.log('Override value: "' + CALENDAR_ID_OVERRIDE + '"');
  Logger.log('Is empty? ' + (CALENDAR_ID_OVERRIDE === ''));
  Logger.log('Length: ' + CALENDAR_ID_OVERRIDE.length);
}
```

### Issue: "Calendar not found" Error

**Cause:** Invalid calendar ID or no access

**Fix:**
1. Verify calendar ID is correct
2. Share calendar with Cloud Run service account:
   - Get service account: `PROJECT_NUMBER-compute@developer.gserviceaccount.com`
   - Google Calendar → Settings → Share → Add service account
   - Permission: "Make changes to events"

### Issue: URL Encoding Issues

**Symptom:** Special characters in calendar ID break the request

**Fix:** Already handled! The code uses `encodeURIComponent()`:
```javascript
url += `?calendar_id=${encodeURIComponent(CALENDAR_ID_OVERRIDE)}`;
```

---

## 📚 Related Documentation

- **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** - Complete deployment guide
- **[OPTION3_DEPLOYMENT.md](OPTION3_DEPLOYMENT.md)** - Apps Script setup
- **[ENV_CONFIGURATION_GUIDE.md](ENV_CONFIGURATION_GUIDE.md)** - Environment variables
- **[cloud_run_service.py](cloud_run_service.py)** - Implementation code

---

## ✅ Summary

### What You Asked For:
> "Can Apps Script override CALENDAR_ID without updating Cloud Run?"

### Answer: YES! ✅

**It's already implemented!** Just set:

```javascript
const CALENDAR_ID_OVERRIDE = 'your-calendar@group.calendar.google.com';
```

### Benefits:
- ✅ **No `gcloud` commands** needed
- ✅ **Instant** calendar switching
- ✅ **Per-user** calendars possible
- ✅ **Dynamic** calendar selection
- ✅ **Zero downtime** changes

### Priority:
1. Apps Script override (highest)
2. Cloud Run `CALENDAR_ID` env var
3. Error if neither set

**Start using it now - no Cloud Run changes required!** 🎉
