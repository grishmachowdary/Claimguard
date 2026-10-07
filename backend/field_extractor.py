"""
Field Extractor - Extract structured fields from document text.

Combines spaCy Named Entity Recognition (NER) with regex patterns
to extract insurance-specific fields like policy numbers, amounts, dates.
"""

import re
import logging
from datetime import datetime
from typing import Dict, Optional, List, Tuple

logger = logging.getLogger(__name__)

# Lazy-load spaCy model
_nlp = None

def get_nlp():
    """
    Get or load spaCy model (lazy loading).
    
    Falls back to regex-only mode if model not available.
    
    Returns:
        spaCy language model or None if unavailable
    """
    global _nlp
    if _nlp is not None:
        return _nlp
    
    try:
        import spacy
        logger.info("Loading spaCy model en_core_web_sm...")
        _nlp = spacy.load("en_core_web_sm")
        logger.info("spaCy model loaded successfully")
        return _nlp
    except OSError:
        logger.warning("spaCy model 'en_core_web_sm' not found. Running in regex-only mode.")
        logger.info("To download the model, run: python -m spacy download en_core_web_sm")
        return None
    except Exception as e:
        logger.error(f"Failed to load spaCy model: {e}. Falling back to regex-only mode.")
        return None


def normalize_date(date_str: str) -> Optional[str]:
    """
    Parse various date formats and return ISO format YYYY-MM-DD.
    
    Handles: DD-MM-YYYY, DD/MM/YYYY, YYYY-MM-DD, etc.
    
    Args:
        date_str: Date string in various formats
        
    Returns:
        ISO format date string or None if parse fails
    """
    if not date_str:
        return None
    
    date_str = date_str.strip()
    
    # Common patterns
    patterns = [
        (r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})', lambda m: f"{m.group(3)}-{m.group(2).zfill(2)}-{m.group(1).zfill(2)}"),  # DD/MM/YYYY -> YYYY-MM-DD
        (r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})', lambda m: f"{m.group(1)}-{m.group(2).zfill(2)}-{m.group(3).zfill(2)}"),    # YYYY-MM-DD
    ]
    
    for pattern, formatter in patterns:
        match = re.search(pattern, date_str)
        if match:
            try:
                result = formatter(match)
                # Validate date
                datetime.strptime(result, '%Y-%m-%d')
                return result
            except:
                continue
    
    return None


def extract_fields(text: str) -> Dict:
    """
    Extract structured fields from document text.
    
    Returns dict with optional fields (all keys present, values None if not found):
    - claimant_name: string
    - policy_number: string
    - claim_date: string (ISO YYYY-MM-DD)
    - claim_amount: float
    - claimant_email: string
    - claimant_phone: string
    - incident_date: string (ISO YYYY-MM-DD)
    - hospital_name / provider_name: string
    - diagnosis: string
    - vehicle_number: string
    
    Also returns confidence dict with same structure, values 0.0-1.0.
    
    Args:
        text: OCR or manually provided text
        
    Returns:
        {'fields': {field_name: value, ...}, 'confidence': {field_name: score, ...}}
    """
    
    if not text or not isinstance(text, str):
        return {'fields': {}, 'confidence': {}}
    
    text = text.strip()
    if not text:
        return {'fields': {}, 'confidence': {}}
    
    fields = {}
    confidence = {}
    
    # ─── CLAIMANT NAME (spaCy PERSON entity) ───
    nlp = get_nlp()
    if nlp:
        try:
            doc = nlp(text[:5000])  # Limit to first 5000 chars for performance
            persons = [ent.text for ent in doc.ents if ent.label_ == 'PERSON']
            if persons:
                fields['claimant_name'] = persons[0]
                confidence['claimant_name'] = 0.85
            else:
                fields['claimant_name'] = None
                confidence['claimant_name'] = 0.0
        except Exception as e:
            logger.warning(f"spaCy NER failed: {e}")
            fields['claimant_name'] = None
            confidence['claimant_name'] = 0.0
    else:
        fields['claimant_name'] = None
        confidence['claimant_name'] = 0.0
    
    # ─── POLICY NUMBER (regex) ───
    policy_match = re.search(r'(?:policy\s+(?:number|no\.?|#)?\s*)?([A-Z]{2,4}[\d\-]{6,15})', text, re.IGNORECASE)
    if policy_match:
        fields['policy_number'] = policy_match.group(1)
        confidence['policy_number'] = 0.90
    else:
        fields['policy_number'] = None
        confidence['policy_number'] = 0.0
    
    # ─── CLAIM AMOUNT (regex: currency patterns) ───
    amount_match = re.search(
        r'(?:claim\s+amount|amount\s+claimed|rs\.?|inr|₹)\s*[\:\s]*(?:(?:Rs|INR|₹)\s*)?([0-9,]+(?:\.[0-9]{2})?)',
        text,
        re.IGNORECASE
    )
    if amount_match:
        try:
            amount_str = amount_match.group(1).replace(',', '')
            fields['claim_amount'] = float(amount_str)
            confidence['claim_amount'] = 0.88
        except:
            fields['claim_amount'] = None
            confidence['claim_amount'] = 0.0
    else:
        fields['claim_amount'] = None
        confidence['claim_amount'] = 0.0
    
    # ─── CLAIM DATE (regex: date patterns) ───
    claim_date_patterns = [
        r'(?:claim\s+(?:date|submitted)\s*(?::|-)?\s*)(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
        r'(?:on\s+)?(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
    ]
    claim_date = None
    for pattern in claim_date_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            claim_date = normalize_date(match.group(1))
            if claim_date:
                break
    
    if claim_date:
        fields['claim_date'] = claim_date
        confidence['claim_date'] = 0.85
    else:
        fields['claim_date'] = None
        confidence['claim_date'] = 0.0
    
    # ─── EMAIL ───
    email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
    if email_match:
        fields['claimant_email'] = email_match.group(0).lower()
        confidence['claimant_email'] = 0.95
    else:
        fields['claimant_email'] = None
        confidence['claimant_email'] = 0.0
    
    # ─── PHONE NUMBER (regex: Indian phone format) ───
    phone_match = re.search(r'(?:phone|mobile|contact|tel)\s*(?::|#)?\s*(?:\+91[-\s]?)?([6-9]\d{9})', text, re.IGNORECASE)
    if phone_match:
        fields['claimant_phone'] = phone_match.group(1)
        confidence['claimant_phone'] = 0.90
    else:
        fields['claimant_phone'] = None
        confidence['claimant_phone'] = 0.0
    
    # ─── INCIDENT DATE ───
    incident_match = re.search(
        r'(?:incident|accident|loss|event)\s+(?:date|occurred|on)\s*(?::|-)?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
        text,
        re.IGNORECASE
    )
    if incident_match:
        incident_date = normalize_date(incident_match.group(1))
        if incident_date:
            fields['incident_date'] = incident_date
            confidence['incident_date'] = 0.85
        else:
            fields['incident_date'] = None
            confidence['incident_date'] = 0.0
    else:
        fields['incident_date'] = None
        confidence['incident_date'] = 0.0
    
    # ─── HOSPITAL/PROVIDER NAME (spaCy ORG entity) ───
    if nlp:
        try:
            doc = nlp(text[:5000])
            orgs = [ent.text for ent in doc.ents if ent.label_ == 'ORG']
            if orgs:
                fields['hospital_name'] = orgs[0]
                fields['provider_name'] = orgs[0]
                confidence['hospital_name'] = 0.80
                confidence['provider_name'] = 0.80
            else:
                fields['hospital_name'] = None
                fields['provider_name'] = None
                confidence['hospital_name'] = 0.0
                confidence['provider_name'] = 0.0
        except:
            fields['hospital_name'] = None
            fields['provider_name'] = None
            confidence['hospital_name'] = 0.0
            confidence['provider_name'] = 0.0
    else:
        fields['hospital_name'] = None
        fields['provider_name'] = None
        confidence['hospital_name'] = 0.0
        confidence['provider_name'] = 0.0
    
    # ─── DIAGNOSIS (keyword context extraction) ───
    diagnosis_match = re.search(
        r'(?:diagnosis|condition|disease|illness)\s*(?::|=)?\s*([A-Za-z\s,]+?)(?:\n|$|;)',
        text,
        re.IGNORECASE
    )
    if diagnosis_match:
        diag = diagnosis_match.group(1).strip()
        fields['diagnosis'] = diag[:100] if len(diag) > 100 else diag
        confidence['diagnosis'] = 0.75
    else:
        fields['diagnosis'] = None
        confidence['diagnosis'] = 0.0
    
    # ─── VEHICLE NUMBER (regex: Indian vehicle plate format) ───
    # Pattern: XX-XX-0000 or XXXX-00 or similar
    vehicle_match = re.search(r'(?:vehicle|car|bike|registration|number)\s*(?::|#)?\s*([A-Z]{2}\d{1,2}[A-Z]{2}\d{4})', text, re.IGNORECASE)
    if vehicle_match:
        fields['vehicle_number'] = vehicle_match.group(1)
        confidence['vehicle_number'] = 0.92
    else:
        fields['vehicle_number'] = None
        confidence['vehicle_number'] = 0.0
    
    # Remove None values for cleaner output
    fields = {k: v for k, v in fields.items() if v is not None}
    confidence = {k: v for k, v in confidence.items() if k in fields}
    
    return {
        'fields': fields,
        'confidence': confidence
    }
