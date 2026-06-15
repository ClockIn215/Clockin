"""
OCR Adapter - Switch between OCR engines easily
===============================================
Supports multiple OCR backends:
- Tesseract (default, fast, requires binary)
- EasyOCR (pure Python, accurate, larger)
- PaddleOCR (pure Python, fast, medium size)
- Google Cloud Vision (cloud API, most accurate)

Usage:
    from ocr_adapter import OCRAdapter
    
    # Use Tesseract (default)
    ocr = OCRAdapter('tesseract')
    text = ocr.extract_text('image.png')
    
    # Use EasyOCR (no binary needed)
    ocr = OCRAdapter('easyocr')
    text = ocr.extract_text('image.png')
"""

from pathlib import Path
from typing import Optional, Literal
import cv2
import numpy as np

OCREngine = Literal['tesseract', 'easyocr', 'paddleocr', 'cloud_vision']


class OCRAdapter:
    """Unified interface for multiple OCR engines."""
    
    def __init__(self, engine: OCREngine = 'tesseract'):
        """
        Initialize OCR adapter.
        
        Args:
            engine: OCR engine to use
        """
        self.engine = engine
        self._reader = None  # Lazy initialization
        
    def extract_text(self, image_path: Path, preprocess: bool = True) -> str:
        """
        Extract text from image using selected OCR engine.
        
        Args:
            image_path: Path to image file
            preprocess: Whether to preprocess image for better results
            
        Returns:
            Extracted text as string
        """
        if preprocess:
            image = self._preprocess_image(image_path)
        else:
            image = cv2.imread(str(image_path))
        
        if self.engine == 'tesseract':
            return self._extract_tesseract(image)
        elif self.engine == 'easyocr':
            return self._extract_easyocr(image_path)
        elif self.engine == 'paddleocr':
            return self._extract_paddleocr(image_path)
        elif self.engine == 'cloud_vision':
            return self._extract_cloud_vision(image_path)
        else:
            raise ValueError(f"Unknown OCR engine: {self.engine}")
    
    def _preprocess_image(self, image_path: Path) -> np.ndarray:
        """Preprocess image for better OCR accuracy."""
        img = cv2.imread(str(image_path))
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, binary = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        denoised = cv2.bilateralFilter(binary, 9, 75, 75)
        return denoised
    
    # ========================================
    # TESSERACT (REQUIRES BINARY)
    # ========================================
    
    def _extract_tesseract(self, image: np.ndarray) -> str:
        """Extract text using Tesseract OCR."""
        import pytesseract
        
        custom_config = r'--oem 3 --psm 6'
        text = pytesseract.image_to_string(image, config=custom_config)
        return text
    
    # ========================================
    # EASYOCR (PURE PYTHON)
    # ========================================
    
    def _extract_easyocr(self, image_path: Path) -> str:
        """
        Extract text using EasyOCR (pure Python).
        
        Pros:
        - No binary dependencies
        - Very accurate
        - GPU support
        
        Cons:
        - Slower (~2-3x)
        - Large model download (~500MB)
        - Higher memory usage
        """
        import easyocr
        
        # Lazy initialization (cache reader)
        if self._reader is None:
            print("Initializing EasyOCR (first run downloads ~500MB model)...")
            self._reader = easyocr.Reader(['en'], gpu=False)
        
        # Extract text
        results = self._reader.readtext(str(image_path), detail=0)
        text = '\n'.join(results)
        return text
    
    # ========================================
    # PADDLEOCR (PURE PYTHON)
    # ========================================
    
    def _extract_paddleocr(self, image_path: Path) -> str:
        """
        Extract text using PaddleOCR (pure Python).
        
        Pros:
        - No binary dependencies
        - Fast (faster than EasyOCR)
        - Good accuracy
        
        Cons:
        - Medium model size (~400MB)
        - Less mature than Tesseract
        """
        from paddleocr import PaddleOCR
        
        # Lazy initialization
        if self._reader is None:
            print("Initializing PaddleOCR...")
            self._reader = PaddleOCR(use_angle_cls=True, lang='en', show_log=False)
        
        # Extract text
        result = self._reader.ocr(str(image_path), cls=True)
        
        # Parse results
        lines = []
        for line in result[0]:
            text = line[1][0]  # Extract text from tuple
            lines.append(text)
        
        return '\n'.join(lines)
    
    # ========================================
    # GOOGLE CLOUD VISION (API)
    # ========================================
    
    def _extract_cloud_vision(self, image_path: Path) -> str:
        """
        Extract text using Google Cloud Vision API.
        
        Pros:
        - Most accurate
        - No local dependencies
        - Handles any image quality
        
        Cons:
        - Costs money ($1.50/1000 images)
        - Requires internet
        - API latency
        """
        from google.cloud import vision
        
        client = vision.ImageAnnotatorClient()
        
        with open(image_path, 'rb') as f:
            content = f.read()
        
        image = vision.Image(content=content)
        response = client.text_detection(image=image)
        
        if response.error.message:
            raise Exception(f"Cloud Vision API error: {response.error.message}")
        
        if response.text_annotations:
            return response.text_annotations[0].description
        else:
            return ""


# ========================================
# CONVENIENCE FUNCTIONS
# ========================================

def get_best_ocr_engine() -> str:
    """
    Automatically detect best available OCR engine.
    
    Priority:
    1. Tesseract (if available) - fastest, most reliable
    2. EasyOCR (fallback) - pure Python
    3. PaddleOCR (alternative) - pure Python
    """
    try:
        import pytesseract
        pytesseract.get_tesseract_version()
        return 'tesseract'
    except:
        pass
    
    try:
        import easyocr
        return 'easyocr'
    except ImportError:
        pass
    
    try:
        import paddleocr
        return 'paddleocr'
    except ImportError:
        pass
    
    raise RuntimeError(
        "No OCR engine available. Install one of:\n"
        "  - Tesseract: brew install tesseract && pip install pytesseract\n"
        "  - EasyOCR: pip install easyocr\n"
        "  - PaddleOCR: pip install paddleocr"
    )


# ========================================
# EXAMPLE USAGE
# ========================================

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python ocr_adapter.py <image_path> [engine]")
        print("\nEngines: tesseract (default), easyocr, paddleocr, cloud_vision")
        print("\nExample:")
        print("  python ocr_adapter.py screenshots/schedule.png tesseract")
        print("  python ocr_adapter.py screenshots/schedule.png easyocr")
        sys.exit(1)
    
    image_path = Path(sys.argv[1])
    engine = sys.argv[2] if len(sys.argv) > 2 else get_best_ocr_engine()
    
    print(f"Using OCR engine: {engine}")
    print("=" * 60)
    
    ocr = OCRAdapter(engine)
    text = ocr.extract_text(image_path)
    
    print(text)
    print("=" * 60)
    print(f"Characters extracted: {len(text)}")
