from datetime import datetime
import json

# Import Phase 4 validators
try:
    from data_validator import validate_field
    from consistency_validator import validate_consistency
    from fraud_detector import detect_fraud
    VALIDATORS_AVAILABLE = True
except ImportError:
    VALIDATORS_AVAILABLE = False


def validate_claim(claim):
    # Import inside function to avoid circular import issues
    from app import db, Rule, Violation, InsuranceType, ClaimDocumentAnalysis

    violations = []
    field_errors = []
    consistency_issues = []
    fraud_detection = {'fraud_score': 0.0, 'risk_level': 'low', 'flags': []}

    # Get all rules for this insurance type
    all_rules        = Rule.query.filter_by(insurance_type_id=claim.insurance_type_id).all()
    doc_rules        = [r for r in all_rules if r.rule_type == 'document']
    field_rules      = [r for r in all_rules if r.rule_type == 'field']
    consistency_rules= [r for r in all_rules if r.rule_type == 'consistency']

    uploaded_docs = json.loads(claim.uploaded_docs) if claim.uploaded_docs else []
    form_data     = json.loads(claim.form_data)     if claim.form_data     else {}

    # ── DOCUMENT SCORE (40 pts) ──────────────────────────────────────────
    # Only required documents count toward score
    required_docs   = [r for r in doc_rules if r.is_required]
    max_doc_weight  = sum(r.weight for r in required_docs)
    earned_weight   = sum(r.weight for r in required_docs if r.name in uploaded_docs)

    document_score  = (earned_weight / max_doc_weight * 40) if max_doc_weight > 0 else 0

    # Violations for missing required docs
    for rule in required_docs:
        if rule.name not in uploaded_docs:
            violations.append({
                'rule_name': rule.name,
                'message':   f'Missing required document: {rule.label}',
                'suggestion': rule.suggestion,
                'severity':  rule.severity
            })

    # ── FIELD SCORE (35 pts) ─────────────────────────────────────────────
    required_fields = [r for r in field_rules if r.is_required]
    total_fields    = len(required_fields)
    filled_fields   = sum(1 for r in required_fields if form_data.get(r.name))

    field_score = (filled_fields / total_fields * 35) if total_fields > 0 else 0

    # Violations for missing fields
    for rule in required_fields:
        if not form_data.get(rule.name):
            violations.append({
                'rule_name': rule.name,
                'message':   f'Missing required field: {rule.label}',
                'suggestion': rule.suggestion,
                'severity':  rule.severity
            })

    # ── CONSISTENCY SCORE (25 pts) ───────────────────────────────────────
    consistency_score = 25
    ins_type = InsuranceType.query.get(claim.insurance_type_id)

    if ins_type:
        code = ins_type.code
        if code == 'health':
            consistency_score = _check_health(form_data, consistency_rules, violations, consistency_score)
        elif code == 'vehicle':
            consistency_score = _check_vehicle(form_data, consistency_rules, violations, consistency_score)
        elif code == 'life':
            consistency_score = _check_life(form_data, consistency_rules, violations, consistency_score)
        elif code == 'property':
            consistency_score = _check_property(form_data, consistency_rules, violations, consistency_score)
        elif code == 'travel':
            consistency_score = _check_travel(form_data, consistency_rules, violations, consistency_score)
        elif code == 'crop':
            consistency_score = _check_crop(form_data, consistency_rules, violations, consistency_score)

    consistency_score = max(0, consistency_score)

    # ── PHASE 4: DATA QUALITY & FRAUD DETECTION ──────────────────────────
    data_quality_adjustment = 0
    if VALIDATORS_AVAILABLE:
        # Validate individual fields
        for field_name, field_value in form_data.items():
            if field_value:
                field_result = validate_field(field_name, field_value)
                if not field_result['valid']:
                    for error in field_result['errors']:
                        field_errors.append(error)
                        # Penalize based on severity
                        if error['severity'] == 'HIGH':
                            data_quality_adjustment -= 10
                        elif error['severity'] == 'MEDIUM':
                            data_quality_adjustment -= 5
                        elif error['severity'] == 'LOW':
                            data_quality_adjustment -= 2
        
        # Validate cross-field consistency (Phase 4)
        insurance_code = ins_type.code if ins_type else None
        consistency_result = validate_consistency(form_data, insurance_code)
        if not consistency_result['valid']:
            for error in consistency_result['errors']:
                consistency_issues.append(error)
                if error['severity'] == 'HIGH':
                    data_quality_adjustment -= 10
                elif error['severity'] == 'MEDIUM':
                    data_quality_adjustment -= 5
        
        # Warnings don't block but reduce score
        for warning in consistency_result.get('warnings', []):
            consistency_issues.append(warning)
            if warning['severity'] == 'MEDIUM':
                data_quality_adjustment -= 2
            elif warning['severity'] == 'LOW':
                data_quality_adjustment -= 1
        
        # Detect fraud patterns
        ocr_confidence = 0.5  # default
        try:
            latest_analysis = ClaimDocumentAnalysis.query.filter_by(claim_id=claim.id).order_by(
                ClaimDocumentAnalysis.analysis_timestamp.desc()
            ).first()
            if latest_analysis and latest_analysis.ocr_confidence:
                ocr_confidence = latest_analysis.ocr_confidence
        except Exception:
            pass
        
        fraud_detection = detect_fraud(
            ocr_confidence=ocr_confidence,
            extracted_fields=form_data,
            document_types=uploaded_docs,
            insurance_type=insurance_code
        )

    # ── FINAL SCORE WITH DATA QUALITY ADJUSTMENT ──────────────────────────
    final_score = document_score + field_score + consistency_score + data_quality_adjustment
    final_score = round(max(0, min(100, final_score)))

    if final_score >= 80:
        readiness_label = 'Ready to Submit'
    elif final_score >= 50:
        readiness_label = 'Needs Attention'
    else:
        readiness_label = 'Incomplete'

    # ── SAVE TO DB ───────────────────────────────────────────────────────
    claim.readiness_score = final_score
    claim.score_breakdown = json.dumps({
        'document':    round(document_score, 1),
        'field':       round(field_score, 1),
        'consistency': round(consistency_score, 1),
        'data_quality_adjustment': data_quality_adjustment,
        'doc_earned':  earned_weight,
        'doc_max':     max_doc_weight,
        'doc_pct':     round(earned_weight / max_doc_weight * 100, 1) if max_doc_weight else 0,
        'field_filled': filled_fields,
        'field_total':  total_fields,
        'field_pct':    round(filled_fields / total_fields * 100, 1) if total_fields else 0,
    })
    claim.readiness_label = readiness_label

    # Clear old violations and save new ones
    Violation.query.filter_by(claim_id=claim.id).delete()
    for v in violations:
        db.session.add(Violation(
            claim_id   = claim.id,
            rule_name  = v['rule_name'],
            message    = v['message'],
            suggestion = v['suggestion'],
            severity   = v['severity']
        ))

    db.session.commit()

    return {
        'score':          final_score,
        'breakdown':      json.loads(claim.score_breakdown),
        'readiness_label': readiness_label,
        'violations':     violations,
        'field_errors':   field_errors,
        'consistency_issues': consistency_issues,
        'fraud_detection': fraud_detection
    }


# ── Consistency checkers ─────────────────────────────────────────────────────

def _add_violation(violations, rules, name, score, deduction):
    rule = next((r for r in rules if r.name == name), None)
    if rule:
        violations.append({
            'rule_name': rule.name,
            'message':   rule.label,
            'suggestion': rule.suggestion,
            'severity':  rule.severity
        })
    return score - deduction


def _check_health(form_data, rules, violations, score):
    adm = form_data.get('admission_date')
    dis = form_data.get('discharge_date')
    amt = form_data.get('claim_amount')
    cov = form_data.get('policy_coverage')

    if adm and dis:
        try:
            if datetime.strptime(dis, '%Y-%m-%d') <= datetime.strptime(adm, '%Y-%m-%d'):
                score = _add_violation(violations, rules, 'discharge_after_admission', score, 15)
        except: pass

    if amt and cov:
        try:
            if float(amt) > float(cov):
                score = _add_violation(violations, rules, 'claim_within_coverage', score, 10)
        except: pass

    return score


def _check_vehicle(form_data, rules, violations, score):
    amt = form_data.get('claim_amount')
    cov = form_data.get('policy_coverage')
    if amt and cov:
        try:
            if float(amt) > float(cov):
                score = _add_violation(violations, rules, 'claim_within_coverage', score, 10)
        except: pass
    return score


def _check_life(form_data, rules, violations, score):
    amt = form_data.get('claim_amount')
    sa  = form_data.get('sum_assured')
    if amt and sa:
        try:
            if abs(float(amt) - float(sa)) > 1000:
                score = _add_violation(violations, rules, 'claim_matches_sum_assured', score, 10)
        except: pass
    return score


def _check_property(form_data, rules, violations, score):
    amt = form_data.get('claim_amount')
    val = form_data.get('property_value')
    if amt and val:
        try:
            if float(amt) > float(val):
                score = _add_violation(violations, rules, 'claim_within_value', score, 10)
        except: pass
    return score


def _check_travel(form_data, rules, violations, score):
    start    = form_data.get('travel_start_date')
    end      = form_data.get('travel_end_date')
    incident = form_data.get('incident_date')

    if start and end:
        try:
            if datetime.strptime(end, '%Y-%m-%d') <= datetime.strptime(start, '%Y-%m-%d'):
                score = _add_violation(violations, rules, 'travel_end_after_start', score, 15)
        except: pass

    if start and end and incident:
        try:
            s = datetime.strptime(start, '%Y-%m-%d')
            e = datetime.strptime(end,   '%Y-%m-%d')
            i = datetime.strptime(incident, '%Y-%m-%d')
            if i < s or i > e:
                score = _add_violation(violations, rules, 'incident_during_travel', score, 15)
        except: pass

    return score


def _check_crop(form_data, rules, violations, score):
    sow    = form_data.get('sowing_date')
    damage = form_data.get('damage_date')
    if sow and damage:
        try:
            if datetime.strptime(damage, '%Y-%m-%d') <= datetime.strptime(sow, '%Y-%m-%d'):
                score = _add_violation(violations, rules, 'damage_after_sowing', score, 15)
        except: pass
    return score
