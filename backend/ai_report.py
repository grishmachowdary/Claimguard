"""
AI Claim Report Generator
Calculates approval probability and generates structured report
based on document validation results and violations.
"""
import json

def generate_ai_report(claim, violations, rules, uploaded_docs):
    """
    Generate AI-based claim report with approval probability.
    
    Logic:
    - Start at 100%
    - Missing required document:  -20% each
    - Missing required field:     -10% each
    - Invalid/consistency issue:  -30% each (high severity)
    - Medium severity violation:  -15% each
    - Low severity violation:     -5% each
    """

    # Get all document rules
    doc_rules   = [r for r in rules if r.rule_type == 'document' and r.is_required]
    field_rules = [r for r in rules if r.rule_type == 'field'    and r.is_required]

    approval_pct = 100
    issues       = []
    suggestions  = []
    deductions   = []

    # ── Check missing required documents ──────────────────────────────────
    for rule in doc_rules:
        if rule.name not in uploaded_docs:
            approval_pct -= 20
            issues.append({
                'type': 'missing_document',
                'label': f'Missing document: {rule.label}',
                'severity': rule.severity
            })
            suggestions.append({
                'action': f'Upload {rule.label}',
                'detail': rule.suggestion
            })
            deductions.append({
                'reason': f'Missing required document — {rule.label}',
                'deduction': -20
            })

    # ── Check violations ───────────────────────────────────────────────────
    for v in violations:
        if v['severity'] == 'high':
            # Consistency / invalid issues
            if 'Missing required field' in v['message']:
                approval_pct -= 10
                deductions.append({'reason': v['message'], 'deduction': -10})
            else:
                approval_pct -= 30
                deductions.append({'reason': v['message'], 'deduction': -30})
            issues.append({
                'type': 'invalid' if 'Missing required field' not in v['message'] else 'missing_info',
                'label': v['message'],
                'severity': 'high'
            })
            suggestions.append({
                'action': v['suggestion'],
                'detail': ''
            })
        elif v['severity'] == 'medium':
            approval_pct -= 15
            deductions.append({'reason': v['message'], 'deduction': -15})
            issues.append({
                'type': 'missing_info',
                'label': v['message'],
                'severity': 'medium'
            })
            suggestions.append({
                'action': v['suggestion'],
                'detail': ''
            })
        elif v['severity'] == 'low':
            approval_pct -= 5
            deductions.append({'reason': v['message'], 'deduction': -5})
            issues.append({
                'type': 'low_risk',
                'label': v['message'],
                'severity': 'low'
            })
            suggestions.append({
                'action': v['suggestion'],
                'detail': ''
            })

    # Clamp between 0 and 100
    approval_pct = max(0, min(100, approval_pct))

    # ── Generate summary text ──────────────────────────────────────────────
    summary = _generate_summary(approval_pct, issues, claim)

    # ── Determine approval status ──────────────────────────────────────────
    if approval_pct >= 80:
        status       = 'High'
        status_color = 'green'
        status_msg   = 'Your claim has a high probability of approval. All major requirements are met.'
    elif approval_pct >= 50:
        status       = 'Moderate'
        status_color = 'yellow'
        status_msg   = 'Your claim has moderate chances of approval. Address the issues below to improve.'
    else:
        status       = 'Low'
        status_color = 'red'
        status_msg   = 'Your claim has a low probability of approval. Several critical issues need to be resolved.'

    return {
        'approval_percentage': approval_pct,
        'approval_status':     status,
        'approval_color':      status_color,
        'approval_status_msg': status_msg,
        'summary':             summary,
        'issues':              issues,
        'suggestions':         suggestions,
        'deductions':          deductions,
        'total_issues':        len(issues),
        'critical_issues':     len([i for i in issues if i['severity'] == 'high']),
    }


def _generate_summary(pct, issues, claim):
    """Generate a human-readable summary paragraph."""
    form_data = json.loads(claim.form_data) if claim.form_data else {}

    missing_docs  = [i for i in issues if i['type'] == 'missing_document']
    invalid_docs  = [i for i in issues if i['type'] == 'invalid']
    missing_info  = [i for i in issues if i['type'] == 'missing_info']

    if pct >= 90:
        return (
            "Your claim is well-prepared and has an excellent chance of approval. "
            "All required documents appear to be in order and the claim details are complete. "
            "You may proceed with submission."
        )
    elif pct >= 75:
        parts = []
        if missing_docs:
            parts.append(f"{len(missing_docs)} required document(s) still need to be uploaded")
        if missing_info:
            parts.append(f"{len(missing_info)} field(s) have incomplete or inconsistent information")
        detail = " and ".join(parts) if parts else "minor issues were found"
        return (
            f"Your claim has a good chance of approval. However, {detail}. "
            "Resolving these will significantly improve your approval probability."
        )
    elif pct >= 50:
        parts = []
        if missing_docs:
            parts.append(f"{len(missing_docs)} required document(s) are missing")
        if invalid_docs:
            parts.append(f"{len(invalid_docs)} consistency issue(s) were detected")
        if missing_info:
            parts.append(f"{len(missing_info)} field(s) have incomplete information")
        detail = ", ".join(parts) if parts else "several issues were found"
        return (
            f"Your claim has moderate chances of approval. {detail.capitalize()}. "
            "Please review the issues listed below and make corrections before submitting."
        )
    else:
        critical = len([i for i in issues if i['severity'] == 'high'])
        return (
            f"Your claim currently has a low probability of approval. "
            f"{critical} critical issue(s) were found that must be resolved. "
            "Missing documents and invalid information are the primary concerns. "
            "Please address all issues listed below before submitting your claim."
        )
