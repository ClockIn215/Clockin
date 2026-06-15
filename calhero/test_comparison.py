#!/usr/bin/env python3
"""
Calendar Parser Comparison Test Suite
=====================================
Compares the accuracy and performance of LLM vs ML/OCR versions.

This script:
1. Runs both parsers on the same test images
2. Compares extracted shifts
3. Provides accuracy metrics
4. Generates detailed comparison reports

Usage:
    python test_comparison.py
    python test_comparison.py --images screenshots/processed/*.png
    python test_comparison.py --ground-truth ground_truth.json
"""

import json
import argparse
import time
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple
from collections import defaultdict

# Import shared utilities
from calendar_utils import Config

# Import parsing functions from both versions
from google import genai
from google.genai import types
import pytesseract


# ========================================
# PARSING FUNCTIONS (ISOLATED FOR TESTING)
# ========================================

def parse_with_llm(image_path: Path) -> Tuple[List[Dict], float]:
    """
    Parse image using Gemini LLM.
    
    Returns:
        (list of shifts, processing time in seconds)
    """
    start_time = time.time()
    
    client = genai.Client(api_key=Config.GEMINI_API_KEY)
    
    with open(image_path, "rb") as f:
        image_bytes = f.read()
    
    try:
        response = client.models.generate_content(
            model=Config.GEMINI_MODEL,
            contents=[types.Part.from_bytes(data=image_bytes, mime_type="image/png"), Config.GEMINI_PROMPT],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=Config.GEMINI_TEMPERATURE
            )
        )
        
        shifts = json.loads(response.text)
        elapsed = time.time() - start_time
        return shifts, elapsed
    except Exception as e:
        print(f"    ❌ LLM parsing error: {e}")
        return [], time.time() - start_time


def parse_with_ml(image_path: Path) -> Tuple[List[Dict], float]:
    """
    Parse image using ML/OCR.
    
    Returns:
        (list of shifts, processing time in seconds)
    """
    start_time = time.time()
    
    try:
        # Import ML parsing functions
        from calhero_ml import extract_text_from_image, extract_shifts_from_text
        
        # Extract text and parse
        text = extract_text_from_image(image_path)
        shifts = extract_shifts_from_text(text)
        
        elapsed = time.time() - start_time
        return shifts, elapsed
    except Exception as e:
        print(f"    ❌ ML/OCR parsing error: {e}")
        return [], time.time() - start_time


# ========================================
# COMPARISON LOGIC
# ========================================

def normalize_shift_for_comparison(shift: dict) -> dict:
    """Normalize shift data for fair comparison."""
    # Remove prefixes and clean summary
    summary = shift['summary'].replace('Odel shoola ', '').strip()
    
    # Parse datetimes
    start = datetime.fromisoformat(shift['start'])
    end = datetime.fromisoformat(shift['end'])
    
    return {
        'summary': summary,
        'start': start,
        'end': end,
        'date': start.date(),
        'start_time': start.time(),
        'end_time': end.time()
    }


def shifts_match(shift1: dict, shift2: dict, tolerance_minutes: int = 30) -> bool:
    """
    Check if two shifts match (allowing for minor differences).
    
    Args:
        shift1, shift2: Normalized shift dictionaries
        tolerance_minutes: How many minutes difference to allow in times
    """
    from datetime import timedelta
    
    # Must be same date
    if shift1['date'] != shift2['date']:
        return False
    
    # Must be similar summary
    s1_summary = shift1['summary'].lower()
    s2_summary = shift2['summary'].lower()
    if s1_summary not in s2_summary and s2_summary not in s1_summary:
        # Allow common variations
        if not (('coverage' in s1_summary or 'coverage' in s2_summary) and
                ('training' not in s1_summary and 'training' not in s2_summary)):
            return False
    
    # Times must be within tolerance
    time_diff_start = abs((shift1['start'] - shift2['start']).total_seconds() / 60)
    time_diff_end = abs((shift1['end'] - shift2['end']).total_seconds() / 60)
    
    return time_diff_start <= tolerance_minutes and time_diff_end <= tolerance_minutes


def compare_shift_lists(llm_shifts: List[dict], ml_shifts: List[dict]) -> Dict:
    """
    Compare two lists of shifts and compute accuracy metrics.
    
    Returns:
        Dictionary with comparison results
    """
    # Normalize all shifts
    llm_normalized = [normalize_shift_for_comparison(s) for s in llm_shifts]
    ml_normalized = [normalize_shift_for_comparison(s) for s in ml_shifts]
    
    # Find matches
    matched_llm = set()
    matched_ml = set()
    matches = []
    
    for i, llm_shift in enumerate(llm_normalized):
        for j, ml_shift in enumerate(ml_normalized):
            if j not in matched_ml and shifts_match(llm_shift, ml_shift):
                matched_llm.add(i)
                matched_ml.add(j)
                matches.append((llm_shift, ml_shift))
                break
    
    # Calculate metrics
    llm_only = [s for i, s in enumerate(llm_normalized) if i not in matched_llm]
    ml_only = [s for i, s in enumerate(ml_normalized) if i not in matched_ml]
    
    total_unique = len(llm_normalized) + len(ml_only)
    
    return {
        'total_llm': len(llm_shifts),
        'total_ml': len(ml_shifts),
        'matches': len(matches),
        'llm_only': llm_only,
        'ml_only': ml_only,
        'match_details': matches,
        'accuracy_llm': len(matches) / len(llm_normalized) if llm_normalized else 0,
        'accuracy_ml': len(matches) / len(ml_normalized) if ml_normalized else 0,
        'f1_score': (2 * len(matches)) / (len(llm_normalized) + len(ml_normalized)) 
                    if (llm_normalized or ml_normalized) else 0
    }


# ========================================
# TEST EXECUTION
# ========================================

def test_single_image(image_path: Path, verbose: bool = True) -> Dict:
    """Test both parsers on a single image."""
    if verbose:
        print(f"\n{'='*70}")
        print(f"Testing: {image_path.name}")
        print('='*70)
    
    # Parse with both methods
    if verbose:
        print("\n[1] Running LLM parser...")
    llm_shifts, llm_time = parse_with_llm(image_path)
    if verbose:
        print(f"    ✅ Found {len(llm_shifts)} shifts in {llm_time:.2f}s")
    
    if verbose:
        print("\n[2] Running ML/OCR parser...")
    ml_shifts, ml_time = parse_with_ml(image_path)
    if verbose:
        print(f"    ✅ Found {len(ml_shifts)} shifts in {ml_time:.2f}s")
    
    # Compare results
    if verbose:
        print("\n[3] Comparing results...")
    comparison = compare_shift_lists(llm_shifts, ml_shifts)
    comparison['llm_time'] = llm_time
    comparison['ml_time'] = ml_time
    comparison['image'] = image_path.name
    
    if verbose:
        print_comparison_results(comparison)
    
    return comparison


def print_comparison_results(comparison: Dict):
    """Print formatted comparison results."""
    print(f"\n📊 Results:")
    print(f"  LLM found: {comparison['total_llm']} shifts ({comparison['llm_time']:.2f}s)")
    print(f"  ML found:  {comparison['total_ml']} shifts ({comparison['ml_time']:.2f}s)")
    print(f"  Matches:   {comparison['matches']} shifts")
    print(f"  F1 Score:  {comparison['f1_score']:.2%}")
    
    if comparison['llm_only']:
        print(f"\n  ⚠️  LLM found {len(comparison['llm_only'])} shifts that ML missed:")
        for shift in comparison['llm_only']:
            print(f"    - {shift['summary']}: {shift['start'].strftime('%a %m/%d %I:%M%p')}")
    
    if comparison['ml_only']:
        print(f"\n  ⚠️  ML found {len(comparison['ml_only'])} shifts that LLM missed:")
        for shift in comparison['ml_only']:
            print(f"    - {shift['summary']}: {shift['start'].strftime('%a %m/%d %I:%M%p')}")


def create_ground_truth(results: List[Dict], output_file: str, avg_f1: float):
    """
    Create ground truth JSON file from comparison results.
    Only creates file if all images have 100% F1 score.
    
    Args:
        results: List of comparison results from test_single_image
        output_file: Path to output JSON file
        avg_f1: Average F1 score across all images
    """
    print("\n" + "="*70)
    print("🎯 GROUND TRUTH GENERATION")
    print("="*70)
    
    # Check if all results have perfect match
    imperfect_images = []
    for result in results:
        if result['f1_score'] < 1.0:  # F1 is 0-1, not 0-100
            imperfect_images.append({
                'image': result['image'],
                'f1_score': result['f1_score'] * 100,
                'llm_count': result['total_llm'],
                'ml_count': result['total_ml'],
                'matched': result['matches']
            })
    
    if imperfect_images:
        print("\n❌ Cannot create ground truth file - not all images have perfect matches:")
        print(f"\n  Average F1 Score: {avg_f1:.2%} (need 100.00%)")
        print(f"\n  Images with mismatches:")
        for img_info in imperfect_images:
            print(f"    • {img_info['image']}: F1={img_info['f1_score']:.2f}%")
            print(f"      LLM found {img_info['llm_count']}, ML found {img_info['ml_count']}, matched {img_info['matched']}")
        print(f"\n  💡 Fix the parsing differences and re-run with --create-ground-truth")
        return
    
    # All images have perfect match - create ground truth
    ground_truth = {
        "version": "1.0",
        "created": datetime.now().isoformat(),
        "description": "Ground truth data for calendar shift parsing validation",
        "images": {}
    }
    
    for result in results:
        image_name = result['image']
        # Use LLM shifts as ground truth (since they match ML perfectly)
        # Convert datetime objects to ISO strings for JSON serialization
        shifts = []
        for shift in result['llm_shifts']:
            shifts.append({
                "summary": shift['summary'],
                "start": shift['start'].isoformat() if hasattr(shift['start'], 'isoformat') else shift['start'],
                "end": shift['end'].isoformat() if hasattr(shift['end'], 'isoformat') else shift['end']
            })
        
        ground_truth['images'][image_name] = {
            "shifts": shifts
        }
    
    # Write to file
    output_path = Path(output_file)
    with open(output_path, 'w') as f:
        json.dump(ground_truth, f, indent=2)
    
    print(f"\n✅ Ground truth file created: {output_path}")
    print(f"   Images: {len(results)}")
    print(f"   Total shifts: {sum(r['total_llm'] for r in results)}")
    print(f"   All images have 100% F1 score match")
    print("\n" + "="*70)


def run_ground_truth_validation(image_paths: List[Path], ground_truth_path: Path, args=None):
    """
    Validate parser results against ground truth data.
    
    Args:
        image_paths: List of image files to validate
        ground_truth_path: Path to ground truth JSON file
        args: Optional argparse args (for future extensions like --output)
    """
    print("\n" + "="*70)
    print("🎯 GROUND TRUTH VALIDATION MODE")
    print("="*70)
    print(f"Loading ground truth from: {ground_truth_path}\n")
    
    ground_truth_data = load_ground_truth(ground_truth_path)
    
    # Run validation for each image
    validation_results = []
    for image_path in image_paths:
        image_name = image_path.name
        
        if image_name not in ground_truth_data['images']:
            print(f"⚠️  Skipping {image_name} - not in ground truth file")
            continue
        
        print(f"\n{'='*70}")
        print(f"Validating: {image_name}")
        print('='*70)
        
        # Run both parsers
        print("\n[1] Running LLM parser...")
        llm_shifts, llm_time = parse_with_llm(image_path)
        print(f"    ✅ Found {len(llm_shifts)} shifts in {llm_time:.2f}s")
        
        print("\n[2] Running ML/OCR parser...")
        ml_shifts, ml_time = parse_with_ml(image_path)
        print(f"    ✅ Found {len(ml_shifts)} shifts in {ml_time:.2f}s")
        
        # Validate against ground truth
        gt_shifts = ground_truth_data['images'][image_name]['shifts']
        
        print("\n[3] Validating against ground truth...")
        llm_validation = validate_against_ground_truth(image_path, llm_shifts, gt_shifts)
        ml_validation = validate_against_ground_truth(image_path, ml_shifts, gt_shifts)
        
        # Get detailed comparison for mismatch reporting
        llm_comparison = compare_shift_lists(gt_shifts, llm_shifts)
        ml_comparison = compare_shift_lists(gt_shifts, ml_shifts)
        
        print(f"\n📊 Validation Results:")
        print(f"  Ground Truth: {len(gt_shifts)} shifts")
        print(f"\n  LLM Parser:")
        print(f"    Precision: {llm_validation['precision']:.2%}")
        print(f"    Recall:    {llm_validation['recall']:.2%}")
        print(f"    F1 Score:  {llm_validation['f1_score']:.2%}")
        
        # Show LLM mismatches if any
        if llm_validation['f1_score'] < 1.0:
            if llm_comparison['llm_only']:
                print(f"\n    ⚠️  Missed {len(llm_comparison['llm_only'])} shifts (in ground truth but not found):")
                for shift in llm_comparison['llm_only']:
                    start_dt = datetime.fromisoformat(shift['start']) if isinstance(shift['start'], str) else shift['start']
                    end_dt = datetime.fromisoformat(shift['end']) if isinstance(shift['end'], str) else shift['end']
                    print(f"      - {shift['summary']}: {start_dt.strftime('%a %m/%d %I:%M%p')} - {end_dt.strftime('%I:%M%p')}")
            
            if llm_comparison['ml_only']:
                print(f"\n    ⚠️  Found {len(llm_comparison['ml_only'])} extra shifts (not in ground truth):")
                for shift in llm_comparison['ml_only']:
                    start_dt = shift['start'] if isinstance(shift['start'], datetime) else datetime.fromisoformat(shift['start'])
                    end_dt = shift['end'] if isinstance(shift['end'], datetime) else datetime.fromisoformat(shift['end'])
                    print(f"      - {shift['summary']}: {start_dt.strftime('%a %m/%d %I:%M%p')} - {end_dt.strftime('%I:%M%p')}")
        
        print(f"\n  ML/OCR Parser:")
        print(f"    Precision: {ml_validation['precision']:.2%}")
        print(f"    Recall:    {ml_validation['recall']:.2%}")
        print(f"    F1 Score:  {ml_validation['f1_score']:.2%}")
        
        # Show ML mismatches if any
        if ml_validation['f1_score'] < 1.0:
            if ml_comparison['llm_only']:
                print(f"\n    ⚠️  Missed {len(ml_comparison['llm_only'])} shifts (in ground truth but not found):")
                for shift in ml_comparison['llm_only']:
                    start_dt = datetime.fromisoformat(shift['start']) if isinstance(shift['start'], str) else shift['start']
                    end_dt = datetime.fromisoformat(shift['end']) if isinstance(shift['end'], str) else shift['end']
                    print(f"      - {shift['summary']}: {start_dt.strftime('%a %m/%d %I:%M%p')} - {end_dt.strftime('%I:%M%p')}")
            
            if ml_comparison['ml_only']:
                print(f"\n    ⚠️  Found {len(ml_comparison['ml_only'])} extra shifts (not in ground truth):")
                for shift in ml_comparison['ml_only']:
                    start_dt = shift['start'] if isinstance(shift['start'], datetime) else datetime.fromisoformat(shift['start'])
                    end_dt = shift['end'] if isinstance(shift['end'], datetime) else datetime.fromisoformat(shift['end'])
                    print(f"      - {shift['summary']}: {start_dt.strftime('%a %m/%d %I:%M%p')} - {end_dt.strftime('%I:%M%p')}")
        
        validation_results.append({
            'image': image_name,
            'llm': llm_validation,
            'ml': ml_validation,
            'llm_time': llm_time,
            'ml_time': ml_time
        })
    
    # Summary
    print("\n" + "="*70)
    print("📈 VALIDATION SUMMARY")
    print("="*70)
    
    if validation_results:
        avg_llm_f1 = sum(r['llm']['f1_score'] for r in validation_results) / len(validation_results)
        avg_ml_f1 = sum(r['ml']['f1_score'] for r in validation_results) / len(validation_results)
        
        avg_llm_time = sum(r['llm_time'] for r in validation_results) / len(validation_results)
        avg_ml_time = sum(r['ml_time'] for r in validation_results) / len(validation_results)
        
        print(f"\nAverage F1 Scores:")
        print(f"  LLM Parser:    {avg_llm_f1:.2%}")
        print(f"  ML/OCR Parser: {avg_ml_f1:.2%}")
        
        print(f"\nAverage Processing Time:")
        print(f"  LLM Parser:    {avg_llm_time:.2f}s per image")
        print(f"  ML/OCR Parser: {avg_ml_time:.2f}s per image")
        print(f"  Speed ratio:   {avg_llm_time/avg_ml_time:.1f}x" if avg_ml_time > 0 else "")
    else:
        print("\n⚠️  No images were validated")
    
    print("\n" + "="*70)
    
    return validation_results


def run_test_suite(image_paths: List[Path]) -> Dict:
    """Run comparison tests on multiple images."""
    print("\n" + "="*70)
    print("🧪 CALENDAR PARSER COMPARISON TEST SUITE")
    print("="*70)
    print(f"\nTesting {len(image_paths)} image(s)...\n")
    
    results = []
    for image_path in image_paths:
        result = test_single_image(image_path, verbose=True)
        results.append(result)
    
    # Aggregate statistics
    print("\n" + "="*70)
    print("📈 AGGREGATE STATISTICS")
    print("="*70)
    
    total_llm = sum(r['total_llm'] for r in results)
    total_ml = sum(r['total_ml'] for r in results)
    total_matches = sum(r['matches'] for r in results)
    avg_f1 = sum(r['f1_score'] for r in results) / len(results) if results else 0
    
    avg_llm_time = sum(r['llm_time'] for r in results) / len(results) if results else 0
    avg_ml_time = sum(r['ml_time'] for r in results) / len(results) if results else 0
    
    print(f"\nTotal shifts found:")
    print(f"  LLM:     {total_llm} shifts")
    print(f"  ML/OCR:  {total_ml} shifts")
    print(f"  Matched: {total_matches} shifts")
    
    print(f"\nAccuracy:")
    print(f"  Average F1 Score: {avg_f1:.2%}")
    print(f"  LLM Precision:    {total_matches/total_llm:.2%}" if total_llm else "  LLM Precision: N/A")
    print(f"  ML Precision:     {total_matches/total_ml:.2%}" if total_ml else "  ML Precision: N/A")
    
    print(f"\nPerformance:")
    print(f"  LLM avg time: {avg_llm_time:.2f}s per image")
    print(f"  ML avg time:  {avg_ml_time:.2f}s per image")
    print(f"  Speed ratio:  {avg_llm_time/avg_ml_time:.1f}x" if avg_ml_time > 0 else "")
    
    # Recommendation
    print(f"\n💡 Recommendation:")
    if avg_f1 >= 0.95:
        print(f"  ✅ Both parsers are highly accurate (F1: {avg_f1:.2%})")
        print(f"  → Use ML version for cost savings ({avg_ml_time:.2f}s vs {avg_llm_time:.2f}s)")
    elif avg_f1 >= 0.85:
        print(f"  ✅ Both parsers work well (F1: {avg_f1:.2%})")
        print(f"  → Use LLM for better accuracy, ML for learning/cost savings")
    else:
        print(f"  ⚠️  Significant differences detected (F1: {avg_f1:.2%})")
        print(f"  → Review individual results above")
        print(f"  → LLM version recommended for production use")
    
    return {
        'results': results,
        'total_llm': total_llm,
        'total_ml': total_ml,
        'total_matches': total_matches,
        'avg_f1': avg_f1,
        'avg_llm_time': avg_llm_time,
        'avg_ml_time': avg_ml_time
    }


# ========================================
# GROUND TRUTH VALIDATION (OPTIONAL)
# ========================================

def load_ground_truth(json_path: Path) -> Dict[str, List[Dict]]:
    """
    Load ground truth data from JSON file.
    
    Format:
    {
        "image_name.png": [
            {"summary": "Coverage", "start": "2026-01-19T12:00:00", "end": "2026-01-19T18:00:00"},
            ...
        ]
    }
    """
    with open(json_path) as f:
        return json.load(f)


def validate_against_ground_truth(image_path: Path, shifts: List[Dict], 
                                  ground_truth: List[Dict]) -> Dict:
    """Compare parser results against known ground truth."""
    comparison = compare_shift_lists(ground_truth, shifts)
    
    # True Positives, False Positives, False Negatives
    tp = comparison['matches']
    fp = len(comparison['ml_only'])  # Found but not in ground truth
    fn = len(comparison['llm_only'])  # In ground truth but not found
    
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    
    return {
        'true_positives': tp,
        'false_positives': fp,
        'false_negatives': fn,
        'precision': precision,
        'recall': recall,
        'f1_score': f1
    }


# ========================================
# MAIN CLI
# ========================================

def main():
    parser = argparse.ArgumentParser(
        description='Compare LLM and ML/OCR calendar parsers',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test all processed images
  python test_comparison.py
  
  # Test specific images
  python test_comparison.py --images screenshots/processed/1000012581.png
  
  # Validate against ground truth
  python test_comparison.py --ground-truth ground_truth.json
        """
    )
    parser.add_argument('--images', nargs='+', 
                       help='Specific images to test (default: all in processed/)')
    parser.add_argument('--ground-truth', type=Path,
                       help='JSON file with ground truth data')
    parser.add_argument('--output', type=Path,
                       help='Save results to JSON file')
    parser.add_argument('--create-ground-truth', type=str, metavar='OUTPUT_FILE',
                       help='Create ground truth JSON file from comparison (only if 100%% match)')
    
    args = parser.parse_args()
    
    # Get images to test
    if args.images:
        image_paths = [Path(img) for img in args.images]
    else:
        # Default: use all processed images
        image_paths = list(Config.PROCESSED_DIR.glob("*.png"))
        image_paths += list(Config.PROCESSED_DIR.glob("*.jpg"))
    
    if not image_paths:
        print("❌ No images found to test")
        print("\nTry:")
        print("  python test_comparison.py --images screenshots/processed/*.png")
        return
    
    # Check if ground truth validation mode
    if args.ground_truth:
        # VALIDATION MODE: Compare against ground truth
        validation_results = run_ground_truth_validation(image_paths, args.ground_truth, args)
        
        # Save validation results if requested
        if args.output:
            with open(args.output, 'w') as f:
                serializable_results = {
                    'mode': 'ground_truth_validation',
                    'ground_truth_file': str(args.ground_truth),
                    'images_validated': len(validation_results),
                    'results': [
                        {
                            'image': r['image'],
                            'llm_f1': r['llm']['f1_score'],
                            'ml_f1': r['ml']['f1_score'],
                            'llm_time': r['llm_time'],
                            'ml_time': r['ml_time']
                        } for r in validation_results
                    ],
                    'timestamp': datetime.now().isoformat()
                }
                json.dump(serializable_results, f, indent=2)
            print(f"\n💾 Validation results saved to: {args.output}")
        
        return
    
    # COMPARISON MODE: Compare LLM vs ML
    test_results = run_test_suite(image_paths)
    
    # Create ground truth if requested
    if hasattr(args, 'create_ground_truth') and args.create_ground_truth:
        create_ground_truth(test_results['results'], args.create_ground_truth, test_results['avg_f1'])
    
    # Save results if requested
    if args.output:
        with open(args.output, 'w') as f:
            # Convert datetime objects to strings for JSON serialization
            serializable_results = {
                'total_llm': test_results['total_llm'],
                'total_ml': test_results['total_ml'],
                'total_matches': test_results['total_matches'],
                'avg_f1': test_results['avg_f1'],
                'avg_llm_time': test_results['avg_llm_time'],
                'avg_ml_time': test_results['avg_ml_time'],
                'timestamp': datetime.now().isoformat()
            }
            json.dump(serializable_results, f, indent=2)
        print(f"\n💾 Results saved to: {args.output}")
    
    print("\n" + "="*70)


if __name__ == "__main__":
    main()
