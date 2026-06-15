"""
Calendar Shift Parser - ML/OCR Version
======================================
This script demonstrates using traditional ML/OCR techniques instead of LLMs.

Key ML Concepts Used:
1. OCR (Optical Character Recognition) - Computer vision for text extraction
2. Image preprocessing - Enhancing images for better ML model performance  
3. Pattern recognition - Using regex and text analysis to extract structured data
4. Data normalization - Converting varied text formats into consistent structure

Libraries:
- pytesseract: OCR engine (uses LSTM neural networks internally)
- opencv-cv2: Image preprocessing (contrast, denoising, etc.)
- PIL: Image loading and manipulation
"""

import re
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional

# OCR and Image Processing
import pytesseract
from PIL import Image
import cv2
import numpy as np

# Import shared utilities
from calendar_utils import (
    Config,
    get_calendar_service,
    is_duplicate,
    create_calendar_event,
    move_to_processed,
    get_unprocessed_images,
    normalize_shift
)


# ========================================
# PART 1: IMAGE PREPROCESSING (ML TECHNIQUE)
# ========================================

def preprocess_image_for_ocr(image_path: Path, mode: str = 'standard') -> np.ndarray:
    """
    Preprocesses image to improve OCR accuracy.
    
    ML Concept: Feature engineering and data preprocessing
    - Increases contrast to make text more distinct
    - Removes noise that could confuse the OCR model
    - Converts to grayscale (reduces complexity, improves speed)
    
    Args:
        mode: 'standard' (default) or 'gentle' (preserves more detail for colored text)
    
    Returns: Preprocessed image as numpy array
    """
    # Load image using OpenCV
    img = cv2.imread(str(image_path))
    
    if mode == 'gentle':
        # Gentle preprocessing - better for white text on colored backgrounds
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Use adaptive thresholding instead of global threshold
        # This handles varying lighting better (like circles with different colors)
        binary = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 11, 2
        )
        
        # Light denoising
        denoised = cv2.medianBlur(binary, 3)
        
        return denoised
    else:
        # Standard preprocessing (current approach)
        # Convert to grayscale (reduces dimensionality from 3 channels to 1)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Apply thresholding (binarization) - makes text black on white background
        # This helps OCR models by increasing contrast
        _, binary = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Denoise using bilateral filter (preserves edges while smoothing)
        denoised = cv2.bilateralFilter(binary, 9, 75, 75)
        
        return denoised


# ========================================
# PART 2: OCR TEXT EXTRACTION (ML MODEL)
# ========================================

def extract_text_from_image(image_path: Path) -> str:
    """
    Uses OCR to extract text from image with multiple preprocessing strategies.
    
    ML Concept: Tesseract OCR uses LSTM (Long Short-Term Memory) neural networks
    - Trained on millions of text samples
    - Recognizes characters and words from pixel patterns
    - PSM 6 assumes uniform block of text (best for structured schedules)
    
    Strategy: Try both standard and gentle preprocessing, combine results
    
    Returns: Raw extracted text
    """
    print(f"  🔍 Running OCR on {image_path.name}...")
    
    # Strategy 1: Standard preprocessing (good for black text on white)
    preprocessed_standard = preprocess_image_for_ocr(image_path, mode='standard')
    
    # Strategy 2: Gentle preprocessing (better for colored backgrounds)
    preprocessed_gentle = preprocess_image_for_ocr(image_path, mode='gentle')
    
    # Configure Tesseract
    # PSM (Page Segmentation Mode) 6 = Assume uniform block of text
    # OEM (OCR Engine Mode) 3 = Default, uses LSTM neural network
    custom_config = r'--oem 3 --psm 6'
    
    # Run OCR with both strategies
    text_standard = pytesseract.image_to_string(preprocessed_standard, config=custom_config)
    text_gentle = pytesseract.image_to_string(preprocessed_gentle, config=custom_config)
    
    # Extract standalone numbers from gentle preprocessing (likely the circle numbers)
    gentle_numbers = re.findall(r'^\s*(\d{1,2})\s*$', text_gentle, re.MULTILINE)
    
    if gentle_numbers:
        print(f"  📍 Gentle preprocessing found standalone numbers: {gentle_numbers}")
        # Inject these numbers into the standard text near their corresponding day names
        # For now, just return standard text (we'll enhance this if needed)
        return text_standard
    
    return text_standard


# ========================================
# PART 3: TEXT PARSING (PATTERN RECOGNITION)
# ========================================

def parse_date_range_from_text(text: str) -> Optional[tuple]:
    """
    Extracts date range from header (e.g., "01/19/2026 - 01/25/2026").
    
    ML Concept: Pattern recognition using regex
    - Trained pattern (regex) to recognize date formats
    - Feature extraction: pulling specific info from unstructured text
    """
    # Regex pattern for date range: MM/DD/YYYY - MM/DD/YYYY
    pattern = r'(\d{2}/\d{2}/\d{4})\s*-\s*(\d{2}/\d{2}/\d{4})'
    match = re.search(pattern, text)
    
    if match:
        print(f"  🔍 Found date range in text: {match.group(0)}")
        start_date = datetime.strptime(match.group(1), '%m/%d/%Y')
        end_date = datetime.strptime(match.group(2), '%m/%d/%Y')
        return (start_date, end_date)
    
    print(f"  ⚠️  Date range pattern not found. Looking for format: MM/DD/YYYY - MM/DD/YYYY")
    return None


def parse_shift_from_line(line: str, week_start: datetime, fallback_date: Optional[datetime] = None) -> Optional[Dict]:
    """
    Parses a single line to extract shift information.
    
    ML Concept: Feature extraction and classification
    - Identifies key features (date, time, location, type)
    - Classifies line as shift vs. non-shift
    - Returns structured data (feature vector)
    
    Example line: "Mon 19  12:00 PM - 06:00 PM  5.50 hrs Coverage"
    
    Args:
        line: Text line to parse
        week_start: Start date of the week
        fallback_date: Date to use if no day name found (for multiple shifts same day)
    """
    # Skip non-shift lines
    if 'No Shift' in line or 'Claim Shifts' in line or not line.strip():
        return None
    
    # Pattern 1: Extract day name (and optionally date if present)
    # First, just look for the day name
    day_name_match = re.search(r'(Mon|Tue|Wed|Thu|Fri|Sat|Sun)', line)
    
    # Check if this is a time-only line (multiple shifts same day)
    time_pattern = r'(\d{1,2}):(\d{2})\s*(AM|PM)\s*-\s*(\d{1,2}):(\d{2})\s*(AM|PM)'
    has_time = re.search(time_pattern, line)
    
    if not day_name_match and has_time and fallback_date:
        # This is a second shift on the same day (no day name, but has time)
        print(f"  🔍 Line: '{line[:80]}'")
        print(f"  🔍 No day name - treating as additional shift on {fallback_date.strftime('%Y-%m-%d')}")
        shift_date = fallback_date
        day_name = None
        day_num = None
    elif not day_name_match:
        return None
    else:
        day_name = day_name_match.group(1)
    
        # Try to find a day number that's NOT part of the time
        # Look for day name followed by 1-2 digits that are NOT followed by ":" or part of time
        day_num_match = re.search(r'(Mon|Tue|Wed|Thu|Fri|Sat|Sun)\s+(\d{1,2})(?=\s+\d{1,2}:\d{2})', line)
        
        # If we found a day number that comes BEFORE the time, use it
        if day_num_match:
            day_num = int(day_num_match.group(2))
            print(f"  🔍 Line: '{line[:80]}'")
            print(f"  🔍 Extracted day name and date from line: {day_name} {day_num}")
        else:
            # FALLBACK: Calculate date from day of week and week range
            # This handles cases where OCR doesn't capture the day number
            day_num = None
            print(f"  🔍 Line: '{line[:80]}'")
            print(f"  🔍 Day number not in line, will calculate from day of week: {day_name}")
    
    # Pattern 2: Extract time range (e.g., "12:00 PM - 06:00 PM")
    time_pattern = r'(\d{1,2}):(\d{2})\s*(AM|PM)\s*-\s*(\d{1,2}):(\d{2})\s*(AM|PM)'
    time_match = re.search(time_pattern, line)
    if not time_match:
        return None
    
    #TODO: Remove this after testing
    print(f"  🔍 Extracted time range from line: {time_match.group(1)}:{time_match.group(2)} {time_match.group(3)} - {time_match.group(4)}:{time_match.group(5)} {time_match.group(6)}")
    # Parse start time
    start_hour = int(time_match.group(1))
    start_min = int(time_match.group(2))
    start_period = time_match.group(3)
    
    # Convert to 24-hour format
    if start_period == 'PM' and start_hour != 12:
        start_hour += 12
    elif start_period == 'AM' and start_hour == 12:
        start_hour = 0
    
    # Parse end time
    end_hour = int(time_match.group(4))
    end_min = int(time_match.group(5))
    end_period = time_match.group(6)
    
    if end_period == 'PM' and end_hour != 12:
        end_hour += 12
    elif end_period == 'AM' and end_hour == 12:
        end_hour = 0

    #TODO: Remove this after testing
    print(f"  🔍 Parsed start time: {start_hour}:{start_min} {start_period}")
    print(f"  🔍 Parsed end time: {end_hour}:{end_min} {end_period}")

    # Construct full datetime
    # Note: shift_date may already be set if this is a fallback_date scenario
    if 'shift_date' not in locals():
        shift_date = None
    
    if shift_date is None and day_num is not None:
        # Method 1: We have a day number, find matching date
        for offset in range(-7, 15):
            candidate = week_start + timedelta(days=offset)
            if candidate.day == day_num:
                shift_date = candidate
                break
        
        if shift_date is None:
            print(f"  ⚠️  Could not find date with day {day_num} near week start {week_start.strftime('%Y-%m-%d')}")
            # Fall through to method 2
    
    if shift_date is None and day_name is not None:
        # Method 2: Calculate from day of week
        # Map day names to weekday numbers (Monday=0, Sunday=6)
        day_map = {'Mon': 0, 'Tue': 1, 'Wed': 2, 'Thu': 3, 'Fri': 4, 'Sat': 5, 'Sun': 6}
        target_weekday = day_map.get(day_name)
        
        if target_weekday is not None:
            # Find the first occurrence of this weekday in the week range
            current = week_start
            for _ in range(14):  # Search up to 2 weeks
                if current.weekday() == target_weekday:
                    shift_date = current
                    print(f"  ✅ Calculated date from day of week: {day_name} = {shift_date.strftime('%Y-%m-%d')}")
                    break
                current += timedelta(days=1)
    
    if shift_date is None:
        print(f"  ⚠️  Could not determine date")
        return None
    
    start_datetime = shift_date.replace(hour=start_hour, minute=start_min, second=0)
    end_datetime = shift_date.replace(hour=end_hour, minute=end_min, second=0)
    
    print(f"  🔍 Parsed start datetime: {start_datetime}")

    # Handle overnight shifts (end time is next day)
    if end_datetime <= start_datetime:
        end_datetime += timedelta(days=1)
    
    # Pattern 3: Extract shift type (Coverage, Training, etc.)
    shift_type = "Coverage"  # Default
    if 'Training' in line:
        shift_type = "Training"
    elif 'Coverage' in line:
        shift_type = "Coverage"
    
    return {
        'summary': shift_type,
        'start': start_datetime.isoformat(),
        'end': end_datetime.isoformat()
    }


def extract_shifts_from_text(text: str) -> List[Dict]:
    """
    Main parser: Converts raw OCR text into structured shift data.
    
    ML Concept: Data structuring and normalization
    - Transforms unstructured text into structured JSON-like format
    - Filters noise and irrelevant data
    - Normalizes dates/times into ISO format
    
    Returns: List of shift dictionaries
    """
    shifts = []
    
    # Extract date range from header
    date_range = parse_date_range_from_text(text)
    if not date_range:
        print("  ⚠️  Could not extract date range from text")
        print("  📄 First 500 chars of text:")
        print(text[:500])
        return shifts
    
    week_start = date_range[0]
    week_end = date_range[1]
    print(f"  📅 Detected week: {week_start.strftime('%m/%d/%Y')} - {week_end.strftime('%m/%d/%Y')}")
    
    # Process each line
    lines = [line.strip() for line in text.split('\n')]
    print(f"  📝 Processing {len(lines)} lines of text...")
    
    # DEBUG: Show all lines to see if day numbers are present
    print("\n  📄 All OCR lines (showing first 100 chars):")
    for i, line in enumerate(lines[:50], 1):  # Show first 50 lines
        if line:
            # Highlight lines with just numbers (might be circled day numbers)
            if line.isdigit() and len(line) <= 2:
                print(f"    {i:2d}. ⭐ '{line}' (STANDALONE NUMBER)")
            else:
                print(f"    {i:2d}. '{line[:100]}'")
    print()
    
    # Try multi-line parsing: combine day name + day number + shift details
    # Track last parsed date for handling multiple shifts same day
    last_shift_date = None
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        if not line:
            i += 1
            continue
        
        # Check if current line has a day name
        if any(day in line for day in ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']):
            # Try to build a combined line from next few lines
            combined = line
            
            # Look ahead for day number (standalone number on next line)
            if i + 1 < len(lines) and lines[i + 1].strip().isdigit() and len(lines[i + 1].strip()) <= 2:
                combined += ' ' + lines[i + 1].strip()
                i += 1  # Skip the number line
            
            # Look ahead for time pattern (might be on next line)
            if i + 1 < len(lines) and re.search(r'\d{1,2}:\d{2}\s*(AM|PM)', lines[i + 1]):
                combined += ' ' + lines[i + 1].strip()
                i += 1  # Skip the time line
            
            # Try to parse the combined line
            shift = parse_shift_from_line(combined, week_start, last_shift_date)
            if shift:
                print(f"  ✅ Parsed shift: {shift['summary']} on {shift['start'][:10]}")
                shifts.append(shift)
                # Extract the date for potential same-day shifts
                last_shift_date = datetime.fromisoformat(shift['start'])
        else:
            # Check if this is a time-only line (second shift same day)
            if re.search(r'\d{1,2}:\d{2}\s*(AM|PM)', line):
                # Combine with next lines to get shift type and location
                combined = line
                
                # Look ahead for shift type (lines starting with @)
                lookahead = 1
                while i + lookahead < len(lines) and lookahead <= 3:
                    next_line = lines[i + lookahead].strip()
                    # Include lines with @ (shift type/location)
                    if next_line.startswith('@'):
                        combined += ' ' + next_line
                        i += 1  # Skip this line
                    elif not next_line or next_line.startswith('-'):
                        # Stop at empty lines or next shift
                        break
                    lookahead += 1
                
                shift = parse_shift_from_line(combined, week_start, last_shift_date)
                if shift:
                    print(f"  ✅ Parsed shift: {shift['summary']} on {shift['start'][:10]}")
                    shifts.append(shift)
                    # Keep the same last_shift_date for potential third shift
        
        i += 1
    
    print(f"  📊 Total shifts found: {len(shifts)}")
    return shifts


# ========================================
# PART 4: GOOGLE CALENDAR INTEGRATION
# ========================================
# (Now using shared utilities from calendar_utils.py)


# ========================================
# PART 5: MAIN PROCESSING PIPELINE
# ========================================

def process_image_with_ml(service, file_path: Path, args, calendar_id: Optional[str]) -> tuple[int, int]:
    """
    ML Pipeline: Image → OCR → Parsing → Calendar Upload
    
    This demonstrates a typical ML workflow:
    1. Data acquisition (load image)
    2. Preprocessing (enhance image)
    3. Model inference (OCR extraction)
    4. Post-processing (parse and structure)
    5. Action (upload to calendar)
    
    Args:
        service: Google Calendar service (None if dry-run)
        file_path: Path to image file
        args: Command-line arguments with mode flags
        calendar_id: Calendar ID (None if dry-run)
        
    Returns:
        (created_count, would_create_count) - Tuple of events created and would-be created
    """
    print(f"\n📷 Processing: {file_path.name}")
    
    # Step 1 & 2: Load and preprocess image, then run OCR
    raw_text = extract_text_from_image(file_path)
    
    if args.debug:
        print("\n--- RAW OCR OUTPUT ---")
        print(raw_text)
        print("--- END OCR OUTPUT ---\n")
    
    # Step 3: Parse text into structured data
    shifts = extract_shifts_from_text(raw_text)
    
    if not shifts:
        print("  ⚠️  No shifts detected in image")
        return 0
    
    print(f"  📊 Extracted {len(shifts)} shift(s)")
    
    # Step 4: Upload to calendar
    created_count = 0
    would_create_count = 0
    
    for shift in shifts:
        # Normalize shift data (adds prefix)
        normalized = normalize_shift(shift)
        summary, start = normalized['summary'], normalized['start']
        
        # Dry-run mode: No calendar API calls at all
        if args.dry_run:
            print(f"  [DRY RUN] Would create: {summary} at {start}")
            would_create_count += 1
            continue
        
        # Check for duplicates (unless dry-run)
        is_dup = is_duplicate(service, summary, start, calendar_id=calendar_id)
        
        if is_dup and not args.force:
            print(f"  ⏩ Duplicate skipped: {summary}")
        else:
            # Check-only mode: Show what would be created but don't actually create
            if args.check_only:
                if is_dup:
                    print(f"  🔍 Duplicate found: {summary}")
                else:
                    print(f"  [CHECK ONLY] Would create: {summary} at {start}")
                    would_create_count += 1
            else:
                # Normal mode: Actually create the event
                create_calendar_event(service, summary, start, normalized['end'], calendar_id=calendar_id)
                print(f"  ✅ Created: {summary} for {start}")
                created_count += 1
    
    return created_count, would_create_count


def main():
    """Main entry point with CLI argument parsing."""
    parser = argparse.ArgumentParser(
        description='Parse calendar screenshots using OCR and upload to Google Calendar',
        epilog='Example: python calhero_ml.py --dry-run --debug'
    )
    parser.add_argument('--dry-run', action='store_true', 
                       help="Test image processing only (no calendar API calls)")
    parser.add_argument('--check-only', action='store_true',
                       help="Check for duplicates but don't create events (read-only mode)")
    parser.add_argument('--force', action='store_true', 
                       help="Create events even if duplicates exist")
    parser.add_argument('--debug', action='store_true',
                       help="Show raw OCR output for debugging")
    parser.add_argument('--calendar-id', type=str,
                       help="Google Calendar ID to use (overrides env var)")
    args = parser.parse_args()
    
    print("🤖 Calendar Shift Parser - ML/OCR Version")
    print("=" * 50)
    
    # Validate flag combinations
    if args.dry_run and args.check_only:
        print("❌ Error: Cannot use --dry-run and --check-only together")
        print("   --dry-run: No calendar operations (test image processing)")
        print("   --check-only: Read-only calendar access (check duplicates)")
        return
    
    if args.dry_run and args.force:
        print("⚠️  Warning: --force has no effect in --dry-run mode")
    
    # Determine mode and get calendar ID if needed
    if args.dry_run:
        mode = "DRY-RUN"
        calendar_id = None
        service = None
        print(f"🔧 Mode: {mode}")
        print("   No calendar operations will be performed")
    elif args.check_only:
        mode = "CHECK-ONLY"
        try:
            calendar_id, source = Config.get_active_calendar_id(args.calendar_id)
            Config.log_calendar_selection(calendar_id, source)
        except ValueError as e:
            print(f"❌ Configuration Error: {e}")
            return
        service = get_calendar_service()
        print(f"🔧 Mode: {mode} (Read-only - will check duplicates but not create events)")
    else:
        mode = "NORMAL"
        try:
            calendar_id, source = Config.get_active_calendar_id(args.calendar_id)
            Config.log_calendar_selection(calendar_id, source)
        except ValueError as e:
            print(f"❌ Configuration Error: {e}")
            return
        service = get_calendar_service()
        print(f"🔧 Mode: {mode}")
    
    # Get all unprocessed screenshots
    images = get_unprocessed_images()
    
    if not images:
        print("❌ No screenshots found in /screenshots folder")
        return
    
    print(f"📂 Found {len(images)} image(s) to process")
    
    # Process each image
    total_created = 0
    total_would_create = 0
    
    for img_path in images:
        try:
            created, would_create = process_image_with_ml(service, img_path, args, calendar_id)
            total_created += created
            total_would_create += would_create
            
            # Move to processed folder (only if not dry-run or check-only)
            if not args.dry_run and not args.check_only:
                dest_path = move_to_processed(img_path)
                print(f"  📦 Moved to: {dest_path.name}")
                
        except Exception as e:
            print(f"  ❌ Error: {e}")
            if args.debug:
                import traceback
                traceback.print_exc()
    
    # Summary based on mode
    print("\n" + "=" * 50)
    print("✅ PROCESSING COMPLETE")
    print(f"📊 Images processed: {len(images)}")
    
    if args.dry_run:
        print(f"📋 Would create: {total_would_create} shifts (dry-run mode)")
    elif args.check_only:
        print(f"📋 Would create: {total_would_create} shifts (check-only mode - no events created)")
    else:
        print(f"📅 Events created: {total_created}")
    
    print("=" * 50)


if __name__ == "__main__":
    main()
