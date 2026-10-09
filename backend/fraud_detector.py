"""
Fraud Detector Module
Detects fraud risk patterns based on OCR confidence, claim size, document completeness,
and anomalies in extracted data.
Returns fraud_score (0-1.0) and list of flagged signals.
"""

import re
from datetime import datetime
from typing import Dict, List, Any, Optional


def detect_fraud(ocr_confidence: float, extracted_fields: Dict[str, Any], 
                document_types: List[str], insurance_type: str = None,
                historical_claims: List[Dict] = None) -> Dict[str, Any]:
    """
    Detect fraud risk patterns in a claim.
    
    Args:
        ocr_confidence: OCR confidence score (0.0-1.0), from document analysis
        extracted_fields: Dictionary of extracted form fields
        document_types: List of document types uploaded (e.g., ['insurance_policy', 'hospital_bill'])
        insurance_type: Insurance type code (health, vehicle, life, etc.)
        historical_claims: List of previous claims from this claimant
    
    Returns:
        {
            'fraud_score': float (0.0-1.0),
            'risk_level': 'low' | 'medium' | 'high',
            'flags': [
                {
                    'signal': str,
                    'message': str,
                    'severity': 'HIGH' | 'MEDIUM' | 'LOW',
                    'contribution': float (score points added)
                },
                ...
            ]
        }
    """
    if extracted_fields is None:
        extracted_fields = {}
    if document_types is None:
        document_types = []
    if historical_claims is None:
        historical_claims = []
    
    fraud_score = 0.0
    flags = []
    
    # Signal 1: Low OCR confidence with high claim amount
    claim_amount = extracted_fields.get('claim_amount')
    try:
        if isinstance(claim_amount, str):
            claim_amount = float(claim_amount)
    except (ValueError, TypeError):
        claim_amount = 0
    
    if ocr_confidence < 0.5 and claim_amount > 100000:
        contribution = 0.25
        fraud_score += contribution
        flags.append({
            'signal': 'low_ocr_high_claim',
            'message': f'Low OCR confidence ({ocr_confidence:.2f}) with high claim amount ({claim_amount})',
            'severity': 'HIGH',
            'contribution': contribution
        })
    
    # Signal 2: Missing key documents with high claim
    required_docs_health = {'discharge_summary', 'hospital_bill', 'prescription', 'invoice'}
    required_docs_vehicle = {'police_report', 'repair_estimate', 'insurance_policy'}
    required_docs_default = {'insurance_policy', 'claim_form'}
    
    required_docs = required_docs_default
    if insurance_type == 'health':
        required_docs = required_docs_health
    elif insurance_type == 'vehicle':
        required_docs = required_docs_vehicle
    
    doc_types_lower = [d.lower() for d in document_types]
    missing_key_docs = len([d for d in required_docs if d not in doc_types_lower]) > 0
    
    if missing_key_docs and claim_amount > 50000:
        contribution = 0.2
        fraud_score += contribution
        flags.append({
            'signal': 'missing_key_documents',
            'message': f'Missing key documents with high claim amount ({claim_amount})',
            'severity': 'HIGH',
            'contribution': contribution
        })
    
    # Signal 3: Pharmacy bill missing but medication keywords in diagnosis
    diagnosis = extracted_fields.get('diagnosis', '').lower()
    pharmacy_present = 'pharmacy_bill' in doc_types_lower or 'medicine_receipt' in doc_types_lower
    
    medication_keywords = ['medicine', 'drug', 'medication', 'tablet', 'injection', 'insulin', 
                          'antibiotics', 'prescription', 'dispenser', 'syrup']
    has_medication_keyword = any(kw in diagnosis for kw in medication_keywords)
    
    if not pharmacy_present and has_medication_keyword and claim_amount > 10000:
        contribution = 0.1
        fraud_score += contribution
        flags.append({
            'signal': 'medication_without_pharmacy_bill',
            'message': 'Diagnosis mentions medications but no pharmacy bill provided',
            'severity': 'MEDIUM',
            'contribution': contribution
        })
    
    # Signal 4: Discharge same day as admission
    admission_str = extracted_fields.get('admission_date')
    discharge_str = extracted_fields.get('discharge_date')
    
    if admission_str and discharge_str:
        try:
            admission_formats = ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%d-%m-%Y']
            admission_date = None
            discharge_date = None
            
            for fmt in admission_formats:
                try:
                    admission_date = datetime.strptime(admission_str, fmt)
                    break
                except ValueError:
                    continue
            
            for fmt in admission_formats:
                try:
                    discharge_date = datetime.strptime(discharge_str, fmt)
                    break
                except ValueError:
                    continue
            
            if admission_date and discharge_date:
                if admission_date.date() == discharge_date.date():
                    contribution = 0.15
                    fraud_score += contribution
                    flags.append({
                        'signal': 'same_day_discharge',
                        'message': 'Admission and discharge on same day - suspicious pattern',
                        'severity': 'HIGH',
                        'contribution': contribution
                    })
        except Exception:
            pass
    
    # Signal 5: Claim amount exactly equals policy coverage
    policy_coverage = extracted_fields.get('policy_coverage')
    try:
        if isinstance(policy_coverage, str):
            policy_coverage = float(policy_coverage)
    except (ValueError, TypeError):
        policy_coverage = None
    
    if claim_amount and policy_coverage:
        try:
            claim_float = float(claim_amount) if isinstance(claim_amount, str) else claim_amount
            coverage_float = float(policy_coverage) if isinstance(policy_coverage, str) else policy_coverage
            if abs(claim_float - coverage_float) < 0.01:  # exactly equal (within rounding)
                contribution = 0.2
                fraud_score += contribution
                flags.append({
                    'signal': 'claim_equals_coverage',
                    'message': f'Claim amount exactly matches policy coverage ({claim_float})',
                    'severity': 'HIGH',
                    'contribution': contribution
                })
        except (ValueError, TypeError):
            pass
    
    # Signal 6: Hospital name very short or generic
    hospital_name = extracted_fields.get('hospital_name', '').strip()
    
    if hospital_name:
        if len(hospital_name) < 4:
            contribution = 0.1
            fraud_score += contribution
            flags.append({
                'signal': 'short_hospital_name',
                'message': f'Hospital name suspiciously short: "{hospital_name}"',
                'severity': 'MEDIUM',
                'contribution': contribution
            })
        
        hospital_name_lower = hospital_name.lower()
        generic_names = ['hospital', 'clinic', 'health', 'care', 'medical', 'center']
        if hospital_name_lower in generic_names:
            contribution = 0.1
            fraud_score += contribution
            flags.append({
                'signal': 'generic_hospital_name',
                'message': f'Hospital name is generic: "{hospital_name}"',
                'severity': 'MEDIUM',
                'contribution': contribution
            })
    
    # Cap fraud_score at 1.0
    fraud_score = min(1.0, fraud_score)
    
    # Determine risk level
    if fraud_score >= 0.6:
        risk_level = 'high'
    elif fraud_score >= 0.3:
        risk_level = 'medium'
    else:
        risk_level = 'low'
    
    return {
        'fraud_score': fraud_score,
        'risk_level': risk_level,
        'flags': flags
    }
