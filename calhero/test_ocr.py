#!/usr/bin/env python3
"""
ML Parser Test Script
=====================
Comprehensive testing of calhero_ml.py OCR and parsing functions.

This script tests the ACTUAL functions used by calhero_ml.py:
- preprocess_image_for_ocr() - Both standard and gentle modes
- extract_text_from_image() - Multi-strategy OCR extraction
- extract_shifts_from_text() - Shift parsing logic
- process_image_with_ml() - Full ML pipeline (dry-run mode)

Features:
- Tests real calhero_ml functions (no code duplication!)
- Compares preprocessing strategies
- Shows confidence scores
- Tests full pipeline
- Saves preprocessed images for inspection
- Provides detailed metrics and recommendations

Usage:
    python test_ocr.py <image_path>
    
    # Test with sample data (recommended for first-time testing)
    python test_ocr.py samples/sample_schedule.png
    python test_ocr.py samples/sample_schedule.png --validate samples/sample_ground_truth.json
    
    # Test with your own screenshots
    python test_ocr.py screenshots/processed/schedule.png
    python test_ocr.py screenshots/processed/schedule.png --full-pipeline
    python test_ocr.py screenshots/processed/schedule.png --save-images
    python test_ocr.py screenshots/processed/schedule.png --validate my_ground_truth.json

Options:
    --full-pipeline    Test complete ML pipeline (dry-run mode)
    --save-images      Save preprocessed images for visual inspection
    --verbose          Show detailed OCR output
    --validate FILE    Validate against ground truth JSON file (or --gt)
"""

import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
import pytesseract
from PIL import Image

# Import ACTUAL functions from calhero_ml (no duplication!)
from calhero_ml import (
    preprocess_image_for_ocr,      # The real preprocessing function
    extract_text_from_image,        # The real OCR function
    extract_shifts_from_text,       # The real parsing function
    process_image_with_ml           # The real full pipeline
)


def analyze_confidence(image, label="Image"):
    """Analyze OCR confidence scores for an image."""
    try:
        data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
        confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
        
        if not confidences:
            print(f"  {label}: No text detected")
            return None
        
        avg_confidence = sum(confidences) / len(confidences)
        min_confidence = min(confidences)
        max_confidence = max(confidences)
        total_words = len(confidences)
        
        # Quality assessment
        quality = "🎯 Excellent" if avg_confidence >= 85 else "✅ Good" if avg_confidence >= 70 else "⚠️  Low"
        
        return {
            'avg': avg_confidence,
            'min': min_confidence,
            'max': max_confidence,
            'words': total_words,
            'quality': quality
        }
    
    except Exception as e:
        print(f"  {label}: Error analyzing confidence: {e}")
        return None


def test_preprocessing(image_path, save_images=False):
    """Test both preprocessing modes using actual calhero_ml function."""
    print("\n[1] Testing Preprocessing (calhero_ml.preprocess_image_for_ocr)")
    print("=" * 70)
    
    # Test standard mode
    print("\n  Testing 'standard' mode...")
    img_standard = preprocess_image_for_ocr(image_path, mode='standard')
    print("  ✅ Standard preprocessing complete")
    
    # Test gentle mode
    print("  Testing 'gentle' mode...")
    img_gentle = preprocess_image_for_ocr(image_path, mode='gentle')
    print("  ✅ Gentle preprocessing complete")
    
    # Save images if requested
    if save_images:
        input_path = Path(image_path)
        import cv2
        
        output_std = input_path.parent / f"{input_path.stem}_preprocessed_standard{input_path.suffix}"
        output_gen = input_path.parent / f"{input_path.stem}_preprocessed_gentle{input_path.suffix}"
        
        cv2.imwrite(str(output_std), img_standard)
        cv2.imwrite(str(output_gen), img_gentle)
        
        print(f"\n  💾 Saved preprocessed images:")
        print(f"     Standard: {output_std.name}")
        print(f"     Gentle:   {output_gen.name}")
    
    return img_standard, img_gentle


def test_text_extraction(image_path, verbose=False):
    """Test the ACTUAL extract_text_from_image function (multi-strategy)."""
    print("\n[2] Testing Text Extraction (calhero_ml.extract_text_from_image)")
    print("=" * 70)
    print("\n  This function uses BOTH preprocessing strategies automatically")
    print("  and combines the results for best accuracy.\n")
    
    # This is what calhero_ml.py actually uses!
    text = extract_text_from_image(Path(image_path))
    
    if verbose:
        print("\n  Extracted Text:")
        print("  " + "-" * 66)
        for line in text.split('\n'):
            if line.strip():
                print(f"  {line}")
        print("  " + "-" * 66)
    else:
        line_count = len([line for line in text.split('\n') if line.strip()])
        print(f"\n  ✅ Extracted {line_count} lines of text")
    
    return text


def test_shift_parsing(text):
    """Test shift parsing using actual calhero_ml function."""
    print("\n[3] Testing Shift Parsing (calhero_ml.extract_shifts_from_text)")
    print("=" * 70)
    
    shifts = extract_shifts_from_text(text)
    
    print(f"\n  📊 Detected {len(shifts)} shift(s)")
    
    if shifts:
        print("\n  Parsed Shifts:")
        for i, shift in enumerate(shifts, 1):
            start = datetime.fromisoformat(shift['start'])
            end = datetime.fromisoformat(shift['end'])
            duration = (end - start).total_seconds() / 3600
            
            print(f"\n  {i}. {shift['summary']}")
            print(f"     Start:    {start.strftime('%A, %m/%d/%Y at %I:%M %p')}")
            print(f"     End:      {end.strftime('%A, %m/%d/%Y at %I:%M %p')}")
            print(f"     Duration: {duration:.1f} hours")
    else:
        print("\n  ⚠️  No shifts detected in the text")
        print("  Possible reasons:")
        print("    - Image quality too low")
        print("    - OCR couldn't read the schedule format")
        print("    - Schedule doesn't match expected patterns")
    
    return shifts


def test_strategy_comparison(image_path):
    """Compare individual preprocessing strategies."""
    print("\n[4] Strategy Comparison")
    print("=" * 70)
    
    import cv2
    
    # Process with each strategy individually
    print("\n  Processing with 'standard' mode...")
    img_std = preprocess_image_for_ocr(image_path, 'standard')
    text_std = pytesseract.image_to_string(img_std)
    shifts_std = extract_shifts_from_text(text_std)
    conf_std = analyze_confidence(img_std, "Standard")
    
    print("\n  Processing with 'gentle' mode...")
    img_gen = preprocess_image_for_ocr(image_path, 'gentle')
    text_gen = pytesseract.image_to_string(img_gen)
    shifts_gen = extract_shifts_from_text(text_gen)
    conf_gen = analyze_confidence(img_gen, "Gentle")
    
    # Comparison
    print("\n  Results:")
    print("  " + "-" * 66)
    print(f"  Strategy   | Confidence | Words | Shifts | Quality")
    print("  " + "-" * 66)
    
    if conf_std:
        print(f"  Standard   | {conf_std['avg']:5.1f}%     | {conf_std['words']:5d} | {len(shifts_std):6d} | {conf_std['quality']}")
    if conf_gen:
        print(f"  Gentle     | {conf_gen['avg']:5.1f}%     | {conf_gen['words']:5d} | {len(shifts_gen):6d} | {conf_gen['quality']}")
    
    print("  " + "-" * 66)
    
    # Recommendation
    if conf_std and conf_gen:
        if conf_std['avg'] > conf_gen['avg']:
            print("\n  💡 Standard preprocessing performed better")
        elif conf_gen['avg'] > conf_std['avg']:
            print("\n  💡 Gentle preprocessing performed better")
        else:
            print("\n  💡 Both strategies performed equally well")
        
        if len(shifts_std) > len(shifts_gen):
            print("  📊 Standard found more shifts")
        elif len(shifts_gen) > len(shifts_std):
            print("  📊 Gentle found more shifts")
    
    return {
        'standard': {'confidence': conf_std, 'shifts': len(shifts_std)},
        'gentle': {'confidence': conf_gen, 'shifts': len(shifts_gen)}
    }


def test_full_pipeline(image_path):
    """Test complete ML pipeline using actual process_image_with_ml function."""
    print("\n[5] Testing Full Pipeline (calhero_ml.process_image_with_ml)")
    print("=" * 70)
    print("\n  Running in DRY-RUN mode (no calendar operations)\n")
    
    # Create mock args for dry-run
    class MockArgs:
        dry_run = True
        check_only = False
        force = False
        debug = False
    
    try:
        # Run the ACTUAL function used by calhero_ml.py!
        created, would_create = process_image_with_ml(
            service=None,           # No calendar service in dry-run
            file_path=Path(image_path),
            args=MockArgs(),
            calendar_id=None        # No calendar ID in dry-run
        )
        
        print(f"\n  ✅ Pipeline completed successfully!")
        print(f"  📊 Would create: {would_create} shift(s)")
        
        return would_create
        
    except Exception as e:
        print(f"\n  ❌ Pipeline failed: {e}")
        print("\n  This might indicate:")
        print("    - OCR extraction issues")
        print("    - Parsing logic problems")
        print("    - Unexpected schedule format")
        import traceback
        traceback.print_exc()
        return 0


def validate_with_ground_truth(image_path, detected_shifts, gt_file):
    """
    Simple validation against ground truth file.
    
    Note: For detailed metrics (precision/recall/F1), use test_comparison.py.
    This provides quick validation for ML development.
    
    Args:
        image_path: Path to the image being tested
        detected_shifts: List of shifts detected by ML parser
        gt_file: Path to ground truth JSON file
    """
    print("\n[6] Ground Truth Validation")
    print("=" * 70)
    
    try:
        # Load ground truth (uses same format as test_comparison.py)
        with open(gt_file) as f:
            gt_data = json.load(f)
        
        image_name = Path(image_path).name
        if image_name not in gt_data.get('images', {}):
            print(f"  ⚠️  {image_name} not found in ground truth file")
            print(f"  Available images: {', '.join(gt_data.get('images', {}).keys())}")
            return
        
        gt_shifts = gt_data['images'][image_name]['shifts']
        
        # Simple comparison: match by summary and start time
        matches = 0
        matched_summaries = []
        for detected in detected_shifts:
            for gt in gt_shifts:
                if (detected.get('summary') == gt.get('summary') and 
                    detected.get('start') == gt.get('start')):
                    matches += 1
                    matched_summaries.append(detected.get('summary', 'Unknown'))
                    break
        
        # Calculate metrics
        print(f"\n  Ground Truth: {len(gt_shifts)} shifts")
        print(f"  Detected:     {len(detected_shifts)} shifts")
        print(f"  Matches:      {matches} shifts")
        
        accuracy = (matches / len(gt_shifts) * 100) if gt_shifts else 0
        print(f"\n  Accuracy:     {accuracy:.1f}%")
        
        # Status indicator
        if accuracy == 100:
            print("  ✅ Perfect match!")
        elif accuracy >= 80:
            print("  ✅ Good match")
        elif accuracy >= 50:
            print("  ⚠️  Partial match - check OCR quality")
        else:
            print("  ❌ Poor match - OCR issues likely")
        
        # Show what's missing/extra
        if len(detected_shifts) < len(gt_shifts):
            missing = len(gt_shifts) - len(detected_shifts)
            print(f"\n  ⚠️  Missing {missing} shift(s)")
        elif len(detected_shifts) > len(gt_shifts):
            extra = len(detected_shifts) - len(gt_shifts)
            print(f"\n  ⚠️  Found {extra} extra shift(s)")
        
        # Show matched shifts (if reasonable number)
        if matches > 0 and matches < 10:
            print(f"\n  Matched shifts:")
            for summary in matched_summaries:
                print(f"    ✓ {summary}")
        
        print("\n  💡 For detailed metrics (precision/recall/F1), use:")
        print("     python test_comparison.py --ground-truth ground_truth.json")
        
    except FileNotFoundError:
        print(f"  ❌ Ground truth file not found: {gt_file}")
        print(f"\n  To create ground truth:")
        print(f"     python test_comparison.py --create-ground-truth ground_truth.json")
    except json.JSONDecodeError as e:
        print(f"  ❌ Invalid JSON in ground truth file: {e}")
    except Exception as e:
        print(f"  ❌ Validation error: {e}")


def print_summary(image_path, shifts_found, comparison_results=None):
    """Print test summary and recommendations."""
    print("\n" + "=" * 70)
    print("📊 TEST SUMMARY")
    print("=" * 70)
    
    print(f"\nImage tested: {Path(image_path).name}")
    print(f"Shifts detected: {shifts_found}")
    
    if comparison_results:
        std_conf = comparison_results['standard']['confidence']
        gen_conf = comparison_results['gentle']['confidence']
        
        if std_conf and gen_conf:
            print(f"\nPreprocessing performance:")
            print(f"  Standard: {std_conf['avg']:.1f}% confidence, {std_conf['quality']}")
            print(f"  Gentle:   {gen_conf['avg']:.1f}% confidence, {gen_conf['quality']}")
    
    print("\n💡 Recommendations:")
    if shifts_found == 0:
        print("  • Check image quality - might need better resolution")
        print("  • Verify schedule format matches expected patterns")
        print("  • Try adjusting preprocessing parameters")
    elif shifts_found < 5:
        print("  • Some shifts might be missing - check OCR output")
        print("  • Consider using LLM version for better accuracy")
    else:
        print("  • ✅ Good detection rate!")
        print("  • ML/OCR version should work well for this image")
    
    print("\n📚 Next steps:")
    print("  • Use --verbose to see extracted text")
    print("  • Use --save-images to inspect preprocessing")
    print("  • Compare with: python test_comparison.py")


def main():
    parser = argparse.ArgumentParser(
        description='Test calhero_ml.py OCR and parsing functions',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python test_ocr.py screenshots/schedule.png
  python test_ocr.py screenshots/schedule.png --full-pipeline
  python test_ocr.py screenshots/schedule.png --save-images --verbose
  python test_ocr.py screenshots/schedule.png --validate ground_truth.json
        """
    )
    
    parser.add_argument('image_path', help='Path to schedule image')
    parser.add_argument('--full-pipeline', action='store_true',
                       help='Test complete ML pipeline (dry-run mode)')
    parser.add_argument('--save-images', action='store_true',
                       help='Save preprocessed images for visual inspection')
    parser.add_argument('--verbose', action='store_true',
                       help='Show detailed OCR output')
    parser.add_argument('--validate', '--gt', dest='ground_truth', metavar='FILE',
                       help='Validate against ground truth JSON file')
    
    args = parser.parse_args()
    
    # Validate image path
    if not Path(args.image_path).exists():
        print(f"❌ File not found: {args.image_path}")
        
        # Show available images
        screenshots_dir = Path("screenshots/processed")
        if screenshots_dir.exists():
            images = list(screenshots_dir.glob("*.png")) + list(screenshots_dir.glob("*.jpg"))
            if images:
                print(f"\nAvailable images in {screenshots_dir}:")
                for img in images[:5]:
                    print(f"  • {img}")
        return 1
    
    print("\n" + "=" * 70)
    print("🧪 ML PARSER TEST SUITE")
    print("=" * 70)
    print(f"\nTesting: {args.image_path}")
    print("Using ACTUAL functions from calhero_ml.py")
    
    try:
        # Test 1: Preprocessing
        img_std, img_gen = test_preprocessing(args.image_path, args.save_images)
        
        # Test 2: Text Extraction (multi-strategy)
        text = test_text_extraction(args.image_path, args.verbose)
        
        # Test 3: Shift Parsing
        shifts = test_shift_parsing(text)
        
        # Test 4: Strategy Comparison
        comparison = test_strategy_comparison(args.image_path)
        
        # Test 5: Full Pipeline (if requested)
        pipeline_shifts = 0
        if args.full_pipeline:
            pipeline_shifts = test_full_pipeline(args.image_path)
            
            # Verify consistency
            if len(shifts) != pipeline_shifts:
                print(f"\n  ⚠️  Mismatch: Direct parsing found {len(shifts)} shifts,")
                print(f"     but full pipeline found {pipeline_shifts} shifts")
        
        # Test 6: Ground Truth Validation (if provided)
        if args.ground_truth:
            validate_with_ground_truth(args.image_path, shifts, args.ground_truth)
        
        # Summary
        print_summary(args.image_path, len(shifts), comparison)
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        
        print("\nPossible issues:")
        print("  • Tesseract not installed: brew install tesseract")
        print("  • Missing dependencies: pip install -r requirements_ml.txt")
        print("  • .env file not configured (for full pipeline test)")
        return 1


if __name__ == "__main__":
    sys.exit(main())
