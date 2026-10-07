#!/usr/bin/env python
"""Quick verification tests for Phase 3 modules."""

import sys

print("=" * 60)
print("Phase 3 Document Intelligence - Verification Tests")
print("=" * 60)

# Test 1: document_classifier
print("\n[1/4] Testing document_classifier...")
try:
    from document_classifier import classify_document
    test_text = 'Medical Report: Patient diagnosis treatment prescription clinical findings doctor hospital'
    result = classify_document(test_text)
    assert result['type'] in ['medical_report', 'medical_bill'], f"Expected medical document, got {result['type']}"
    assert result['confidence'] > 0.0, f"Expected confidence > 0.0, got {result['confidence']}"
    print(f"  ✓ Classified as: {result['type']} (confidence: {result['confidence']:.0%})")
except Exception as e:
    print(f"  ✗ FAILED: {e}")
    sys.exit(1)

# Test 2: field_extractor
print("\n[2/4] Testing field_extractor...")
try:
    from field_extractor import extract_fields
    test_text = 'Policy Number HDFC0012345 claim amount Rs. 50000 claim date 2024-01-15'
    result = extract_fields(test_text)
    fields = result.get('fields', {})
    # Should at least extract policy number and claim amount via regex
    assert 'policy_number' in fields or 'claim_amount' in fields, f"Expected regex extraction, got fields: {list(fields.keys())}"
    print(f"  ✓ Extracted {len(fields)} fields via regex: {list(fields.keys())}")
except Exception as e:
    print(f"  ✗ FAILED: {e}")
    sys.exit(1)

# Test 3: ocr_engine (import only, no model load needed yet)
print("\n[3/4] Testing ocr_engine...")
try:
    from ocr_engine import get_reader, extract_text, extract_text_with_boxes
    print(f"  ✓ ocr_engine imports successfully (modules available)")
    print(f"    - get_reader() ready for lazy loading")
    print(f"    - extract_text() available")
    print(f"    - extract_text_with_boxes() available")
except ImportError as e:
    if 'easyocr' in str(e):
        print(f"  ⚠ Note: easyocr not yet installed (expected, will be installed via requirements.txt)")
    else:
        print(f"  ✗ FAILED: {e}")
        sys.exit(1)
except Exception as e:
    print(f"  ✗ FAILED: {e}")
    sys.exit(1)

# Test 4: app.py imports
print("\n[4/4] Testing app.py imports...")
try:
    from app import app
    print(f"  ✓ app.py imports successfully")
    
    # Check that document intelligence is conditionally loaded
    import app as app_module
    ocr_available = app_module.OCR_AVAILABLE
    print(f"    - OCR_AVAILABLE flag set to: {ocr_available}")
except Exception as e:
    print(f"  ✗ FAILED: {e}")
    sys.exit(1)

print("\n" + "=" * 60)
print("All verification tests passed!")
print("=" * 60)
print("\nNext steps:")
print("1. pip install -r requirements.txt (to install easyocr, spacy, etc)")
print("2. python -m spacy download en_core_web_sm (to download spaCy model)")
print("3. Start the Flask app: python app.py")
print("=" * 60)
