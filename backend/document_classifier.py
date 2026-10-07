"""
Document Classifier - Classify document type based on keyword analysis.

Pure keyword-based classification (no ML model required).
Fast, transparent, and efficient for common document types.
"""

import re
import logging
from typing import Dict, List

logger = logging.getLogger(__name__)

# Document type keyword definitions
DOCUMENT_KEYWORDS = {
    'claim_form': [
        'claim', 'application', 'form', 'claimant', 'policy number',
        'declaration', 'submit', 'insurance', 'coverage', 'policy holder'
    ],
    'police_report': [
        'police', 'fir', 'first information report', 'complaint',
        'officer', 'station', 'report', 'incident', 'crime', 'case'
    ],
    'medical_report': [
        'medical', 'report', 'diagnosis', 'patient', 'doctor',
        'hospital', 'treatment', 'clinical', 'examination', 'findings',
        'prescription', 'discharge'
    ],
    'receipt': [
        'receipt', 'payment', 'received', 'amount paid', 'invoice number',
        'total', 'paid', 'transaction', 'reference', 'bill amount'
    ],
    'invoice': [
        'invoice', 'bill', 'amount due', 'payable', 'total amount',
        'tax', 'gst', 'vat', 'itemized', 'charges', 'services rendered'
    ],
    'identity_document': [
        'aadhaar', 'passport', 'license', 'driving license', 'pan',
        'voter', 'id card', 'identity', 'identification', 'nid'
    ],
    'policy_document': [
        'policy', 'coverage', 'premium', 'terms', 'conditions',
        'schedule', 'insured', 'sum assured', 'deductible', 'exclusion'
    ],
    'medical_bill': [
        'medical bill', 'hospital bill', 'bill', 'invoice', 'charges',
        'amount', 'hospital', 'medical', 'treatment cost', 'medical charges'
    ],
}


def classify_document(text: str) -> Dict:
    """
    Classify document type based on keyword matching.
    
    Returns:
        {
            'type': str,              # Document type or 'unknown'
            'confidence': float,      # 0.0 to 1.0
            'scores': dict,           # {type: score, ...} for all types
            'keywords_matched': list, # Matched keywords
            'method': str            # 'keyword' or 'unknown'
        }
    
    Args:
        text: Document text to classify
        
    Returns:
        Classification result dict
    """
    
    if not text or not isinstance(text, str):
        return {
            'type': 'unknown',
            'confidence': 0.0,
            'scores': {},
            'keywords_matched': [],
            'method': 'unknown'
        }
    
    # Normalize text
    text_lower = text.lower()
    
    # Score each document type
    scores = {}
    matched_keywords = {}
    
    for doc_type, keywords in DOCUMENT_KEYWORDS.items():
        matched = []
        for keyword in keywords:
            # Case-insensitive keyword match (whole word or phrase)
            if re.search(r'\b' + re.escape(keyword) + r'\b', text_lower):
                matched.append(keyword)
        
        # Calculate score: ratio of matched keywords
        hit_ratio = len(matched) / len(keywords) if keywords else 0
        scores[doc_type] = hit_ratio
        matched_keywords[doc_type] = matched
    
    # Find top match
    top_type = max(scores, key=scores.get) if scores else 'unknown'
    top_score = scores.get(top_type, 0)
    
    # Confidence calculation
    if top_score == 0:
        # No keywords matched
        confidence = 0.0
        result_type = 'unknown'
        matched = []
    elif len(scores) > 1:
        # Check for tie (multiple types with similar scores)
        sorted_scores = sorted(scores.values(), reverse=True)
        gap = sorted_scores[0] - sorted_scores[1] if len(sorted_scores) > 1 else sorted_scores[0]
        
        if gap < 0.1 and sorted_scores[0] < 0.5:
            # Too close, low confidence
            confidence = top_score
            result_type = 'unknown'
            matched = []
        else:
            # Clear winner
            confidence = min(top_score, 1.0)  # Cap at 1.0
            result_type = top_type
            matched = matched_keywords.get(top_type, [])
    else:
        confidence = min(top_score, 1.0)
        result_type = top_type
        matched = matched_keywords.get(top_type, [])
    
    logger.info(f"Classified document as '{result_type}' (confidence: {confidence:.2f})")
    
    return {
        'type': result_type,
        'confidence': confidence,
        'scores': scores,
        'keywords_matched': list(set(matched)),  # Remove duplicates
        'method': 'keyword' if result_type != 'unknown' else 'unknown'
    }
