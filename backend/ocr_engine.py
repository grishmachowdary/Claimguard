"""
OCR Engine - EasyOCR wrapper for document text extraction.

Provides singleton-based lazy loading of EasyOCR models to avoid
startup overhead. Supports both images and PDFs.
"""

import logging
import os
from pathlib import Path
from typing import Optional, Dict, List

logger = logging.getLogger(__name__)

# Singleton instance
_reader: Optional['easyocr.Reader'] = None
_easyocr_available = False

try:
    import easyocr
    _easyocr_available = True
except ImportError:
    logger.warning("easyocr not installed; OCR functions will not work until package is installed")


def get_reader() -> Optional['easyocr.Reader']:
    """
    Get or initialize the EasyOCR reader singleton.
    
    Lazy initialization: first call loads model (~2-3 seconds),
    subsequent calls return cached instance.
    
    Returns:
        easyocr.Reader: Initialized OCR reader, or None if easyocr is not available
        
    Raises:
        RuntimeError: If easyocr is not installed
    """
    global _reader
    
    if not _easyocr_available:
        raise RuntimeError("easyocr is not installed. Install with: pip install easyocr")
    
    if _reader is None:
        logger.info("Initializing EasyOCR reader (first run, ~2-3 seconds)...")
        _reader = easyocr.Reader(['en'], gpu=False)
        logger.info("EasyOCR reader initialized")
    return _reader


def extract_text(image_path: str) -> str:
    """
    Extract raw text from image or PDF file.
    
    Handles:
    - PNG, JPG, JPEG images (direct OCR)
    - PDF files (convert each page to image, then OCR)
    
    Args:
        image_path: Path to image or PDF file
        
    Returns:
        Concatenated text from all pages, or empty string on failure
        
    Raises:
        ValueError: If file doesn't exist or format is unsupported
    """
    path = Path(image_path)
    
    if not path.exists():
        raise ValueError(f"File not found: {image_path}")
    
    suffix = path.suffix.lower()
    
    # Handle PDF
    if suffix == '.pdf':
        try:
            from pdf2image import convert_from_path
            logger.info(f"Converting PDF to images: {image_path}")
            # Add timeout (30 seconds per page) to prevent hanging on corrupted PDFs
            pages = convert_from_path(image_path, timeout=30, first_page=1, last_page=None)
            all_text = []
            
            for page_num, page in enumerate(pages, 1):
                try:
                    reader = get_reader()
                    results = reader.readtext(page, detail=0)
                    page_text = '\n'.join(results) if results else ''
                    all_text.append(page_text)
                    logger.debug(f"Extracted text from PDF page {page_num}")
                except Exception as e:
                    logger.warning(f"Failed to OCR PDF page {page_num}: {e}")
                    continue
            
            combined = '\n'.join(all_text)
            logger.info(f"PDF OCR complete: {len(combined)} chars extracted")
            return combined
            
        except ImportError:
            logger.error("pdf2image not installed; cannot process PDF")
            return ""
        except Exception as e:
            logger.error(f"PDF processing failed: {e}")
            return ""
    
    # Handle image
    elif suffix in ['.png', '.jpg', '.jpeg']:
        try:
            reader = get_reader()
            results = reader.readtext(image_path, detail=0)
            text = '\n'.join(results) if results else ''
            logger.info(f"Image OCR complete: {len(text)} chars extracted")
            return text
        except Exception as e:
            logger.error(f"Image OCR failed: {e}")
            return ""
    
    else:
        raise ValueError(f"Unsupported file format: {suffix}")


def extract_text_with_boxes(image_path: str) -> List[Dict]:
    """
    Extract text with bounding boxes and confidence scores from image.
    
    Filters out results with confidence < 0.5.
    
    Args:
        image_path: Path to image file (images only, not PDF)
        
    Returns:
        List of dicts: [{'text': str, 'confidence': float, 'bbox': list}]
        Empty list on failure or unsupported format
        
    Raises:
        ValueError: If file doesn't exist or is unsupported format
    """
    path = Path(image_path)
    
    if not path.exists():
        raise ValueError(f"File not found: {image_path}")
    
    suffix = path.suffix.lower()
    
    if suffix == '.pdf':
        raise ValueError("extract_text_with_boxes does not support PDF; use extract_text() instead")
    
    if suffix not in ['.png', '.jpg', '.jpeg']:
        raise ValueError(f"Unsupported file format: {suffix}")
    
    try:
        reader = get_reader()
        results = reader.readtext(image_path, detail=1)
        
        # Extract boxes with confidence filter
        boxes = []
        for (bbox, text, confidence) in results:
            if confidence >= 0.5:
                boxes.append({
                    'text': text,
                    'confidence': float(confidence),
                    'bbox': [list(point) for point in bbox]
                })
        
        logger.info(f"Extracted {len(boxes)} text boxes from {image_path}")
        return boxes
        
    except Exception as e:
        logger.error(f"extract_text_with_boxes failed: {e}")
        return []
