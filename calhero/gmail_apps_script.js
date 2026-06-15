/**
 * Google Apps Script - Email to Calendar Parser
 * ==============================================
 * 
 * This script:
 * 1. Runs when shift worker emails schedule screenshot
 * 2. Extracts attachment from email
 * 3. Sends to Cloud Run service
 * 4. Processes and adds to calendar
 * 
 * Setup Instructions:
 * 1. Go to script.google.com
 * 2. Create new project
 * 3. Copy this code
 * 4. Update CLOUD_RUN_URL with your service URL
 * 5. Set up trigger (see bottom of file)
 * 
 * Gmail Filter Setup:
 * - From: sender@example.com
 * - Has: attachment
 * - Subject contains: "schedule"
 * - Apply label: "Schedule/ToProcess"
 */

// ========================================
// CONFIGURATION
// ========================================

// IMPORTANT: Replace with your Cloud Run service URL
const CLOUD_RUN_URL = 'https://calhero-xxxxx-uc.a.run.app';  // ← YOUR URL HERE

// Gmail label to watch (create this in Gmail)
const WATCH_LABEL = 'Schedule/ToProcess';
const PROCESSED_LABEL = 'Schedule/Processed';

// Sender email (email address of the shift worker)
const ALLOWED_SENDER = 'sender@example.com'; // ← SHIFT WORKER EMAIL HERE

// Max age of emails to process (hours)
const MAX_EMAIL_AGE_HOURS = 24;

// OPTIONAL: Override calendar ID (leave empty to use Cloud Run default)
// This allows you to switch between test/prod calendars without updating Cloud Run!
// Example: 'abc123...@group.calendar.google.com'
const CALENDAR_ID_OVERRIDE = '';


// ========================================
// MAIN PROCESSING FUNCTION
// ========================================

/**
 * Main function - processes unread emails with schedule attachments.
 * This function should be triggered by:
 * - Time-driven trigger (every 5 minutes)
 * - OR Gmail addon trigger (real-time)
 */
function processScheduleEmails() {
  Logger.log('🔍 Checking for new schedule emails...');
  
  try {
    // Get the labels (create if they don't exist)
    const watchLabel = getOrCreateLabel(WATCH_LABEL);
    const processedLabel = getOrCreateLabel(PROCESSED_LABEL);
    
    // Build search query
    const maxAge = new Date();
    maxAge.setHours(maxAge.getHours() - MAX_EMAIL_AGE_HOURS);
    const maxAgeStr = Utilities.formatDate(maxAge, Session.getScriptTimeZone(), 'yyyy/MM/dd');
    
    const query = `from:${ALLOWED_SENDER} ` +
                  `has:attachment ` +
                  `label:${WATCH_LABEL} ` +
                  `-label:${PROCESSED_LABEL} ` +
                  `after:${maxAgeStr}`;
    
    Logger.log(`Search query: ${query}`);
    
    // Search for matching threads
    const threads = GmailApp.search(query, 0, 10);
    
    if (threads.length === 0) {
      Logger.log('✅ No new schedule emails found');
      return;
    }
    
    Logger.log(`📧 Found ${threads.length} email(s) to process`);
    
    // Process each thread
    for (const thread of threads) {
      const messages = thread.getMessages();
      
      for (const message of messages) {
        processMessage(message, processedLabel);
      }
      
      // Mark thread as processed
      thread.removeLabel(watchLabel);
      thread.addLabel(processedLabel);
      thread.markRead();
    }
    
    Logger.log('✅ Processing complete!');
    
  } catch (error) {
    Logger.log(`❌ Error: ${error.message}`);
    Logger.log(error.stack);
    
    // Send error notification email (optional)
    sendErrorNotification(error);
  }
}


/**
 * Processes a single email message and extracts attachments.
 */
function processMessage(message, processedLabel) {
  const subject = message.getSubject();
  const from = message.getFrom();
  const date = message.getDate();
  
  Logger.log(`  📨 Processing: "${subject}" from ${from}`);
  
  // Validate sender
  if (!from.includes(ALLOWED_SENDER)) {
    Logger.log(`  ⚠️  Skipping: Not from allowed sender`);
    return;
  }
  
  // Get attachments
  const attachments = message.getAttachments();
  
  if (attachments.length === 0) {
    Logger.log(`  ⚠️  No attachments found`);
    return;
  }
  
  // Process each attachment
  for (const attachment of attachments) {
    const filename = attachment.getName().toLowerCase();
    
    // Check if it's an image
    if (filename.endsWith('.png') || 
        filename.endsWith('.jpg') || 
        filename.endsWith('.jpeg')) {
      
      Logger.log(`  📎 Found image: ${attachment.getName()}`);
      sendToCloudRun(attachment, message);
    }
  }
}


/**
 * Sends attachment to Cloud Run service for processing.
 */
function sendToCloudRun(attachment, message) {
  try {
    // Get attachment data
    const blob = attachment.copyBlob();
    const bytes = blob.getBytes();
    const base64 = Utilities.base64Encode(bytes);
    
    // Prepare payload
    const payload = {
      image_base64: base64,
      image_name: attachment.getName(),
      metadata: {
        email_subject: message.getSubject(),
        email_date: message.getDate().toISOString(),
        email_from: message.getFrom()
      }
    };
    
    // Build URL with optional calendar_id override
    let url = CLOUD_RUN_URL;
    if (CALENDAR_ID_OVERRIDE) {
      url += `?calendar_id=${encodeURIComponent(CALENDAR_ID_OVERRIDE)}`;
      Logger.log(`  📅 Using calendar override: ${CALENDAR_ID_OVERRIDE}`);
    }
    
    // Send to Cloud Run
    Logger.log(`  🚀 Sending to Cloud Run...`);
    
    const options = {
      method: 'post',
      contentType: 'application/json',
      payload: JSON.stringify(payload),
      muteHttpExceptions: true
    };
    
    const response = UrlFetchApp.fetch(url, options);
    const responseCode = response.getResponseCode();
    const responseText = response.getContentText();
    
    Logger.log(`  📡 Response code: ${responseCode}`);
    
    if (responseCode === 200) {
      const result = JSON.parse(responseText);
      Logger.log(`  ✅ Success! Created ${result.shifts_created} shift(s)`);
      Logger.log(`  📊 Parser used: ${result.parser}`);
      if (result.calendar_source) {
        Logger.log(`  📅 Calendar source: ${result.calendar_source}`);
      }
      
      // Optional: Reply to sender with success message
      if (result.shifts_created > 0) {
        sendSuccessReply(message, result);
      }
    } else {
      Logger.log(`  ❌ Error: ${responseText}`);
      throw new Error(`Cloud Run returned ${responseCode}: ${responseText}`);
    }
    
  } catch (error) {
    Logger.log(`  ❌ Failed to send to Cloud Run: ${error.message}`);
    throw error;
  }
}


// ========================================
// HELPER FUNCTIONS
// ========================================

/**
 * Gets or creates a Gmail label.
 */
function getOrCreateLabel(labelName) {
  let label = GmailApp.getUserLabelByName(labelName);
  
  if (!label) {
    Logger.log(`Creating label: ${labelName}`);
    label = GmailApp.createLabel(labelName);
  }
  
  return label;
}


/**
 * Sends error notification email.
 */
function sendErrorNotification(error) {
  const recipient = Session.getActiveUser().getEmail();
  const subject = '❌ Calendar Parser Error';
  const body = `
Error processing schedule email:

${error.message}

Stack trace:
${error.stack}

Time: ${new Date().toISOString()}
  `.trim();
  
  try {
    MailApp.sendEmail(recipient, subject, body);
  } catch (e) {
    Logger.log(`Failed to send error notification: ${e.message}`);
  }
}


/**
 * Sends success reply to original sender.
 */
function sendSuccessReply(message, result) {
  try {
    const replyBody = `
Hi! Your schedule has been processed ✅

📊 Results:
- Shifts added: ${result.shifts_created}
- Parser used: ${result.parser}
- Image: ${result.image_name}

Check your calendar to see the updated schedule!

---
Automated message from Calendar Parser
    `.trim();
    
    message.reply(replyBody);
    Logger.log(`  💌 Sent success reply to sender`);
    
  } catch (error) {
    Logger.log(`  ⚠️  Could not send reply: ${error.message}`);
  }
}


// ========================================
// MANUAL TESTING
// ========================================

/**
 * Test function - manually trigger processing.
 * Run this from the Apps Script editor to test.
 */
function testProcessing() {
  Logger.log('🧪 Manual test started');
  processScheduleEmails();
  Logger.log('🧪 Test complete - check logs above');
}


/**
 * Test function - check configuration.
 */
function testConfiguration() {
  Logger.log('🔧 Configuration Test');
  Logger.log('====================');
  Logger.log(`Cloud Run URL: ${CLOUD_RUN_URL}`);
  Logger.log(`Allowed sender: ${ALLOWED_SENDER}`);
  Logger.log(`Watch label: ${WATCH_LABEL}`);
  Logger.log(`Processed label: ${PROCESSED_LABEL}`);
  Logger.log(`Calendar override: ${CALENDAR_ID_OVERRIDE || '(none - using Cloud Run default)'}`);
  Logger.log('');
  
  // Test Cloud Run endpoint
  Logger.log('Testing Cloud Run health endpoint...');
  try {
    const response = UrlFetchApp.fetch(CLOUD_RUN_URL + '/health');
    const result = JSON.parse(response.getContentText());
    Logger.log(`✅ Health check passed: ${JSON.stringify(result)}`);
  } catch (error) {
    Logger.log(`❌ Health check failed: ${error.message}`);
    Logger.log('Please verify your CLOUD_RUN_URL is correct');
  }
  
  // Check labels
  Logger.log('');
  Logger.log('Checking labels...');
  const watchLabel = getOrCreateLabel(WATCH_LABEL);
  const processedLabel = getOrCreateLabel(PROCESSED_LABEL);
  Logger.log(`✅ Labels ready: ${WATCH_LABEL}, ${PROCESSED_LABEL}`);
}


/**
 * Test function - send a test request to Cloud Run.
 */
function testCloudRunConnection() {
  Logger.log('🧪 Testing Cloud Run connection...');
  
  try {
    // Try health endpoint
    const healthResponse = UrlFetchApp.fetch(CLOUD_RUN_URL + '/health');
    Logger.log(`Health check: ${healthResponse.getContentText()}`);
    
    // Try info endpoint
    const infoResponse = UrlFetchApp.fetch(CLOUD_RUN_URL + '/info');
    Logger.log(`Service info: ${infoResponse.getContentText()}`);
    
    Logger.log('✅ Cloud Run connection successful!');
    
  } catch (error) {
    Logger.log(`❌ Connection failed: ${error.message}`);
    Logger.log('');
    Logger.log('Troubleshooting:');
    Logger.log('1. Verify CLOUD_RUN_URL is correct');
    Logger.log('2. Check Cloud Run service is deployed');
    Logger.log('3. Ensure service allows unauthenticated requests');
  }
}


// ========================================
// SETUP INSTRUCTIONS (COMMENT)
// ========================================

/*

SETUP STEPS:
============

1. UPDATE CONFIGURATION (lines 28-37):
   - Set CLOUD_RUN_URL to your Cloud Run service URL
   - Set ALLOWED_SENDER to the shift worker's email
   - Adjust labels if desired

2. TEST CONFIGURATION:
   - Run: testConfiguration()
   - Check logs for any errors

3. CREATE GMAIL FILTER:
   a. Go to Gmail settings → Filters
   b. Create new filter:
      - From: sender@example.com
      - Has attachment: yes
      - Subject contains: schedule (or whatever keyword)
   c. Filter actions:
      - Apply label: Schedule/ToProcess
      - Skip inbox (optional)
      - Mark as read (optional)

4. SET UP TRIGGER:
   a. In Apps Script editor, click Triggers (clock icon)
   b. Add trigger:
      - Function: processScheduleEmails
      - Event source: Time-driven
      - Type: Minutes timer
      - Interval: Every 5 minutes
   c. Save trigger

5. TEST:
   - Have the shift worker send a test email
   - Wait 5 minutes (or run testProcessing() manually)
   - Check logs and calendar

6. MONITOR:
   - Check logs regularly: View → Logs
   - Errors are logged and emailed to you

PERMISSIONS:
============
When you first run, Google will ask for permissions:
- Gmail: To read emails and labels
- URL Fetch: To call your Cloud Run service
- Calendar: Not needed (Cloud Run handles this)

Click "Review Permissions" and approve.

*/
