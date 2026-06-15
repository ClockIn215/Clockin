# Machine Learning Version - Learning Guide

This guide explains the ML/OCR version of the calendar parser and how it differs from the LLM-based approach.

## 🎓 What You'll Learn

### 1. **Computer Vision & OCR**
   - How OCR (Optical Character Recognition) works
   - Image preprocessing techniques to improve ML model accuracy
   - Using Tesseract OCR (which uses LSTM neural networks internally)

### 2. **Pattern Recognition**
   - Regex for extracting structured data from unstructured text
   - Feature extraction from raw text
   - Data normalization and structuring

### 3. **Traditional ML vs. Modern LLMs**
   - Understanding the differences between rule-based parsing and LLM inference
   - When to use traditional ML vs. modern AI approaches

---

## 📊 Architecture Comparison

### Original Version (`calhero.py`)
```
Image → Google Gemini API → Structured JSON → Google Calendar
```
- **Pros**: Extremely accurate, handles complex layouts, minimal code
- **Cons**: Requires API key, costs money, black-box processing

### ML Version (`calhero_ml.py`)
```
Image → Preprocessing → OCR (Tesseract) → Text Parsing → Structured Data → Calendar
```
- **Pros**: Free, transparent, runs locally, great for learning
- **Cons**: Requires more code, sensitive to image quality, needs pattern tuning

---

## 🛠️ Setup Instructions

### Step 1: Install Tesseract OCR Engine

Tesseract is the actual OCR engine. `pytesseract` is just a Python wrapper.

**macOS:**
```bash
brew install tesseract
```

**Ubuntu/Debian:**
```bash
sudo apt-get install tesseract-ocr
```

**Windows:**
Download installer from: https://github.com/UB-Mannheim/tesseract/wiki

### Step 2: Install Python Dependencies

```bash
# Activate your virtual environment
source calenv/bin/activate

# Install ML dependencies
pip install -r requirements_ml.txt
```

### Step 3: Verify Installation

```bash
# Check Tesseract is installed
tesseract --version

# Should show: tesseract 5.x.x
```

---

## 🚀 Usage

### Basic Run
```bash
python calhero_ml.py
```

### Dry Run (Preview without creating events)
```bash
python calhero_ml.py --dry-run
```

### Debug Mode (See raw OCR output)
```bash
python calhero_ml.py --debug
```

### Force Create (Even if duplicates exist)
```bash
python calhero_ml.py --force
```

---

## 🔬 How It Works - Deep Dive

### Phase 1: Image Preprocessing
```python
def preprocess_image_for_ocr(image_path):
    # 1. Convert to grayscale (reduces 3 color channels to 1)
    # 2. Apply thresholding (makes text black on white background)
    # 3. Denoise (removes artifacts that confuse OCR)
```

**Why this matters:**
- OCR models are trained on clean, high-contrast text
- Preprocessing improves accuracy from ~70% to ~95%+
- Similar to how you'd normalize data before feeding to any ML model

### Phase 2: OCR Text Extraction
```python
def extract_text_from_image(image_path):
    # Uses Tesseract OCR (LSTM neural network)
    # - LSTM = Long Short-Term Memory (type of RNN)
    # - Trained on millions of text samples
    # - Recognizes character patterns from pixels
```

**ML Concept:**
- Tesseract uses deep learning (LSTM networks) trained on diverse text data
- PSM (Page Segmentation Mode) helps model understand layout
- Similar to how image classifiers work, but outputs text instead of labels

### Phase 3: Pattern Recognition & Parsing
```python
def parse_shift_from_line(line, week_start):
    # 1. Extract day/date: "Mon 19"
    # 2. Extract time range: "12:00 PM - 06:00 PM"
    # 3. Extract shift type: "Coverage", "Training"
    # 4. Convert to ISO datetime format
```

**ML Concept:**
- Feature extraction: Pulling specific information from unstructured data
- Pattern matching: Using regex (hand-crafted patterns) vs. learned patterns
- Data normalization: Converting various formats to consistent structure

### Phase 4: Validation & Upload
```python
def process_image_with_ml(service, file_path, args):
    # Full ML pipeline:
    # Data → Preprocessing → Model → Post-processing → Action
```

**ML Pipeline:**
1. **Data acquisition**: Load image
2. **Preprocessing**: Enhance image quality
3. **Model inference**: Run OCR to extract text
4. **Post-processing**: Parse and structure data
5. **Action**: Upload to calendar

This is the same workflow used in production ML systems!

---

## 🤔 Common Issues & Solutions

### Issue: OCR Not Detecting Text
**Solution:** 
- Check if Tesseract is installed: `tesseract --version`
- Try `--debug` flag to see raw OCR output
- Image might need better preprocessing (adjust threshold values)

### Issue: Wrong Dates/Times Parsed
**Solution:**
- Check date range format in screenshot header
- Regex patterns in `parse_shift_from_line()` might need adjustment
- Use `--debug` to see what OCR extracted

### Issue: Some Shifts Not Detected
**Solution:**
- OCR might have misread text (check with `--debug`)
- Adjust preprocessing parameters (threshold, denoise strength)
- Add more pattern variations to regex

---

## 📚 Learning Exercises

### Exercise 1: Improve OCR Accuracy
Try different preprocessing techniques:
- Adjust threshold values in `preprocess_image_for_ocr()`
- Try different OpenCV filters (Gaussian blur, adaptive threshold)
- Compare accuracy before/after

### Exercise 2: Handle New Schedule Formats
Modify `parse_shift_from_line()` to handle:
- Different time formats (24-hour time)
- Multiple locations
- Break times

### Exercise 3: Add Confidence Scoring
Modify OCR to return confidence scores:
```python
# Use image_to_data instead of image_to_string
data = pytesseract.image_to_data(image, output_type=Output.DICT)
# Extract confidence scores for each word
```

### Exercise 4: Compare with LLM Version
Run both versions on same images:
- Compare accuracy
- Compare speed
- Compare edge cases (unusual formatting)

---

## 🆚 When to Use Each Approach

### Use ML/OCR Version When:
- ✅ Learning about traditional ML techniques
- ✅ Budget constraints (no API costs)
- ✅ Privacy concerns (runs locally)
- ✅ Consistent, structured layouts
- ✅ Need full transparency/explainability

### Use LLM Version When:
- ✅ Variable/complex layouts
- ✅ Need natural language understanding
- ✅ Time to market is critical
- ✅ High accuracy is paramount
- ✅ Budget allows for API costs

---

## 🎯 Key Takeaways

1. **OCR is ML**: Tesseract uses LSTM neural networks, not just template matching
2. **Preprocessing matters**: Good data preparation is 80% of ML success
3. **Rule-based has limits**: Regex works well for structured data, struggles with variety
4. **LLMs are powerful**: But traditional ML is still relevant for specific tasks
5. **Pipelines are important**: Real ML systems chain multiple steps together

---

## 🔗 Further Reading

- [Tesseract OCR Documentation](https://tesseract-ocr.github.io/)
- [OpenCV Tutorials](https://docs.opencv.org/master/d9/df8/tutorial_root.html)
- [Understanding LSTM Networks](http://colah.github.io/posts/2015-08-Understanding-LSTMs/)
- [Computer Vision Course](https://www.coursera.org/learn/intro-computer-vision-watson-opencv)

---

## 💡 Next Steps

1. Run both versions on your screenshots
2. Use `--debug` to understand what OCR is seeing
3. Experiment with preprocessing parameters
4. Try handling a different schedule format
5. Build something new with OCR!

Happy learning! 🚀
