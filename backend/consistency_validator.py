"""
Consistency Validator Module
Validates cross-field logical consistency.
Checks relationships between fields (e.g., discharge > admission, claim <= coverage).
"""

from datetime import datetime
from typing import Dict, List, Tuple, Any, Optional


def parse_date(date_str: str) -> Optional[datetime]:
    """
    Parse a date string in common formats.
    Returns datetime object or None if parse fails.
    """
    if not date_str:
        return None
    
    formats = ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%d-%m-%Y']
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return None


def _check_health(fields_dict: Dict[str, Any]) -> Tuple[bool, List[Dict], List[Dict]]:
    """
    Health insurance consistency checks.
    - discharge_date must be AFTER admission_date (HIGH if violated)
    - discharge_date must not be more than 365 days after admission_date (HIGH)
    - claim_amount must not exceed policy_coverage (HIGH)
    - admission_date must be within last 5 years (HIGH)
    - discharge_date must not be in the future (HIGH)
    - if stay < 2 days, flag as suspicious (MEDIUM warning)
    - if claim_amount >= 0.98 * policy_coverage, flag as suspicious (MEDIUM warning)
    """
    errors = []
    warnings = []
    
    adm_str = fields_dict.get('admission_date')
    dis_str = fields_dict.get('discharge_date')
    amt = fields_dict.get('claim_amount')
    cov = fields_dict.get('policy_coverage')
    
    adm = parse_date(adm_str)
    dis = parse_date(dis_str)
    
    # Rule 1: discharge_date must be AFTER admission_date
    if adm and dis:
        if dis <= adm:
            errors.append({
                'rule': 'discharge_after_admission',
                'message': 'Discharge date must be after admission date',
                'severity': 'HIGH'
            })
        else:
            # Rule 2: stay must not exceed 365 days
            stay_days = (dis - adm).days
            if stay_days > 365:
                errors.append({
                    'rule': 'stay_duration_reasonable',
                    'message': f'Hospital stay exceeds 365 days ({stay_days} days)',
                    'severity': 'HIGH'
                })
            
            # Rule 6: if stay < 2 days, flag as suspicious
            if stay_days < 2:
                warnings.append({
                    'rule': 'short_stay',
                    'message': f'Very short hospital stay ({stay_days} days) - suspicious',
                    'severity': 'MEDIUM'
                })
    
    # Rule 3: claim_amount must not exceed policy_coverage
    if amt and cov:
        try:
            amt_float = float(amt)
            cov_float = float(cov)
            if amt_float > cov_float:
                errors.append({
                    'rule': 'claim_within_coverage',
                    'message': f'Claim amount ({amt_float}) exceeds policy coverage ({cov_float})',
                    'severity': 'HIGH'
                })
            # Rule 7: if claim_amount >= 0.98 * policy_coverage, flag as suspicious
            elif amt_float >= 0.98 * cov_float:
                warnings.append({
                    'rule': 'claim_at_limit',
                    'message': f'Claim amount very close to policy limit ({amt_float} / {cov_float})',
                    'severity': 'MEDIUM'
                })
        except (ValueError, TypeError):
            pass
    
    # Rule 4: admission_date must be within last 5 years
    if adm:
        today = datetime.now()
        years_diff = (today - adm).days / 365
        if years_diff > 5:
            errors.append({
                'rule': 'admission_within_5_years',
                'message': f'Admission date is {int(years_diff)} years old (outside last 5 years)',
                'severity': 'HIGH'
            })
    
    # Rule 5: discharge_date must not be in the future
    if dis:
        today = datetime.now()
        if dis > today:
            errors.append({
                'rule': 'discharge_not_future',
                'message': f'Discharge date is in the future',
                'severity': 'HIGH'
            })
    
    # Rule 8: if admission_date is a Sunday AND time between 00:00-06:00, flag (LOW)
    # Note: We don't have time component, so we skip this check
    
    valid = len(errors) == 0
    return valid, errors, warnings


def _check_vehicle(fields_dict: Dict[str, Any]) -> Tuple[bool, List[Dict], List[Dict]]:
    """
    Vehicle insurance consistency checks.
    - claim_amount must not exceed policy_coverage
    """
    errors = []
    warnings = []
    
    amt = fields_dict.get('claim_amount')
    cov = fields_dict.get('policy_coverage')
    
    if amt and cov:
        try:
            amt_float = float(amt)
            cov_float = float(cov)
            if amt_float > cov_float:
                errors.append({
                    'rule': 'claim_within_coverage',
                    'message': f'Claim amount ({amt_float}) exceeds policy coverage ({cov_float})',
                    'severity': 'HIGH'
                })
        except (ValueError, TypeError):
            pass
    
    valid = len(errors) == 0
    return valid, errors, warnings


def _check_life(fields_dict: Dict[str, Any]) -> Tuple[bool, List[Dict], List[Dict]]:
    """
    Life insurance consistency checks.
    - claim amount should match sum_assured (with some tolerance)
    """
    errors = []
    warnings = []
    
    amt = fields_dict.get('claim_amount')
    sa = fields_dict.get('sum_assured')
    
    if amt and sa:
        try:
            amt_float = float(amt)
            sa_float = float(sa)
            diff = abs(amt_float - sa_float)
            if diff > 1000:
                errors.append({
                    'rule': 'claim_matches_sum_assured',
                    'message': f'Claim amount ({amt_float}) differs from sum assured ({sa_float}) by {diff}',
                    'severity': 'HIGH'
                })
        except (ValueError, TypeError):
            pass
    
    valid = len(errors) == 0
    return valid, errors, warnings


def _check_property(fields_dict: Dict[str, Any]) -> Tuple[bool, List[Dict], List[Dict]]:
    """
    Property insurance consistency checks.
    - claim_amount must not exceed property_value
    """
    errors = []
    warnings = []
    
    amt = fields_dict.get('claim_amount')
    val = fields_dict.get('property_value')
    
    if amt and val:
        try:
            amt_float = float(amt)
            val_float = float(val)
            if amt_float > val_float:
                errors.append({
                    'rule': 'claim_within_value',
                    'message': f'Claim amount ({amt_float}) exceeds property value ({val_float})',
                    'severity': 'HIGH'
                })
        except (ValueError, TypeError):
            pass
    
    valid = len(errors) == 0
    return valid, errors, warnings


def _check_travel(fields_dict: Dict[str, Any]) -> Tuple[bool, List[Dict], List[Dict]]:
    """
    Travel insurance consistency checks.
    - travel_end > travel_start
    - incident_date within travel period
    """
    errors = []
    warnings = []
    
    start_str = fields_dict.get('travel_start_date')
    end_str = fields_dict.get('travel_end_date')
    incident_str = fields_dict.get('incident_date')
    
    start = parse_date(start_str)
    end = parse_date(end_str)
    incident = parse_date(incident_str)
    
    # travel_end must be after travel_start
    if start and end:
        if end <= start:
            errors.append({
                'rule': 'travel_end_after_start',
                'message': 'Travel end date must be after start date',
                'severity': 'HIGH'
            })
    
    # incident_date must be within travel period
    if start and end and incident:
        if incident < start or incident > end:
            errors.append({
                'rule': 'incident_during_travel',
                'message': f'Incident date ({incident_str}) not within travel period',
                'severity': 'HIGH'
            })
    
    valid = len(errors) == 0
    return valid, errors, warnings


def _check_crop(fields_dict: Dict[str, Any]) -> Tuple[bool, List[Dict], List[Dict]]:
    """
    Crop insurance consistency checks.
    - damage_date must be after sowing_date
    """
    errors = []
    warnings = []
    
    sow_str = fields_dict.get('sowing_date')
    damage_str = fields_dict.get('damage_date')
    
    sow = parse_date(sow_str)
    damage = parse_date(damage_str)
    
    if sow and damage:
        if damage <= sow:
            errors.append({
                'rule': 'damage_after_sowing',
                'message': 'Damage date must be after sowing date',
                'severity': 'HIGH'
            })
    
    valid = len(errors) == 0
    return valid, errors, warnings


def validate_consistency(fields_dict: Dict[str, Any], insurance_type: str = None) -> Dict[str, Any]:
    """
    Main router function for consistency validation.
    Dispatches to type-specific checker based on insurance_type.
    
    Args:
        fields_dict: Dictionary of extracted form fields
        insurance_type: Insurance type code (health, vehicle, life, property, travel, crop)
    
    Returns:
        {
            'valid': bool,
            'errors': [
                {'rule': str, 'message': str, 'severity': 'HIGH'|'MEDIUM'|'LOW'},
                ...
            ],
            'warnings': [
                {'rule': str, 'message': str, 'severity': 'HIGH'|'MEDIUM'|'LOW'},
                ...
            ]
        }
    """
    if not fields_dict:
        fields_dict = {}
    
    errors = []
    warnings = []
    valid = True
    
    if insurance_type == 'health':
        valid, errors, warnings = _check_health(fields_dict)
    elif insurance_type == 'vehicle':
        valid, errors, warnings = _check_vehicle(fields_dict)
    elif insurance_type == 'life':
        valid, errors, warnings = _check_life(fields_dict)
    elif insurance_type == 'property':
        valid, errors, warnings = _check_property(fields_dict)
    elif insurance_type == 'travel':
        valid, errors, warnings = _check_travel(fields_dict)
    elif insurance_type == 'crop':
        valid, errors, warnings = _check_crop(fields_dict)
    else:
        # Unknown type: no specific consistency checks
        pass
    
    return {
        'valid': valid,
        'errors': errors,
        'warnings': warnings
    }
