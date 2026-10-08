"""
Data Validator Module
Validates individual fields against type, format, and range constraints.
Returns validation results with specific error messages and confidence scores.
"""

import re
from datetime import datetime, timedelta
from typing import Tuple, Dict, Any, Optional, List


def validate_date(value: str, field_name: str = 'date', allow_future: bool = False) -> Tuple[bool, Optional[str], float]:
    """
    Validate and parse a date field.
    Tries multiple date formats (YYYY-MM-DD, DD/MM/YYYY, MM/DD/YYYY).
    Checks: valid parse, not future (unless allow_future=True), not older than 5 years.
    
    Returns: (valid: bool, error_msg: str or None, confidence: float)
    """
    if not value:
        return False, 'Date is empty', 0.0
    
    if isinstance(value, str):
        value = value.strip()
    
    # Try multiple date formats
    formats = ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%d-%m-%Y']
    parsed_date = None
    
    for fmt in formats:
        try:
            parsed_date = datetime.strptime(value, fmt)
            break
        except ValueError:
            continue
    
    if parsed_date is None:
        return False, f'Invalid date format. Expected YYYY-MM-DD, DD/MM/YYYY, or MM/DD/YYYY, got: {value}', 0.1
    
    today = datetime.now()
    
    # Check if future date
    if parsed_date > today and not allow_future:
        return False, f'{field_name} is in the future ({value})', 0.2
    
    # Check if older than 5 years
    five_years_ago = today - timedelta(days=5*365)
    if parsed_date < five_years_ago:
        years_old = (today - parsed_date).days / 365
        return False, f'{field_name} is {int(years_old)} years old (outside last 5 years)', 0.3
    
    return True, None, 0.95


def validate_amount(value: Any, field_name: str = 'amount') -> Tuple[bool, Optional[str], float]:
    """
    Validate a numeric amount field.
    Checks: valid numeric parse, positive, < 10,000,000 (ten million realistic limit).
    
    Returns: (valid: bool, error_msg: str or None, confidence: float)
    """
    if value is None or value == '':
        return False, f'{field_name} is empty', 0.0
    
    try:
        amount = float(value)
    except (ValueError, TypeError):
        return False, f'{field_name} is not a valid number: {value}', 0.1
    
    if amount <= 0:
        return False, f'{field_name} must be positive, got: {amount}', 0.2
    
    if amount >= 10_000_000:
        return False, f'{field_name} exceeds maximum allowed (10,000,000), got: {amount}', 0.3
    
    return True, None, 0.95


def validate_text(value: str, field_name: str = 'text', min_length: int = 5) -> Tuple[bool, Optional[str], float]:
    """
    Validate a text field.
    Checks: minimum length, not entirely numeric, not a single generic word.
    
    Returns: (valid: bool, error_msg: str or None, confidence: float)
    """
    if not value:
        return False, f'{field_name} is empty', 0.0
    
    if isinstance(value, str):
        value = value.strip()
    
    if len(value) < min_length:
        return False, f'{field_name} too short (minimum {min_length} characters), got: {value}', 0.2
    
    # Check for vague single-word diagnoses/descriptions
    words = value.lower().split()
    if len(words) == 1:
        generic_words = ['fever', 'pain', 'ache', 'cold', 'cough', 'rash', 'wound', 'injury', 
                        'illness', 'disease', 'issue', 'problem', 'accident', 'incident']
        if value.lower() in generic_words:
            return False, f'{field_name} too vague or generic: {value}', 0.3
    
    # Check if entirely numeric (invalid for text fields like diagnosis)
    if value.replace('.', '').replace('-', '').isdigit():
        return False, f'{field_name} should not be entirely numeric: {value}', 0.2
    
    return True, None, 0.90


def validate_hospital_name(value: str) -> Tuple[bool, Optional[str], float]:
    """
    Validate hospital/provider name.
    Checks: minimum 4 characters, not truncated.
    
    Returns: (valid: bool, error_msg: str or None, confidence: float)
    """
    if not value:
        return False, 'Hospital/provider name is empty', 0.0
    
    value = value.strip()
    
    if len(value) < 4:
        return False, f'Hospital/provider name too short (minimum 4 characters), got: {value}', 0.2
    
    return True, None, 0.90


def validate_policy_number(value: str) -> Tuple[bool, Optional[str], float]:
    """
    Validate policy number format.
    Pattern: alphanumeric, at least 6 characters.
    
    Returns: (valid: bool, error_msg: str or None, confidence: float)
    """
    if not value:
        return False, 'Policy number is empty', 0.0
    
    value = value.strip()
    
    if len(value) < 6:
        return False, f'Policy number too short (minimum 6 characters), got: {value}', 0.2
    
    # Check if alphanumeric (allow hyphens and underscores)
    if not re.match(r'^[a-zA-Z0-9\-_]+$', value):
        return False, f'Policy number contains invalid characters: {value}', 0.3
    
    return True, None, 0.90


def validate_phone(value: str) -> Tuple[bool, Optional[str], float]:
    """
    Validate phone number.
    Checks: 10 digits or standard international format.
    
    Returns: (valid: bool, error_msg: str or None, confidence: float)
    """
    if not value:
        return False, 'Phone number is empty', 0.0
    
    value = value.strip()
    # Remove common separators
    digits = re.sub(r'[\s\-()\.+]', '', value)
    
    # Check for 10 digits (typical Indian format) or 7-15 digits (international)
    if not re.match(r'^\d{10}$', digits) and not re.match(r'^\+?\d{7,15}$', digits):
        return False, f'Invalid phone format (expected 10 digits or +country-code), got: {value}', 0.3
    
    return True, None, 0.90


def validate_email(value: str) -> Tuple[bool, Optional[str], float]:
    """
    Validate email format using standard regex.
    
    Returns: (valid: bool, error_msg: str or None, confidence: float)
    """
    if not value:
        return False, 'Email is empty', 0.0
    
    value = value.strip()
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not re.match(email_regex, value):
        return False, f'Invalid email format: {value}', 0.3
    
    return True, None, 0.90


def validate_field(field_name: str, value: Any, context: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Main router function for field validation.
    Dispatches to appropriate validator based on field_name.
    
    Args:
        field_name: Name of the field being validated (e.g., 'admission_date', 'claim_amount')
        value: Value to validate
        context: Additional context (e.g., insurance_type, field constraints)
    
    Returns:
        {
            'valid': bool,
            'errors': [
                {'field': str, 'message': str, 'severity': 'HIGH'|'MEDIUM'|'LOW'},
                ...
            ],
            'confidence': float (0.0-1.0)
        }
    """
    if context is None:
        context = {}
    
    errors = []
    confidence = 0.5  # default for unknown fields
    valid = True
    
    # Date fields
    if field_name in ['admission_date', 'discharge_date', 'dob', 'date_of_birth', 
                      'travel_start_date', 'travel_end_date', 'incident_date',
                      'sowing_date', 'damage_date', 'policy_start_date', 'policy_end_date']:
        is_valid, error_msg, conf = validate_date(value, field_name=field_name)
        if not is_valid:
            severity = 'HIGH' if 'future' in (error_msg or '').lower() or 'years old' in (error_msg or '').lower() else 'MEDIUM'
            errors.append({
                'field': field_name,
                'message': error_msg,
                'severity': severity
            })
            valid = False
        confidence = conf
    
    # Amount fields
    elif field_name in ['claim_amount', 'policy_coverage', 'total_bill', 'sum_assured', 
                       'property_value', 'policy_premium', 'deductible']:
        is_valid, error_msg, conf = validate_amount(value, field_name=field_name)
        if not is_valid:
            errors.append({
                'field': field_name,
                'message': error_msg,
                'severity': 'HIGH'
            })
            valid = False
        confidence = conf
    
    # Diagnosis/description fields
    elif field_name in ['diagnosis', 'injury_description', 'damage_description', 'claim_reason']:
        is_valid, error_msg, conf = validate_text(value, field_name=field_name, min_length=5)
        if not is_valid:
            severity = 'MEDIUM' if 'vague' in (error_msg or '').lower() else 'MEDIUM'
            errors.append({
                'field': field_name,
                'message': error_msg,
                'severity': severity
            })
            valid = False
        confidence = conf
    
    # Hospital/provider name
    elif field_name in ['hospital_name', 'provider_name', 'hospital', 'clinic_name']:
        is_valid, error_msg, conf = validate_hospital_name(value)
        if not is_valid:
            errors.append({
                'field': field_name,
                'message': error_msg,
                'severity': 'MEDIUM'
            })
            valid = False
        confidence = conf
    
    # Policy number
    elif field_name in ['policy_number', 'policy_id']:
        is_valid, error_msg, conf = validate_policy_number(value)
        if not is_valid:
            errors.append({
                'field': field_name,
                'message': error_msg,
                'severity': 'MEDIUM'
            })
            valid = False
        confidence = conf
    
    # Phone
    elif field_name in ['phone', 'phone_number', 'mobile', 'contact_number']:
        is_valid, error_msg, conf = validate_phone(value)
        if not is_valid:
            errors.append({
                'field': field_name,
                'message': error_msg,
                'severity': 'LOW'
            })
            valid = False
        confidence = conf
    
    # Email
    elif field_name in ['email', 'email_address', 'contact_email']:
        is_valid, error_msg, conf = validate_email(value)
        if not is_valid:
            errors.append({
                'field': field_name,
                'message': error_msg,
                'severity': 'LOW'
            })
            valid = False
        confidence = conf
    
    # Unknown field: return valid=True with low confidence
    else:
        valid = True
        confidence = 0.5
    
    return {
        'valid': valid,
        'errors': errors,
        'confidence': confidence
    }
