"""
Claim History Comparison
Compares current claim with user's past claims.
Shows what improved, what got worse, and patterns.
"""
import json

def compare_claims(current_claim, past_claims, current_violations):
    """Compare current claim against past claims of same type."""
    if not past_claims:
        return None

    # Filter same insurance type
    same_type = [c for c in past_claims if c.insurance_type_id == current_claim.insurance_type_id
                 and c.id != current_claim.id and c.readiness_score is not None]

    if not same_type:
        return None

    # Sort by date, get most recent
    same_type.sort(key=lambda x: x.created_at, reverse=True)
    last_claim = same_type[0]

    current_score  = current_claim.readiness_score or 0
    previous_score = last_claim.readiness_score or 0
    score_diff     = current_score - previous_score

    current_bd  = json.loads(current_claim.score_breakdown) if current_claim.score_breakdown else {}
    previous_bd = json.loads(last_claim.score_breakdown)    if last_claim.score_breakdown    else {}

    improvements = []
    regressions  = []

    # Compare breakdown
    for key, label in [('document', 'Documents'), ('field', 'Fields'), ('consistency', 'Consistency')]:
        curr_val = current_bd.get(key, 0)
        prev_val = previous_bd.get(key, 0)
        diff = curr_val - prev_val
        if diff > 2:
            improvements.append(f'{label} score improved by {diff:.1f} points')
        elif diff < -2:
            regressions.append(f'{label} score dropped by {abs(diff):.1f} points')

    # Compare uploaded docs
    curr_docs = json.loads(current_claim.uploaded_docs) if current_claim.uploaded_docs else []
    prev_docs = json.loads(last_claim.uploaded_docs)    if last_claim.uploaded_docs    else []
    new_docs  = [d for d in curr_docs if d not in prev_docs]
    if new_docs:
        improvements.append(f'{len(new_docs)} more document(s) uploaded this time')

    # Overall message
    if score_diff >= 20:
        summary = f'Excellent improvement! Your score jumped {score_diff} points from your last claim.'
    elif score_diff >= 5:
        summary = f'Good progress! Score improved by {score_diff} points compared to last time.'
    elif score_diff >= -5:
        summary = 'Similar to your last claim. Review the suggestions to improve further.'
    else:
        summary = f'Score dropped by {abs(score_diff)} points. Check what changed from last time.'

    return {
        'previous_score':  previous_score,
        'current_score':   current_score,
        'score_diff':      score_diff,
        'improved':        score_diff > 0,
        'summary':         summary,
        'improvements':    improvements,
        'regressions':     regressions,
        'previous_claim_id': last_claim.id,
        'total_past_claims': len(same_type),
        'avg_past_score':  round(sum(c.readiness_score for c in same_type) / len(same_type), 1),
    }


def get_rejection_predictor(insurance_type_code, form_data, violations):
    """
    Predict rejection risk based on common patterns.
    Returns risk factors and probability.
    """
    risk_factors = []
    risk_score   = 0

    # Common rejection patterns per insurance type
    if insurance_type_code == 'health':
        diagnosis = form_data.get('diagnosis', '').lower()

        # Pre-existing condition keywords
        pre_existing = ['diabetes', 'hypertension', 'bp', 'thyroid', 'asthma', 'heart', 'cancer', 'kidney']
        for condition in pre_existing:
            if condition in diagnosis:
                risk_factors.append({
                    'factor': f'Pre-existing condition detected: {condition}',
                    'impact': 'high',
                    'note': 'Claims with pre-existing conditions are rejected 35% more often. Ensure your policy covers this condition.',
                    'deduction': 25
                })
                risk_score += 25
                break

        # Claim amount vs coverage
        claim_amt = float(form_data.get('claim_amount', 0) or 0)
        coverage  = float(form_data.get('policy_coverage', 0) or 0)
        if coverage > 0 and claim_amt > coverage * 0.9:
            risk_factors.append({
                'factor': 'Claim amount is close to or exceeds policy coverage',
                'impact': 'medium',
                'note': 'Claims near the coverage limit face 20% higher scrutiny.',
                'deduction': 15
            })
            risk_score += 15

    elif insurance_type_code == 'vehicle':
        # Check if FIR filed (required for theft/major accidents)
        incident_desc = form_data.get('incident_description', '').lower()
        if any(w in incident_desc for w in ['theft', 'stolen', 'accident', 'collision']):
            risk_factors.append({
                'factor': 'Incident type requires FIR — ensure police report is uploaded',
                'impact': 'high',
                'note': 'Missing FIR for theft/accident claims leads to 60% rejection rate.',
                'deduction': 30
            })
            risk_score += 30

    elif insurance_type_code == 'life':
        risk_factors.append({
            'factor': 'Life claims require strict document verification',
            'impact': 'medium',
            'note': 'Ensure all nominee documents are original and notarized.',
            'deduction': 10
        })
        risk_score += 10

    # High severity violations increase rejection risk
    high_violations = [v for v in violations if v.get('severity') == 'high']
    if len(high_violations) >= 3:
        risk_factors.append({
            'factor': f'{len(high_violations)} critical issues found in validation',
            'impact': 'high',
            'note': 'Claims with 3+ critical issues are rejected 70% of the time.',
            'deduction': 20
        })
        risk_score += 20

    # Calculate rejection probability
    rejection_prob = min(95, risk_score)
    approval_prob  = 100 - rejection_prob

    if rejection_prob >= 60:
        risk_level = 'High Risk'
        risk_color = '#ef4444'
    elif rejection_prob >= 30:
        risk_level = 'Moderate Risk'
        risk_color = '#f59e0b'
    else:
        risk_level = 'Low Risk'
        risk_color = '#22c55e'

    return {
        'rejection_probability': rejection_prob,
        'approval_probability':  approval_prob,
        'risk_level':            risk_level,
        'risk_color':            risk_color,
        'risk_factors':          risk_factors,
        'recommendation':        _get_recommendation(rejection_prob, risk_factors),
    }


def _get_recommendation(prob, factors):
    if prob >= 60:
        return 'Your claim has a high rejection risk. Address all critical issues before submitting.'
    elif prob >= 30:
        return 'Moderate rejection risk. Review the risk factors and resolve them to improve chances.'
    else:
        return 'Low rejection risk. Your claim looks well-prepared.'
