# Quick Reference Guide

## 📋 File Overview

| File | Purpose |
|------|---------|
| **Core Scripts** | |
| `calendar_utils.py` | 🆕 Shared utilities (no duplicate code!) |
| `calhero.py` | LLM-based parser (uses shared utils) |
| `calhero_ml.py` | ML/OCR-based parser (uses shared utils) |
| **Testing & Utilities** | |
| `test_comparison.py` | 🆕 Compare accuracy of both parsers |
| `test_ocr.py` | Test OCR setup and see raw extraction |
| **Configuration** | |
| `requirements.txt` | Dependencies for LLM version |
| `requirements_ml.txt` | Dependencies for ML version |
| **Documentation** | |
| `TESTING_GUIDE.md` | 🆕 How to test and compare versions |
| `ML_GUIDE.md` | Complete ML learning tutorial |
| `COMPARISON.md` | Detailed comparison of both approaches |
| `README.md` | Main documentation |

## 🚀 Installation Cheat Sheet

### For ML/OCR Version (Recommended for Learning)

**macOS:**
```bash
brew install tesseract
source calenv/bin/activate
pip install -r requirements_ml.txt
```

**Linux:**
```bash
sudo apt-get install tesseract-ocr
source calenv/bin/activate
pip install -r requirements_ml.txt
```

**Windows:**
1. Download Tesseract: https://github.com/UB-Mannheim/tesseract/wiki
2. Install and add to PATH
3. `pip install -r requirements_ml.txt`

## 🎯 Command Cheat Sheet

### Test & Compare
```bash
# 🆕 Compare both parsers (recommended first step!)
python test_comparison.py

# Compare specific images
python test_comparison.py --images screenshots/processed/*.png

# Save comparison results
python test_comparison.py --output results.json
```

### Test Your Setup
```bash
# Test OCR on a specific image
python test_ocr.py screenshots/processed/1000012581.png

# Check Tesseract version
tesseract --version
```

### Run the Parsers
```bash
# ML version - dry run (safe testing)
python calhero_ml.py --dry-run

# ML version - see OCR output for debugging
python calhero_ml.py --debug --dry-run

# ML version - actually create events
python calhero_ml.py

# LLM version
python calhero.py
```

### Common Flags
- `--dry-run`: Preview only, don't create events or move files
- `--debug`: Show detailed OCR output (ML version only)
- `--force`: Create events even if duplicates exist

## 🔍 Troubleshooting

### "tesseract: command not found"
**Solution:** Install Tesseract OCR engine
```bash
brew install tesseract  # macOS
sudo apt-get install tesseract-ocr  # Linux
```

### "No shifts detected in image"
**Solution:** Use debug mode to see what OCR extracted
```bash
python calhero_ml.py --debug
```
Check if:
- Date range format matches: `MM/DD/YYYY - MM/DD/YYYY`
- Time format matches: `HH:MM AM/PM`

### Low OCR Confidence (<70%)
**Solution:** Adjust preprocessing in `calhero_ml.py`
```python
# Try different threshold values
_, binary = cv2.threshold(gray, 130, 255, cv2.THRESH_BINARY)  # Lower from 150
```

### Wrong Times/Dates Parsed
**Solution:** Check regex patterns in `parse_shift_from_line()`
Use test script to see raw OCR output:
```bash
python test_ocr.py screenshots/your_image.png
```

## 📊 ML Pipeline Overview

```
1. IMAGE INPUT
   └── screenshots/schedule.png

2. PREPROCESSING (improves OCR)
   ├── Convert to grayscale
   ├── Apply thresholding
   └── Denoise

3. OCR EXTRACTION (Tesseract LSTM)
   └── Raw text: "Mon 19 12:00 PM - 06:00 PM..."

4. TEXT PARSING (Regex patterns)
   ├── Extract dates
   ├── Extract times
   └── Extract shift types

5. DATA STRUCTURING
   └── JSON: {"summary": "...", "start": "...", "end": "..."}

6. CALENDAR UPLOAD
   └── Google Calendar API

7. FILE MANAGEMENT
   └── Move to screenshots/processed/
```

## 🎓 Learning Path

### Beginner (1-2 hours)
1. ✅ Install Tesseract and dependencies
2. ✅ Run `test_comparison.py` to see both parsers in action
3. ✅ Run `test_ocr.py` on your screenshots
4. ✅ Run `calhero_ml.py --dry-run --debug`
5. ✅ Read through `calhero_ml.py` code comments

### Intermediate (3-5 hours)
1. ✅ Understand shared utilities in `calendar_utils.py`
2. ✅ Modify preprocessing parameters in ML version
3. ✅ Add new regex patterns for different formats
4. ✅ Run test comparisons after changes
5. ✅ Read ML_GUIDE.md and TESTING_GUIDE.md

### Advanced (5+ hours)
1. ✅ Implement confidence scoring
2. ✅ Create ground truth data and validate
3. ✅ Add support for multiple schedule formats
4. ✅ Create hybrid OCR+LLM approach
5. ✅ Build similar parser for different document type

## 💡 Key ML Concepts Demonstrated

| Concept | Where in Code | Learn More |
|---------|---------------|------------|
| **Computer Vision** | `preprocess_image_for_ocr()` | OpenCV docs |
| **OCR/Deep Learning** | `extract_text_from_image()` | Tesseract LSTM |
| **Feature Extraction** | `parse_shift_from_line()` | Regex tutorials |
| **Data Normalization** | `extract_shifts_from_text()` | Data science basics |
| **ML Pipeline** | `process_image_with_ml()` | ML workflow patterns |

## 🔗 Quick Links

- [Tesseract OCR Docs](https://tesseract-ocr.github.io/)
- [OpenCV Python Tutorials](https://docs.opencv.org/master/d6/d00/tutorial_py_root.html)
- [Regex Tutorial](https://regexone.com/)
- [LSTM Networks Explained](http://colah.github.io/posts/2015-08-Understanding-LSTMs/)

## 📈 Next Steps After Learning

1. **Try different schedule formats** - Modify patterns for your specific needs
2. **Build a web interface** - Use Flask/Streamlit to upload images
3. **Add more ML models** - Try different OCR engines (EasyOCR, PaddleOCR)
4. **Create a mobile app** - React Native + this backend
5. **Apply to other documents** - Receipts, forms, invoices, etc.

---

*Happy Learning! 🚀*
