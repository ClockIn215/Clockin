"""
Shared Utilities for Calendar Parsers
=====================================
Common functionality used by both LLM and ML/OCR versions.

This module provides:
- Google Calendar authentication and service setup
- Duplicate event detection
- Configuration management
- File management utilities
"""

import os
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional
from dotenv import load_dotenv

from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

# Load environment variables from .env file
load_dotenv()


# ========================================
# CONFIGURATION
# ========================================

class Config:
    """Centralized configuration for calendar parsing."""
    
    # API Keys and Calendar IDs (loaded from environment variables)
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    CALENDAR_ID = os.getenv('CALENDAR_ID')
    TEST_CALENDAR_ID = os.getenv('TEST_CALENDAR_ID')
    
    # Timezone
    TIMEZONE = os.getenv('TIMEZONE', 'America/Chicago')
    
    # Directory paths
    SCREENSHOTS_DIR = Path("./screenshots")
    PROCESSED_DIR = SCREENSHOTS_DIR / "processed"
    
    # Event prefix (for easy identification)
    EVENT_PREFIX = os.getenv('EVENT_PREFIX', 'Odel shoola ')
    
    # Gemini LLM Settings
    GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-2.5-flash')
    GEMINI_TEMPERATURE = 0  # Deterministic output (0 = no randomness)
    
    GEMINI_PROMPT = """
    Extract ALL work shifts from this schedule image into a JSON array.
    For each shift, extract:
    - summary: The EXACT shift type from the image (e.g., "Coverage", "Training", etc.)
    - start: Start datetime in ISO format (YYYY-MM-DDTHH:MM:SS)
    - end: End datetime in ISO format (YYYY-MM-DDTHH:MM:SS)
    
    The year is 2026. Ignore 'No Shift' or 'Claim Shifts'.
    If a day has multiple shifts, include ALL of them.
    
    Format: [{"summary": "Coverage", "start": "2026-01-12T06:00:00", "end": "2026-01-12T14:30:00"}]
    """
    
    @classmethod
    def ensure_directories(cls):
        """Create necessary directories if they don't exist."""
        cls.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def get_active_calendar_id(cls, cli_override: Optional[str] = None) -> tuple:
        """
        Returns the active calendar ID and its source.
        
        Priority:
        1. CLI argument (--calendar-id)
        2. Environment variable (CALENDAR_ID)
        3. Raises error if not set
        
        Args:
            cli_override: Calendar ID from command-line argument
            
        Returns:
            (calendar_id, source) - The ID to use and where it came from
            
        Raises:
            ValueError: If no calendar ID is configured
        """
        # Check CLI override first
        if cli_override:
            return (cli_override, "CLI argument")
        
        # Check environment variable
        if cls.CALENDAR_ID:
            return (cls.CALENDAR_ID, "environment variable")
        
        # No calendar ID configured
        raise ValueError(
            "No calendar ID configured. Please set CALENDAR_ID in .env file "
            "or use --calendar-id argument"
        )
    
    @classmethod
    def log_calendar_selection(cls, calendar_id: str, source: str):
        """
        Log which calendar is being used (with partial masking for security).
        
        Args:
            calendar_id: The calendar ID being used
            source: Where the calendar ID came from (e.g., "CLI argument")
        """
        # Mask the middle part of the calendar ID for security
        if '@' in calendar_id:
            local, domain = calendar_id.split('@', 1)
            if len(local) > 8:
                masked = f"{local[:4]}...{local[-4:]}@{domain}"
            else:
                masked = f"{local[:2]}...{local[-2:]}@{domain}"
        else:
            masked = f"{calendar_id[:4]}...{calendar_id[-4:]}"
        
        print(f"📅 Using calendar: {masked} (from {source})")


# Initialize directories on import
Config.ensure_directories()


# ========================================
# GOOGLE CALENDAR INTEGRATION
# ========================================

def get_calendar_service():
    """
    Handles OAuth2 authentication and token management.
    
    Returns:
        Google Calendar API service object
        
    Raises:
        FileNotFoundError: If credentials.json is missing
    """
    scopes = ['https://www.googleapis.com/auth/calendar']
    creds = None
    
    # Check for credentials in multiple locations
    # Priority: mounted secrets (Cloud Run) > local files
    token_paths = [
        '/secrets/token/token.json',  # Cloud Run mounted secret
        'token.json'                  # Local development
    ]
    credentials_paths = [
        '/secrets/credentials/credentials.json',  # Cloud Run mounted secret
        'credentials.json'                        # Local development
    ]
    
    # Find token.json
    token_path = next((p for p in token_paths if os.path.exists(p)), None)
    
    # Find credentials.json
    credentials_path = next((p for p in credentials_paths if os.path.exists(p)), None)
    
    # Load existing credentials
    if token_path:
        creds = Credentials.from_authorized_user_file(token_path, scopes)
    
    # Refresh or obtain new credentials
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not credentials_path:
                raise FileNotFoundError(
                    "\n" + "=" * 70 + "\n"
                    "❌ Google Calendar API Credentials Missing\n"
                    "=" * 70 + "\n\n"
                    "Missing file: credentials.json\n\n"
                    "Checked locations:\n"
                    "  • /secrets/credentials/credentials.json (Cloud Run)\n"
                    "  • credentials.json (local)\n\n"
                    "Purpose:\n"
                    "  This file is required to access Google Calendar API for:\n"
                    "  • Checking for duplicate events\n"
                    "  • Creating calendar events\n\n"
                    "How to get it:\n"
                    "  1. Go to: https://console.cloud.google.com/apis/credentials\n"
                    "  2. Create project (or select existing)\n"
                    "  3. Enable 'Google Calendar API'\n"
                    "  4. Create OAuth 2.0 Client ID (Desktop app type)\n"
                    "  5. Download JSON file → Save as 'credentials.json'\n\n"
                    "Important notes:\n"
                    "  • This is SEPARATE from GEMINI_API_KEY (only needed for LLM version)\n"
                    "  • NOT required when using --dry-run flag\n"
                    "  • Will trigger browser login on first run (creates token.json)\n\n"
                    "Need help? See: CREDENTIALS_GUIDE.md\n"
                    "=" * 70
                )
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, scopes)
            creds = flow.run_local_server(port=0)
        
        # Save credentials for next run (local only)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    
    return build('calendar', 'v3', credentials=creds)


def is_duplicate(service, summary: str, start_iso: str, calendar_id: str = None) -> bool:
    """
    Checks if an event with the same summary and start time already exists.
    
    Args:
        service: Google Calendar API service object
        summary: Event title/summary
        start_iso: Event start time in ISO format
        calendar_id: Calendar ID (uses CALENDAR_ID from env if None)
        
    Returns:
        True if duplicate exists, False otherwise
    """
    if calendar_id is None:
        calendar_id = Config.CALENDAR_ID
        if not calendar_id:
            raise ValueError("CALENDAR_ID not configured in environment variables")
    
    start_dt = datetime.fromisoformat(start_iso)
    
    # Search within +/- 12 hours to catch the event regardless of timezone issues
    # This gives us a wide enough window while still being efficient
    time_min = (start_dt - timedelta(hours=12)).isoformat() + 'Z'
    time_max = (start_dt + timedelta(hours=12)).isoformat() + 'Z'
    
    try:
        events_result = service.events().list(
            calendarId=calendar_id,
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            q=summary  # Pre-filter by summary to reduce results
        ).execute()
        
        events = events_result.get('items', [])
        
        # Check for exact match on summary AND start time (within 5 minutes)
        for event in events:
            if event.get('summary') != summary:
                continue
            
            # Get event start time
            event_start = event.get('start', {}).get('dateTime', '')
            if not event_start:
                continue
            
            # Compare times (allow 5 minute difference to handle timezone/rounding)
            try:
                # Parse event datetime (handles both Z and timezone offset formats)
                event_dt = datetime.fromisoformat(event_start.replace('Z', '+00:00'))
                
                # Remove timezone info for naive comparison
                if event_dt.tzinfo:
                    event_dt = event_dt.replace(tzinfo=None)
                search_dt = start_dt.replace(tzinfo=None) if start_dt.tzinfo else start_dt
                
                # Calculate time difference
                time_diff = abs((event_dt - search_dt).total_seconds())
                
                # Allow up to 5 minutes difference (accounts for timezone/DST issues)
                if time_diff < 300:  # 5 minutes = 300 seconds
                    return True
            except (ValueError, AttributeError):
                continue
        
        return False
    except Exception as e:
        print(f"  ⚠️  Error checking for duplicates: {e}")
        return False


def create_calendar_event(service, summary: str, start_iso: str, end_iso: str, 
                         calendar_id: str = None, timezone: str = None) -> dict:
    """
    Creates a new calendar event.
    
    Args:
        service: Google Calendar API service object
        summary: Event title
        start_iso: Start time in ISO format
        end_iso: End time in ISO format
        calendar_id: Calendar ID (uses CALENDAR_ID from env if None)
        timezone: Timezone string (uses TIMEZONE from env if None)
        
    Returns:
        Created event object from Google Calendar API
    """
    if calendar_id is None:
        calendar_id = Config.CALENDAR_ID
        if not calendar_id:
            raise ValueError("CALENDAR_ID not configured in environment variables")
    if timezone is None:
        timezone = Config.TIMEZONE
    
    event = {
        'summary': summary,
        'start': {'dateTime': start_iso, 'timeZone': timezone},
        'end': {'dateTime': end_iso, 'timeZone': timezone},
    }
    
    return service.events().insert(calendarId=calendar_id, body=event).execute()


# ========================================
# FILE MANAGEMENT
# ========================================

def move_to_processed(file_path: Path, processed_dir: Path = None) -> Path:
    """
    Moves a file to the processed directory, handling name conflicts.
    
    Args:
        file_path: Path to file to move
        processed_dir: Destination directory (uses Config.PROCESSED_DIR if None)
        
    Returns:
        Path to the moved file
    """
    if processed_dir is None:
        processed_dir = Config.PROCESSED_DIR
    
    dest_path = processed_dir / file_path.name
    
    # Handle duplicate filenames by adding timestamp
    if dest_path.exists():
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        dest_path = processed_dir / f"{timestamp}_{file_path.name}"
    
    shutil.move(str(file_path), str(dest_path))
    return dest_path


def get_unprocessed_images(screenshots_dir: Path = None) -> list:
    """
    Gets list of unprocessed image files.
    
    Args:
        screenshots_dir: Directory to search (uses Config.SCREENSHOTS_DIR if None)
        
    Returns:
        List of Path objects for PNG and JPG files
    """
    if screenshots_dir is None:
        screenshots_dir = Config.SCREENSHOTS_DIR
    
    return (list(screenshots_dir.glob("*.png")) + 
            list(screenshots_dir.glob("*.jpg")) +
            list(screenshots_dir.glob("*.jpeg")))


# ========================================
# SHIFT DATA NORMALIZATION
# ========================================

def normalize_shift(shift: dict, add_prefix: bool = True) -> dict:
    """
    Normalizes shift data structure and adds event prefix if needed.
    
    Args:
        shift: Dictionary with 'summary', 'start', 'end' keys
        add_prefix: Whether to add Config.EVENT_PREFIX to summary
        
    Returns:
        Normalized shift dictionary
    """
    summary = shift['summary']
    if add_prefix and not summary.startswith(Config.EVENT_PREFIX):
        summary = Config.EVENT_PREFIX + summary
    
    return {
        'summary': summary,
        'start': shift['start'],
        'end': shift['end']
    }


def format_shift_summary(shifts: list) -> str:
    """
    Creates a human-readable summary of shifts.
    
    Args:
        shifts: List of shift dictionaries
        
    Returns:
        Formatted string summary
    """
    if not shifts:
        return "No shifts found"
    
    lines = [f"Found {len(shifts)} shift(s):"]
    for i, shift in enumerate(shifts, 1):
        start = datetime.fromisoformat(shift['start'])
        end = datetime.fromisoformat(shift['end'])
        duration = (end - start).total_seconds() / 3600
        lines.append(
            f"  {i}. {shift['summary']}: "
            f"{start.strftime('%a %m/%d %I:%M%p')} - {end.strftime('%I:%M%p')} "
            f"({duration:.1f}h)"
        )
    return "\n".join(lines)
