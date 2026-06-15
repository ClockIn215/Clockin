"""
Google Cloud Function Entry Point
==================================
Handles email-triggered calendar parsing.

Deployment:
    gcloud functions deploy parse_calendar_screenshot \
        --runtime python311 \
        --trigger-http \
        --allow-unauthenticated \
        --memory 1GB \
        --timeout 300s

Email Integration Options:
1. Gmail API + Cloud Pub/Sub (watch for emails)
2. SendGrid Inbound Parse
3. Mailgun Routes
4. AWS SES + Lambda (if using AWS)
"""

import os
import base64
import tempfile
from pathlib import Path
from typing import Dict, Any
import json

# Import your parsers
from calendar_utils import get_calendar_service, Config
from calhero_ml import process_image_with_ml
from calhero import process_image


def parse_calendar_screenshot(request) -> Dict[str, Any]:
    """
    Cloud Function entry point - HTTP trigger.
    
    Expects JSON payload:
    {
        "image_base64": "base64-encoded image data",
        "image_name": "schedule.png",
        "use_llm": false,  # optional, defaults to ML/OCR
        "calendar_id": "optional-calendar-id",  # optional, overrides env var
        "dry_run": false,  # optional, test processing only
        "check_only": false  # optional, read-only mode
    }
    
    Or multipart/form-data with 'image' field.
    """
    try:
        # Parse request
        calendar_id_override = None
        dry_run = False
        check_only = False
        
        if request.method == 'POST':
            # Check if JSON or form data
            if request.content_type == 'application/json':
                data = request.get_json()
                image_data = base64.b64decode(data.get('image_base64'))
                image_name = data.get('image_name', 'schedule.png')
                use_llm = data.get('use_llm', False)
                calendar_id_override = data.get('calendar_id')
                dry_run = data.get('dry_run', False)
                check_only = data.get('check_only', False)
            else:
                # Form data with file upload
                file = request.files.get('image')
                if not file:
                    return {'error': 'No image provided'}, 400
                image_data = file.read()
                image_name = file.filename
                use_llm = request.form.get('use_llm', 'false').lower() == 'true'
                calendar_id_override = request.form.get('calendar_id')
                dry_run = request.form.get('dry_run', 'false').lower() == 'true'
                check_only = request.form.get('check_only', 'false').lower() == 'true'
        else:
            return {'error': 'Only POST requests supported'}, 405
        
        # Validate flag combinations
        if dry_run and check_only:
            return {
                'success': False,
                'error': 'Cannot use dry_run and check_only together'
            }, 400
        
        # Get active calendar ID if needed
        if dry_run:
            calendar_id = None
            service = None
            mode = "dry-run"
        else:
            try:
                calendar_id, source = Config.get_active_calendar_id(calendar_id_override)
                print(f"📅 Using calendar from {source}")
            except ValueError as e:
                return {
                    'success': False,
                    'error': f'Configuration error: {str(e)}'
                }, 400
            service = get_calendar_service()
            mode = "check-only" if check_only else "normal"
        
        # Save image temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_file:
            tmp_file.write(image_data)
            tmp_path = Path(tmp_file.name)
        
        try:
            # Parse using selected method
            class Args:
                pass
            
            args = Args()
            args.dry_run = dry_run
            args.check_only = check_only
            args.force = False
            args.debug = False
            
            if use_llm:
                # Use LLM version (requires Gemini API)
                from google import genai
                client = genai.Client(api_key=Config.GEMINI_API_KEY)
                
                # Import process_image from calhero module
                created_count, would_create = process_image(service, client, tmp_path, args, calendar_id)
                method = 'LLM (Gemini)'
            else:
                # Use ML/OCR version (Tesseract)
                created_count, would_create = process_image_with_ml(service, tmp_path, args, calendar_id)
                method = 'ML/OCR (Tesseract)'
            
            # Success response
            response_data = {
                'success': True,
                'method': method,
                'image_name': image_name,
                'mode': mode
            }
            
            if dry_run or check_only:
                response_data['would_create'] = would_create
            else:
                response_data['shifts_created'] = created_count
                response_data['calendar_source'] = source
            
            return response_data, 200
            
        finally:
            # Cleanup temp file
            if tmp_path.exists():
                tmp_path.unlink()
    
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }, 500


def gmail_pubsub_trigger(event, context):
    """
    Cloud Function triggered by Gmail Pub/Sub push notifications.
    
    Setup:
    1. Enable Gmail API
    2. Set up Gmail Push Notifications
    3. Create Pub/Sub topic: gmail-calendar-screenshots
    4. Deploy this function with --trigger-topic gmail-calendar-screenshots
    
    The function:
    - Receives Gmail notification
    - Fetches email with attachment
    - Extracts screenshot
    - Processes with calendar parser
    """
    import base64
    from googleapiclient.discovery import build
    from google.oauth2.credentials import Credentials
    
    try:
        # Parse Pub/Sub message
        pubsub_message = base64.b64decode(event['data']).decode('utf-8')
        message_data = json.loads(pubsub_message)
        
        # Get email details
        email_address = message_data.get('emailAddress')
        history_id = message_data.get('historyId')
        
        print(f"Processing email notification for {email_address}, history {history_id}")
        
        # Build Gmail service
        # Note: You'll need to set up service account or OAuth credentials
        gmail_service = build('gmail', 'v1', credentials=get_gmail_credentials())
        
        # Fetch recent messages with attachments
        # Filter: from specific sender, has attachment, recent
        query = 'from:sender@example.com has:attachment newer_than:1h subject:"schedule"'
        
        results = gmail_service.users().messages().list(
            userId='me',
            q=query,
            maxResults=1
        ).execute()
        
        messages = results.get('messages', [])
        
        if not messages:
            print("No matching emails found")
            return {'status': 'no_emails'}, 200
        
        # Get first message
        message_id = messages[0]['id']
        message = gmail_service.users().messages().get(
            userId='me',
            id=message_id,
            format='full'
        ).execute()
        
        # Extract attachments
        for part in message['payload'].get('parts', []):
            if part.get('filename') and part['filename'].lower().endswith(('.png', '.jpg', '.jpeg')):
                attachment_id = part['body']['attachmentId']
                
                attachment = gmail_service.users().messages().attachments().get(
                    userId='me',
                    messageId=message_id,
                    id=attachment_id
                ).execute()
                
                # Decode attachment
                file_data = base64.urlsafe_b64decode(attachment['data'].encode('UTF-8'))
                
                # Process with calendar parser
                with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_file:
                    tmp_file.write(file_data)
                    tmp_path = Path(tmp_file.name)
                
                try:
                    # Get active calendar ID
                    calendar_id, source = Config.get_active_calendar_id()
                    print(f"📅 Using calendar from {source}")
                    
                    service = get_calendar_service()
                    
                    class Args:
                        dry_run = False
                        check_only = False
                        force = False
                        debug = False
                    
                    # Use ML version by default (free, no API cost)
                    created_count, _ = process_image_with_ml(service, tmp_path, Args(), calendar_id)
                    
                    print(f"Successfully processed {part['filename']}: {created_count} shifts created")
                    
                    # Optionally: Mark email as read, add label, etc.
                    gmail_service.users().messages().modify(
                        userId='me',
                        id=message_id,
                        body={'removeLabelIds': ['UNREAD'], 'addLabelIds': ['Label_Processed']}
                    ).execute()
                    
                    return {
                        'status': 'success',
                        'filename': part['filename'],
                        'shifts_created': created_count
                    }, 200
                    
                finally:
                    if tmp_path.exists():
                        tmp_path.unlink()
        
        return {'status': 'no_attachments'}, 200
        
    except Exception as e:
        print(f"Error processing email: {e}")
        return {'status': 'error', 'error': str(e)}, 500


def get_gmail_credentials():
    """
    Get Gmail API credentials.
    
    Options:
    1. Service Account (for org-wide access)
    2. OAuth2 (for personal Gmail)
    3. Domain-wide delegation (G Suite)
    """
    # Implementation depends on your setup
    # This is a placeholder
    pass


# For local testing
if __name__ == '__main__':
    from flask import Flask, request
    
    app = Flask(__name__)
    
    @app.route('/', methods=['POST'])
    def test():
        return parse_calendar_screenshot(request)
    
    app.run(port=8080, debug=True)
    print("Test server running on http://localhost:8080")
    print("\nTest with:")
    print("  curl -X POST http://localhost:8080 \\")
    print("    -F 'image=@screenshots/schedule.png' \\")
    print("    -F 'use_llm=false'")
