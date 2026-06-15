import json
import argparse
from google import genai
from google.genai import types

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

def process_image(service, client, file_path, args, calendar_id):
    """Parses a single image using Gemini LLM and syncs to calendar."""
    print(f"📷 Analyzing: {file_path.name}...")
    with open(file_path, "rb") as f:
        image_bytes = f.read()
    
    response = client.models.generate_content(
        model=Config.GEMINI_MODEL,
        contents=[types.Part.from_bytes(data=image_bytes, mime_type="image/png"), Config.GEMINI_PROMPT],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=Config.GEMINI_TEMPERATURE
        )
    )
    
    shifts = json.loads(response.text)
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
    parser = argparse.ArgumentParser(description='Calendar Screenshot Parser (LLM version)')
    parser.add_argument('--dry-run', action='store_true', 
                       help="Test image processing only (no calendar API calls)")
    parser.add_argument('--check-only', action='store_true',
                       help="Check for duplicates but don't create events (read-only mode)")
    parser.add_argument('--force', action='store_true', 
                       help="Create events even if duplicates exist")
    parser.add_argument('--calendar-id', type=str, 
                       help="Google Calendar ID to use (overrides env var)")
    args = parser.parse_args()

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

    # Validate Gemini API key (required for LLM version, even in dry-run)
    if not Config.GEMINI_API_KEY:
        print("\n" + "=" * 70)
        print("❌ Gemini API Key Missing")
        print("=" * 70)
        print("\nMissing: GEMINI_API_KEY in .env file\n")
        print("Purpose:")
        print("  Required for Gemini LLM to process schedule images")
        print("  This is needed EVEN in --dry-run mode\n")
        print("How to get it:")
        print("  1. Go to: https://aistudio.google.com/app/apikey")
        print("  2. Create API key")
        print("  3. Add to .env file: GEMINI_API_KEY=your-key-here\n")
        print("Alternative:")
        print("  Use ML/OCR version instead (no API key needed):")
        print("  → python calhero_ml.py [options]\n")
        print("=" * 70)
        return

    client = genai.Client(api_key=Config.GEMINI_API_KEY)
    
    # Get all unprocessed screenshots
    images = get_unprocessed_images()
    
    if not images:
        print("No new screenshots found in /screenshots.")
        return

    total_created = 0
    total_would_create = 0
    
    for img_path in images:
        try:
            created, would_create = process_image(service, client, img_path, args, calendar_id)
            total_created += created
            total_would_create += would_create
            
            if not args.dry_run and not args.check_only:
                dest_path = move_to_processed(img_path)
                print(f"  📦 Moved to: {dest_path.name}")
        except Exception as e:
            print(f"  ❌ Error processing {img_path.name}: {e}")

    # Summary based on mode
    print(f"\n--- Processing Complete ---")
    print(f"Files processed: {len(images)}")
    
    if args.dry_run:
        print(f"Would create: {total_would_create} shifts (dry-run mode)")
    elif args.check_only:
        print(f"Would create: {total_would_create} shifts (check-only mode - no events created)")
    else:
        print(f"Shifts created: {total_created}")

if __name__ == "__main__":
    main()