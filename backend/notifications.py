"""
Email Notification System
Sends emails when claim status changes.
Uses Flask-Mail with Gmail SMTP (configurable).
"""
from flask_mail import Mail, Message
from flask import current_app

mail = Mail()

STATUS_SUBJECTS = {
    'draft':           '📋 ClaimGuard — Claim #{id} Created',
    'documents':       '📎 ClaimGuard — Documents Uploaded for Claim #{id}',
    'needs_attention': '🔔 ClaimGuard — Action Needed on Claim #{id}',
    'incomplete':      '⚠️ ClaimGuard — Claim #{id} Has Critical Issues',
    'ready':           '✅ ClaimGuard — Claim #{id} is Ready to Submit!',
    'submitted':       '🚀 ClaimGuard — Claim #{id} Submitted to Insurer',
    'under_review':    '🔍 ClaimGuard — Claim #{id} is Under Review',
    'approved':        '🎉 ClaimGuard — Claim #{id} APPROVED!',
    'rejected':        '❌ ClaimGuard — Claim #{id} Rejected',
}

STATUS_BODIES = {
    'draft': """
Hi {name},

Your insurance claim #{id} has been created on ClaimGuard.

Next Step: Upload all required documents to proceed.

View your claim: http://localhost:3000/report/{id}

— ClaimGuard Team
""",
    'needs_attention': """
Hi {name},

Your claim #{id} ({insurance_type}) needs attention.

Validation Score: {score}/100
Issues Found: {issues}

Please review and fix the issues to improve your approval chances.

View your claim: http://localhost:3000/report/{id}

— ClaimGuard Team
""",
    'ready': """
Hi {name},

Great news! Your claim #{id} ({insurance_type}) is ready to submit.

Validation Score: {score}/100 ✅
Approval Probability: {approval}%

You can now submit your claim directly to your insurance company.

Submit now: http://localhost:3000/report/{id}

— ClaimGuard Team
""",
    'submitted': """
Hi {name},

Your claim #{id} ({insurance_type}) has been submitted to {company}.

Reference Number: {reference}

What happens next:
- The insurer will review your documents within 3-5 business days
- You will receive updates as your claim progresses
- Keep your reference number safe

Track your claim: http://localhost:3000/report/{id}

— ClaimGuard Team
""",
    'approved': """
Hi {name},

🎉 Congratulations! Your claim #{id} ({insurance_type}) has been APPROVED!

Settlement will be processed to your registered bank account within 7 working days.

Track your claim: http://localhost:3000/report/{id}

— ClaimGuard Team
""",
    'rejected': """
Hi {name},

We're sorry to inform you that your claim #{id} ({insurance_type}) has been rejected.

You have the right to appeal this decision within 30 days.
Contact your insurer with your reference number for more details.

Track your claim: http://localhost:3000/report/{id}

— ClaimGuard Team
""",
}

def send_status_email(user_email, user_name, claim_id, status, extra={}):
    """Send status change email. Fails silently if mail not configured."""
    try:
        subject_template = STATUS_SUBJECTS.get(status, 'ClaimGuard — Claim #{id} Update')
        body_template    = STATUS_BODIES.get(status, 'Your claim #{id} status has been updated to: {status}')

        context = {
            'id':             claim_id,
            'name':           user_name,
            'status':         status,
            'insurance_type': extra.get('insurance_type', ''),
            'score':          extra.get('score', 0),
            'issues':         extra.get('issues', 0),
            'approval':       extra.get('approval', 0),
            'company':        extra.get('company', ''),
            'reference':      extra.get('reference', ''),
        }

        subject = subject_template.format(**context)
        body    = body_template.format(**context)

        msg = Message(
            subject=subject,
            recipients=[user_email],
            body=body,
            sender=current_app.config.get('MAIL_DEFAULT_SENDER', 'noreply@claimguard.in')
        )
        mail.send(msg)
        return True
    except Exception as e:
        # Log but don't crash — email is non-critical
        print(f'[Email] Failed to send: {e}')
        return False
