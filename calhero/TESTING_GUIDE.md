# Testing Guide - Comparing LLM vs ML/OCR

This guide explains how to test and compare the accuracy of both calendar parsers.

## 🎯 Testing Philosophy

When building ML systems, it's critical to:
1. **Measure accuracy** - Know how well each approach performs
2. **Compare approaches** - Understand trade-offs between methods
3. **Track regressions** - Ensure changes don't break functionality
4. **Validate with ground truth** - Test against known-correct data

## 📁 Test Framework Structure

```
test_comparison.py       # Main test framework
test_ocr.py             # ML/OCR specific tests
calendar_utils.py       # Shared utilities (no duplication)
calhero.py              # LLM version (uses shared utils)
calhero_ml.py           # ML version (uses shared utils)
samples/                # Sample data for testing
  ├── sample_schedule.png
  ├── sample_ground_truth.json
  └── README.md
screenshots/            # Your personal screenshots (gitignored)
  └── processed/
```

## 🚀 Quick Start

### Test with Sample Data (Recommended First Step)

Start by testing with sanitized sample data immediately after cloning:

```bash
# Test ML/OCR parser with sample
python test_ocr.py samples/sample_schedule.png --validate samples/sample_ground_truth.json

# Test both parsers and compare (requires LLM API key)
python test_comparison.py --image samples/sample_schedule.png --ground-truth samples/sample_ground_truth.json
```

**Note:** Sample data is provided in the `samples/` directory for quick testing without needing real schedule screenshots. See `samples/README.md` for more details.

### Basic Comparison Test

Test both parsers on all processed images:

```bash
python test_comparison.py
```

This will:
- Run both parsers on each image
- Compare the results
- Show accuracy metrics (F1 score, precision, recall)
- Provide a recommendation

### Test Specific Images

```bash
python test_comparison.py --images screenshots/processed/1000012581.png
```

### Save Results to JSON

```bash
python test_comparison.py --output test_results.json
```

## 📊 Understanding the Metrics

### F1 Score
- **Range**: 0.0 to 1.0 (higher is better)
- **Meaning**: Harmonic mean of precision and recall
- **Interpretation**:
  - `> 0.95` = Excellent agreement (both parsers highly accurate)
  - `0.85 - 0.95` = Good agreement (minor differences)
  - `< 0.85` = Significant differences (investigate why)

### Precision
- **Formula**: True Positives / (True Positives + False Positives)
- **Meaning**: Of all shifts found, how many were correct?
- **High precision** = Few false alarms

### Recall
- **Formula**: True Positives / (True Positives + False Negatives)
- **Meaning**: Of all actual shifts, how many were found?
- **High recall** = Few missed shifts

### Example Output

```
📊 Results:
  LLM found: 5 shifts (1.23s)
  ML found:  5 shifts (0.45s)
  Matches:   5 shifts
  F1 Score:  100.00%

💡 Recommendation:
  ✅ Both parsers are highly accurate (F1: 100.00%)
  → Use ML version for cost savings (0.45s vs 1.23s)
```

## 🔬 Advanced Testing

### Creating Ground Truth Data

For rigorous testing, create a ground truth JSON file with known-correct data:

```json
{
  "1000012581.png": [
    {
      "summary": "Coverage",
      "start": "2026-01-19T12:00:00",
      "end": "2026-01-19T18:00:00"
    },
    {
      "summary": "Coverage",
      "start": "2026-01-20T10:30:00",
      "end": "2026-01-20T17:00:00"
    }
  ],
  "1000012582.png": [
    ...
  ]
}
```

Save as `ground_truth.json`, then test:

```bash
python test_comparison.py --ground-truth ground_truth.json
```

This provides absolute accuracy measurements against known data.

## 🧪 Test Scenarios

### Scenario 1: New Image Format

When you have a new schedule format:

1. **Test both parsers**:
   ```bash
   python test_comparison.py --images screenshots/new_format.png
   ```

2. **Review results**:
   - If LLM succeeds but ML fails → ML patterns need updating
   - If both fail → Image preprocessing might need adjustment
   - If both succeed → Great! Both are robust

### Scenario 2: ML Pattern Updates

After modifying regex patterns in `calhero_ml.py`:

1. **Run full test suite**:
   ```bash
   python test_comparison.py
   ```

2. **Compare with previous results**:
   - Did F1 score improve?
   - Are there new false positives/negatives?
   - Did processing time change?

### Scenario 3: Production Validation

Before deploying to production:

1. **Create ground truth** for your specific schedule format
2. **Test both parsers** against ground truth
3. **Choose parser** based on:
   - Accuracy requirements (use LLM if >99% needed)
   - Cost constraints (use ML if budget-limited)
   - Volume (ML is faster for high-volume processing)

## 📈 Interpreting Results

### When Both Parsers Agree (High F1)

This is the ideal scenario:
- Both found the same shifts
- Times match (within tolerance)
- You can confidently use either parser

**Recommendation**: Use ML version for cost savings

### When LLM Finds More Shifts

Possible reasons:
- ML OCR missed text (poor image quality)
- ML regex patterns too restrictive
- New format not handled by ML

**Action**:
- Check OCR output with `--debug` flag
- Update ML preprocessing or patterns
- Use LLM for this format

### When ML Finds More Shifts

Possible reasons:
- ML incorrectly parsed non-shift text
- LLM correctly filtered out noise
- ML patterns too permissive

**Action**:
- Review false positives
- Tighten ML regex patterns
- Add filters for common noise patterns

### When Times Differ Slightly

Small time differences (5-15 minutes) can occur due to:
- OCR misreading digits (e.g., "8" vs "3")
- AM/PM confusion
- Timezone handling

**Action**:
- Check if differences are systematic
- Adjust time parsing logic
- Consider if tolerance is acceptable

## 🛠️ Debugging Failed Tests

### Step 1: Identify Which Parser Failed

```bash
python test_comparison.py --images problem_image.png
```

Look for:
- "LLM found: 0 shifts" → LLM issue
- "ML found: 0 shifts" → ML/OCR issue
- Different counts → Parsing discrepancy

### Step 2: Debug LLM Parser

The LLM is usually accurate, but can fail if:
- Image format is very unusual
- API key issues
- Network problems

Test directly:
```bash
python calhero.py --dry-run
```

### Step 3: Debug ML Parser

Most ML failures are OCR-related:

```bash
# See what OCR extracted
python test_ocr.py screenshots/problem_image.png

# Run ML with debug mode
python calhero_ml.py --debug --dry-run
```

Common issues:
- **Low OCR confidence** (<70%) → Adjust preprocessing
- **Text not detected** → Check image quality/format
- **Text detected but not parsed** → Update regex patterns

### Step 4: Image Preprocessing

If OCR is failing, try adjusting preprocessing in `calhero_ml.py`:

```python
# Original
_, binary = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

# For darker images, try lower threshold
_, binary = cv2.threshold(gray, 120, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

# For very noisy images, try adaptive threshold
binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                cv2.THRESH_BINARY, 11, 2)
```

## 📊 Sample Test Report

Here's what a typical test run looks like:

```
🧪 CALENDAR PARSER COMPARISON TEST SUITE
======================================================================

Testing 3 image(s)...

======================================================================
Testing: 1000012581.png
======================================================================

[1] Running LLM parser...
    ✅ Found 4 shifts in 1.23s

[2] Running ML/OCR parser...
    ✅ Found 4 shifts in 0.56s

[3] Comparing results...

📊 Results:
  LLM found: 4 shifts (1.23s)
  ML found:  4 shifts (0.56s)
  Matches:   4 shifts
  F1 Score:  100.00%

======================================================================
Testing: 1000012582.png
======================================================================
...

======================================================================
📈 AGGREGATE STATISTICS
======================================================================

Total shifts found:
  LLM:     12 shifts
  ML/OCR:  11 shifts
  Matched: 11 shifts

Accuracy:
  Average F1 Score: 95.65%
  LLM Precision:    91.67%
  ML Precision:     100.00%

Performance:
  LLM avg time: 1.15s per image
  ML avg time:  0.52s per image
  Speed ratio:  2.2x

💡 Recommendation:
  ✅ Both parsers work well (F1: 95.65%)
  → Use LLM for better accuracy, ML for learning/cost savings
```

## 🎓 Learning Exercises

### Exercise 1: Measure Baseline
1. Run test suite on your images
2. Record F1 scores and processing times
3. This is your baseline for improvements

### Exercise 2: Improve ML Accuracy
1. Identify images where ML fails
2. Debug with `test_ocr.py`
3. Adjust preprocessing/patterns
4. Re-test and compare F1 scores

### Exercise 3: Create Ground Truth
1. Manually annotate 5 images
2. Save as `ground_truth.json`
3. Test both parsers against ground truth
4. Measure absolute accuracy

### Exercise 4: Performance Optimization
1. Profile both parsers
2. Identify bottlenecks
3. Optimize (e.g., batch processing, caching)
4. Measure improvement

## 🔗 Related Documentation

- [ML_GUIDE.md](ML_GUIDE.md) - Learn about ML/OCR techniques
- [COMPARISON.md](COMPARISON.md) - Detailed feature comparison
- [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - Command cheat sheet

## 💡 Best Practices

1. **Test regularly** - Run tests after any code changes
2. **Use ground truth** - For critical applications, maintain ground truth data
3. **Track metrics** - Save test results to track improvements over time
4. **Understand failures** - Don't just look at F1, understand why parsers differ
5. **Balance trade-offs** - Consider accuracy, speed, and cost together

---

*Happy Testing! 🧪*
