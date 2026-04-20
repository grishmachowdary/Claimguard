"""
Claim-Ready Package Generator
Generates a professional PDF report with:
- AI summary
- Validation score
- Document checklist
- Risk assessment
- All claim details
"""
import json
import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

# Colors
DARK_BG    = colors.HexColor('#0c1120')
BLUE       = colors.HexColor('#3b82f6')
GREEN      = colors.HexColor('#22c55e')
YELLOW     = colors.HexColor('#f59e0b')
RED        = colors.HexColor('#ef4444')
LIGHT_GRAY = colors.HexColor('#e2e8f0')
MUTED      = colors.HexColor('#475569')
WHITE      = colors.white
BLACK      = colors.black


def generate_claim_package(claim, rules, violations, ai_report, output_path):
    """Generate a complete claim-ready PDF package."""

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=0.75*inch,
        bottomMargin=0.75*inch
    )

    styles = getSampleStyleSheet()
    story  = []

    form_data     = json.loads(claim.form_data)     if claim.form_data     else {}
    uploaded_docs = json.loads(claim.uploaded_docs) if claim.uploaded_docs else []
    score         = claim.readiness_score or 0
    breakdown     = json.loads(claim.score_breakdown) if claim.score_breakdown else {}

    score_color = GREEN if score >= 80 else YELLOW if score >= 50 else RED

    # ── Custom styles ─────────────────────────────────────────────────────
    title_style = ParagraphStyle('Title', parent=styles['Title'],
        fontSize=22, textColor=BLUE, spaceAfter=4, alignment=TA_CENTER)
    subtitle_style = ParagraphStyle('Subtitle', parent=styles['Normal'],
        fontSize=11, textColor=MUTED, spaceAfter=20, alignment=TA_CENTER)
    h2_style = ParagraphStyle('H2', parent=styles['Heading2'],
        fontSize=14, textColor=BLACK, spaceBefore=16, spaceAfter=8)
    h3_style = ParagraphStyle('H3', parent=styles['Heading3'],
        fontSize=11, textColor=BLUE, spaceBefore=10, spaceAfter=6)
    body_style = ParagraphStyle('Body', parent=styles['Normal'],
        fontSize=10, textColor=BLACK, spaceAfter=6, leading=16)
    small_style = ParagraphStyle('Small', parent=styles['Normal'],
        fontSize=9, textColor=MUTED, spaceAfter=4)

    # ── Header ────────────────────────────────────────────────────────────
    story.append(Paragraph('ClaimGuard', title_style))
    story.append(Paragraph('Claim-Ready Validation Package', subtitle_style))
    story.append(HRFlowable(width='100%', thickness=2, color=BLUE))
    story.append(Spacer(1, 0.2*inch))

    # ── Claim info table ──────────────────────────────────────────────────
    from app import InsuranceType
    ins_type = InsuranceType.query.get(claim.insurance_type_id)

    info_data = [
        ['Claim ID', f'#{claim.id}', 'Insurance Type', ins_type.name if ins_type else 'N/A'],
        ['Generated', datetime.now().strftime('%d %b %Y %H:%M'), 'Status', claim.readiness_label or 'N/A'],
        ['Policy Number', form_data.get('policy_number', 'N/A'), 'Claim Amount', f"₹{form_data.get('claim_amount', 'N/A')}"],
    ]

    info_table = Table(info_data, colWidths=[1.2*inch, 2.3*inch, 1.2*inch, 2.3*inch])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8fafc')),
        ('TEXTCOLOR',  (0,0), (0,-1), MUTED),
        ('TEXTCOLOR',  (2,0), (2,-1), MUTED),
        ('FONTSIZE',   (0,0), (-1,-1), 9),
        ('FONTNAME',   (0,0), (0,-1), 'Helvetica-Bold'),
        ('FONTNAME',   (2,0), (2,-1), 'Helvetica-Bold'),
        ('GRID',       (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
        ('PADDING',    (0,0), (-1,-1), 6),
        ('ROWBACKGROUNDS', (0,0), (-1,-1), [colors.white, colors.HexColor('#f8fafc')]),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 0.2*inch))

    # ── Score section ─────────────────────────────────────────────────────
    story.append(Paragraph('Validation Score', h2_style))

    score_data = [
        ['Overall Score', f'{score}/100', 'Readiness', claim.readiness_label or 'N/A'],
        ['Documents', f"{breakdown.get('document', 0)}/40", 'Fields', f"{breakdown.get('field', 0)}/35"],
        ['Consistency', f"{breakdown.get('consistency', 0)}/25", 'Approval Probability',
         f"{ai_report.get('approval_percentage', 0)}%" if ai_report else 'N/A'],
    ]

    score_table = Table(score_data, colWidths=[1.5*inch, 2*inch, 1.5*inch, 2*inch])
    score_table.setStyle(TableStyle([
        ('BACKGROUND', (1,0), (1,0), score_color),
        ('TEXTCOLOR',  (1,0), (1,0), WHITE),
        ('FONTNAME',   (1,0), (1,0), 'Helvetica-Bold'),
        ('FONTSIZE',   (1,0), (1,0), 14),
        ('FONTNAME',   (0,0), (0,-1), 'Helvetica-Bold'),
        ('FONTNAME',   (2,0), (2,-1), 'Helvetica-Bold'),
        ('TEXTCOLOR',  (0,0), (0,-1), MUTED),
        ('TEXTCOLOR',  (2,0), (2,-1), MUTED),
        ('FONTSIZE',   (0,0), (-1,-1), 10),
        ('GRID',       (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
        ('PADDING',    (0,0), (-1,-1), 8),
        ('ALIGN',      (0,0), (-1,-1), 'CENTER'),
        ('ROWBACKGROUNDS', (0,0), (-1,-1), [colors.white, colors.HexColor('#f8fafc')]),
    ]))
    story.append(score_table)
    story.append(Spacer(1, 0.15*inch))

    # ── AI Summary ────────────────────────────────────────────────────────
    if ai_report:
        story.append(Paragraph('AI Analysis Summary', h2_style))
        story.append(Paragraph(ai_report.get('summary', ''), body_style))
        story.append(Spacer(1, 0.1*inch))

    # ── Document checklist ────────────────────────────────────────────────
    story.append(Paragraph('Document Checklist', h2_style))

    doc_rules = [r for r in rules if r.rule_type == 'document']
    doc_data  = [['Document', 'Required', 'Status', 'Weight']]

    for rule in doc_rules:
        status = '✓ Uploaded' if rule.name in uploaded_docs else '✗ Missing'
        doc_data.append([
            rule.label,
            'Yes' if rule.is_required else 'No',
            status,
            f'{rule.weight}pts'
        ])

    doc_table = Table(doc_data, colWidths=[3*inch, 0.8*inch, 1.2*inch, 0.8*inch])
    doc_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), BLUE),
        ('TEXTCOLOR',  (0,0), (-1,0), WHITE),
        ('FONTNAME',   (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE',   (0,0), (-1,-1), 9),
        ('GRID',       (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
        ('PADDING',    (0,0), (-1,-1), 6),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f8fafc')]),
    ]))

    # Color uploaded/missing rows
    for i, rule in enumerate(doc_rules, start=1):
        if rule.name in uploaded_docs:
            doc_table.setStyle(TableStyle([('TEXTCOLOR', (2,i), (2,i), GREEN)]))
        else:
            doc_table.setStyle(TableStyle([('TEXTCOLOR', (2,i), (2,i), RED)]))

    story.append(doc_table)
    story.append(Spacer(1, 0.15*inch))

    # ── Claim details ─────────────────────────────────────────────────────
    if form_data:
        story.append(Paragraph('Claim Details', h2_style))
        field_data = [['Field', 'Value']]
        for k, v in form_data.items():
            field_data.append([k.replace('_', ' ').title(), str(v)])

        field_table = Table(field_data, colWidths=[2.5*inch, 4.5*inch])
        field_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1e3a5f')),
            ('TEXTCOLOR',  (0,0), (-1,0), WHITE),
            ('FONTNAME',   (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTNAME',   (0,1), (0,-1), 'Helvetica-Bold'),
            ('TEXTCOLOR',  (0,1), (0,-1), MUTED),
            ('FONTSIZE',   (0,0), (-1,-1), 9),
            ('GRID',       (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
            ('PADDING',    (0,0), (-1,-1), 6),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f8fafc')]),
        ]))
        story.append(field_table)
        story.append(Spacer(1, 0.15*inch))

    # ── Violations ────────────────────────────────────────────────────────
    if violations:
        story.append(Paragraph(f'Issues Found ({len(violations)})', h2_style))
        for v in violations:
            sev_color = RED if v.severity == 'high' else YELLOW if v.severity == 'medium' else BLUE
            story.append(Paragraph(f'<font color="#{sev_color.hexval()[1:]}">■</font> {v.message}', body_style))
            story.append(Paragraph(f'  → {v.suggestion}', small_style))
        story.append(Spacer(1, 0.1*inch))

    # ── Suggestions ───────────────────────────────────────────────────────
    if ai_report and ai_report.get('suggestions'):
        story.append(Paragraph('Recommendations', h2_style))
        for s in ai_report['suggestions']:
            story.append(Paragraph(f'• {s["action"]}', body_style))
            if s.get('detail'):
                story.append(Paragraph(f'  {s["detail"]}', small_style))

    # ── Footer ────────────────────────────────────────────────────────────
    story.append(Spacer(1, 0.3*inch))
    story.append(HRFlowable(width='100%', thickness=1, color=MUTED))
    story.append(Spacer(1, 0.1*inch))
    story.append(Paragraph(
        f'Generated by ClaimGuard on {datetime.now().strftime("%d %B %Y at %H:%M")} | Claim ID: #{claim.id}',
        ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, textColor=MUTED, alignment=TA_CENTER)
    ))

    doc.build(story)
    return output_path
