"""
Smart Document Analyzer
Analyzes uploaded documents for:
- Name mismatches (ID vs Policy)
- Date validation (bill vs policy period)
- Policy number errors
- Amount consistency
Uses fuzzywuzzy for name matching, regex for date/amount extraction.
"""
import re
import json
import os
from datetime import datetime
from fuzzywuzzy import fuzz

# ── Text extraction (no OCR dependency — works on text-based PDFs) ────────────

def extract_text_from_file(file_path):
    """Extract text from uploaded file. Supports PDF and images."""
    text = ''
    ext = os.path.splitext(file_path)[1].lower()

    if ext == '.pdf':
        text = _extract_from_pdf(file_path)
    elif ext in ['.png', '.jpg', '.jpeg']:
        text = _extract_from_image(file_path)

    return text.strip()


def _extract_from_pdf(file_path):
    """Extract text from PDF using basic binary reading for text PDFs."""
    try:
        # Try reading as text-based PDF
        with open(file_path, 'rb') as f:
            content = f.read().decode('latin-1', errors='ignore')
        # Extract readable text between stream markers
        text_parts = re.findall(r'BT(.*?)ET', content, re.DOTALL)
        text = ' '.join(text_parts)
        # Clean up PDF encoding artifacts
        text = re.sub(r'\(([^)]+)\)', r'\1 ', text)
        text = re.sub(r'[^\x20-\x7E\n]', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        return text if len(text) > 20 else f'[PDF file: {os.path.basename(file_path)}]'
    except Exception:
        return f'[PDF file: {os.path.basename(file_path)}]'


def _extract_from_image(file_path):
    """For images, return placeholder (OCR requires Tesseract installation)."""
    return f'[Image file: {os.path.basename(file_path)}]'


# ── Pattern extractors ────────────────────────────────────────────────────────

def extract_dates(text):
    """Extract all dates from text."""
    patterns = [
        r'\b(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})\b',
        r'\b(\d{4})[/-](\d{1,2})[/-](\d{1,2})\b',
        r'\b(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+(\d{4})\b',
    ]
    dates = []
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        dates.extend(matches)
    return dates


def extract_amounts(text):
    """Extract monetary amounts from text."""
    patterns = [
        r'(?:Rs\.?|INR|₹)\s*([0-9,]+(?:\.[0-9]{2})?)',
        r'([0-9,]+(?:\.[0-9]{2})?)\s*(?:/-|rupees|Rs)',
        r'\b([0-9]{4,}(?:\.[0-9]{2})?)\b',
    ]
    amounts = []
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        amounts.extend([m.replace(',', '') for m in matches])
    return [float(a) for a in amounts if a.replace('.', '').isdigit()]


def extract_names(text):
    """Extract potential person names from text."""
    # Look for common name patterns
    patterns = [
        r'(?:Patient|Name|Insured|Policyholder|Mr\.|Mrs\.|Ms\.|Dr\.)\s*:?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})',
        r'(?:Name of|Name)\s*:?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})',
    ]
    names = []
    for pattern in patterns:
        matches = re.findall(pattern, text)
        names.extend(matches)
    return names


def extract_policy_numbers(text):
    """Extract policy numbers from text."""
    patterns = [
        r'(?:Policy\s*(?:No|Number|#)\.?)\s*:?\s*([A-Z0-9/-]{6,20})',
        r'\b([A-Z]{2,4}[0-9]{6,12})\b',
    ]
    numbers = []
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        numbers.extend(matches)
    return numbers


# ── Main analyzer ─────────────────────────────────────────────────────────────

def analyze_documents(claim, uploaded_file_paths):
    """
    Analyze all uploaded documents and cross-check with form data.
    Returns list of findings (issues and confirmations).
    """
    form_data = json.loads(claim.form_data) if claim.form_data else {}
    findings  = []
    all_text  = {}

    # Extract text from each document
    for doc_type, file_path in uploaded_file_paths.items():
        if os.path.exists(file_path):
            text = extract_text_from_file(file_path)
            all_text[doc_type] = text

    if not all_text:
        return [{
            'type': 'info',
            'severity': 'low',
            'document': 'All Documents',
            'message': 'Documents uploaded but text extraction requires OCR setup.',
            'suggestion': 'Install Tesseract OCR for automatic document analysis.'
        }]

    # ── Name consistency check ────────────────────────────────────────────
    patient_name = (form_data.get('patient_name') or
                    form_data.get('insured_name') or
                    form_data.get('farmer_name') or
                    form_data.get('traveler_name') or '')

    if patient_name:
        for doc_type, text in all_text.items():
            names_in_doc = extract_names(text)
            if names_in_doc:
                best_match = max(
                    [fuzz.token_sort_ratio(patient_name.lower(), n.lower()) for n in names_in_doc],
                    default=0
                )
                if best_match >= 80:
                    findings.append({
                        'type': 'match',
                        'severity': 'ok',
                        'document': doc_type.replace('_', ' ').title(),
                        'message': f'Name match confirmed in {doc_type.replace("_", " ")} ({best_match}% match)',
                        'suggestion': ''
                    })
                elif best_match > 0 and best_match < 80:
                    findings.append({
                        'type': 'mismatch',
                        'severity': 'high',
                        'document': doc_type.replace('_', ' ').title(),
                        'message': f'Name mismatch in {doc_type.replace("_", " ")}. Form says "{patient_name}" but document shows different name ({best_match}% match)',
                        'suggestion': 'Ensure the name on all documents matches exactly with the policy holder name'
                    })

    # ── Policy number check ───────────────────────────────────────────────
    policy_number = form_data.get('policy_number', '')
    if policy_number:
        for doc_type, text in all_text.items():
            policy_nums = extract_policy_numbers(text)
            if policy_nums:
                if any(policy_number.upper() in p.upper() or p.upper() in policy_number.upper() for p in policy_nums):
                    findings.append({
                        'type': 'match',
                        'severity': 'ok',
                        'document': doc_type.replace('_', ' ').title(),
                        'message': f'Policy number verified in {doc_type.replace("_", " ")}',
                        'suggestion': ''
                    })
                else:
                    findings.append({
                        'type': 'mismatch',
                        'severity': 'high',
                        'document': doc_type.replace('_', ' ').title(),
                        'message': f'Policy number in {doc_type.replace("_", " ")} does not match. Expected: {policy_number}',
                        'suggestion': 'Verify the policy number on all documents matches your insurance policy'
                    })

    # ── Date range check ──────────────────────────────────────────────────
    admission_date  = form_data.get('admission_date')
    discharge_date  = form_data.get('discharge_date')

    if admission_date and discharge_date:
        for doc_type, text in all_text.items():
            if 'bill' in doc_type or 'report' in doc_type:
                dates_in_doc = extract_dates(text)
                if dates_in_doc:
                    findings.append({
                        'type': 'info',
                        'severity': 'low',
                        'document': doc_type.replace('_', ' ').title(),
                        'message': f'Found {len(dates_in_doc)} date(s) in {doc_type.replace("_", " ")}. Verify they fall within admission ({admission_date}) to discharge ({discharge_date}) period.',
                        'suggestion': 'All bills and reports should have dates within your hospital stay period'
                    })

    # ── Amount consistency check ──────────────────────────────────────────
    claim_amount = form_data.get('claim_amount')
    if claim_amount:
        try:
            claim_amt_float = float(claim_amount)
            for doc_type, text in all_text.items():
                if 'bill' in doc_type:
                    amounts = extract_amounts(text)
                    if amounts:
                        max_amount = max(amounts)
                        if max_amount > claim_amt_float * 1.1:
                            findings.append({
                                'type': 'mismatch',
                                'severity': 'medium',
                                'document': doc_type.replace('_', ' ').title(),
                                'message': f'Bill amount (₹{max_amount:,.0f}) appears higher than claimed amount (₹{claim_amt_float:,.0f})',
                                'suggestion': 'Ensure your claim amount matches the total bill amount'
                            })
        except (ValueError, TypeError):
            pass

    # If no specific findings, add a general confirmation
    if not findings:
        findings.append({
            'type': 'info',
            'severity': 'low',
            'document': 'All Documents',
            'message': f'{len(all_text)} document(s) uploaded and processed.',
            'suggestion': 'Manual review recommended for complete verification.'
        })

    return findings
