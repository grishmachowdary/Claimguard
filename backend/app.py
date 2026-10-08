from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
import bcrypt
import json
import os
import logging
import time
from config import get_config

# Document intelligence modules (lazy-loaded with error handling)
try:
    from ocr_engine import extract_text, extract_text_with_boxes
    from field_extractor import extract_fields
    from document_classifier import classify_document
    OCR_AVAILABLE = True
except ImportError as e:
    OCR_AVAILABLE = False
    logging.warning(f'Document intelligence modules not available: {e}')

app = Flask(__name__)
CORS(app)

# Load configuration based on environment
config = get_config()
app.config.from_object(config)

# Ensure essential config keys exist
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=7)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)
jwt = JWTManager(app)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def log_status(claim_id, status, note=''):
    """Log a status change to claim history."""
    entry = ClaimStatusHistory(claim_id=claim_id, status=status, note=note)
    db.session.add(entry)
    db.session.commit()

# ── Models ──────────────────────────────────────────────────────────────────

class User(db.Model):
    __tablename__ = 'users'
    id         = db.Column(db.Integer, primary_key=True)
    full_name  = db.Column(db.String(200), nullable=False)
    email      = db.Column(db.String(200), unique=True, nullable=False)
    password   = db.Column(db.String(255), nullable=False)
    role       = db.Column(db.String(20), default='customer')  # customer | agent | insurer
    company    = db.Column(db.String(200))  # for insurer role
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class AgentClient(db.Model):
    """Links agents to their clients."""
    __tablename__ = 'agent_clients'
    id         = db.Column(db.Integer, primary_key=True)
    agent_id   = db.Column(db.Integer, db.ForeignKey('users.id'))
    client_id  = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class InsuranceType(db.Model):
    __tablename__ = 'insurance_types'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(50), unique=True, nullable=False)
    icon = db.Column(db.String(50))
    is_active = db.Column(db.Boolean, default=True)

class Rule(db.Model):
    __tablename__ = 'rules'
    id = db.Column(db.Integer, primary_key=True)
    insurance_type_id = db.Column(db.Integer, db.ForeignKey('insurance_types.id'))
    rule_type = db.Column(db.String(50), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    label = db.Column(db.String(200))
    is_required = db.Column(db.Boolean, default=False)
    weight = db.Column(db.Integer, default=0)
    severity = db.Column(db.String(20))
    suggestion = db.Column(db.Text)

class Claim(db.Model):
    __tablename__ = 'claims'
    id                = db.Column(db.Integer, primary_key=True)
    user_id           = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    insurance_type_id = db.Column(db.Integer, db.ForeignKey('insurance_types.id'))
    form_data         = db.Column(db.Text)
    uploaded_docs     = db.Column(db.Text)
    readiness_score   = db.Column(db.Integer)
    score_breakdown   = db.Column(db.Text)
    readiness_label   = db.Column(db.String(50))
    ai_report         = db.Column(db.Text)
    status            = db.Column(db.String(50), default='draft')
    insurer_notes     = db.Column(db.Text)   # notes from insurer
    assigned_insurer  = db.Column(db.String(100))  # which insurer it was submitted to
    created_at        = db.Column(db.DateTime, default=datetime.utcnow)

class ClaimStatusHistory(db.Model):
    __tablename__ = 'claim_status_history'
    id         = db.Column(db.Integer, primary_key=True)
    claim_id   = db.Column(db.Integer, db.ForeignKey('claims.id'))
    status     = db.Column(db.String(50), nullable=False)
    note       = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Violation(db.Model):
    __tablename__ = 'violations'
    id = db.Column(db.Integer, primary_key=True)
    claim_id = db.Column(db.Integer, db.ForeignKey('claims.id'))
    rule_name = db.Column(db.String(100))
    message = db.Column(db.Text)
    suggestion = db.Column(db.Text)
    severity = db.Column(db.String(20))

class ClaimDocument(db.Model):
    __tablename__ = 'claim_documents'
    id = db.Column(db.Integer, primary_key=True)
    claim_id = db.Column(db.Integer, db.ForeignKey('claims.id'))
    document_type = db.Column(db.String(100))
    file_name = db.Column(db.String(255))
    file_path = db.Column(db.String(500))
    file_size = db.Column(db.Integer)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

class ClaimDocumentAnalysis(db.Model):
    __tablename__ = 'claim_document_analyses'
    id = db.Column(db.Integer, primary_key=True)
    claim_id = db.Column(db.Integer, db.ForeignKey('claims.id'))
    document_id = db.Column(db.Integer, db.ForeignKey('claim_documents.id'))
    ocr_text = db.Column(db.Text)
    ocr_confidence = db.Column(db.Float)
    document_type = db.Column(db.String(100))
    classification_confidence = db.Column(db.Float)
    extracted_fields = db.Column(db.Text)
    confidence_score = db.Column(db.Float)
    analysis_timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# ── Auth Routes ──────────────────────────────────────────────────────────────

@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.json
    full_name = data.get('full_name', '').strip()
    email     = data.get('email', '').strip().lower()
    password  = data.get('password', '')
    role      = data.get('role', 'customer')  # customer | agent | insurer
    company   = data.get('company', '')

    if not full_name or not email or not password:
        return jsonify({'error': 'All fields are required'}), 400
    if len(password) < 6:
        return jsonify({'error': 'Password must be at least 6 characters'}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Email already registered'}), 409
    if role not in ['customer', 'agent', 'insurer']:
        role = 'customer'

    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    user = User(full_name=full_name, email=email, password=hashed, role=role, company=company)
    db.session.add(user)
    db.session.commit()

    token = create_access_token(identity=str(user.id))
    return jsonify({
        'token': token,
        'user': {'id': user.id, 'full_name': user.full_name, 'email': user.email, 'role': user.role}
    }), 201

@app.route('/api/auth/login', methods=['POST'])
def login():
    data     = request.json
    email    = data.get('email', '').strip().lower()
    password = data.get('password', '')

    user = User.query.filter_by(email=email).first()
    if not user or not bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
        return jsonify({'error': 'Invalid email or password'}), 401

    token = create_access_token(identity=str(user.id))
    return jsonify({
        'token': token,
        'user': {'id': user.id, 'full_name': user.full_name, 'email': user.email}
    })

@app.route('/api/auth/me', methods=['GET'])
@jwt_required()
def get_me():
    user_id = get_jwt_identity()
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    return jsonify({'id': user.id, 'full_name': user.full_name, 'email': user.email, 'role': user.role, 'company': user.company})

# ── Routes ───────────────────────────────────────────────────────────────────

@app.route('/api/insurance-types', methods=['GET'])
def get_insurance_types():
    types = InsuranceType.query.filter_by(is_active=True).all()
    return jsonify([{'id': t.id, 'name': t.name, 'code': t.code, 'icon': t.icon} for t in types])

@app.route('/api/rules/<insurance_type>', methods=['GET'])
def get_rules(insurance_type):
    ins_type = InsuranceType.query.filter_by(code=insurance_type).first()
    if not ins_type:
        return jsonify({'error': 'Insurance type not found'}), 404

    rules = Rule.query.filter_by(insurance_type_id=ins_type.id).all()
    result = {'insurance_type_id': ins_type.id, 'documents': [], 'fields': [], 'consistency': []}

    for rule in rules:
        rule_data = {
            'id': rule.id, 'name': rule.name, 'label': rule.label,
            'is_required': rule.is_required, 'weight': rule.weight,
            'severity': rule.severity, 'suggestion': rule.suggestion
        }
        if rule.rule_type == 'document':
            result['documents'].append(rule_data)
        elif rule.rule_type == 'field':
            result['fields'].append(rule_data)
        elif rule.rule_type == 'consistency':
            result['consistency'].append(rule_data)

    return jsonify(result)

@app.route('/api/claims', methods=['GET'])
def get_claims():
    page     = request.args.get('page', 1, type=int)
    per_page = 10
    query    = Claim.query.order_by(Claim.created_at.desc())
    total    = query.count()
    all_claims = query.offset((page - 1) * per_page).limit(per_page).all()
    result = []
    for c in all_claims:
        form_data = json.loads(c.form_data) if c.form_data else {}
        ins_type = db.session.get(InsuranceType, c.insurance_type_id)
        result.append({
            'id': c.id,
            'insurance_type_id': c.insurance_type_id,
            'insurance_type_name': ins_type.name if ins_type else None,
            'primary_field': form_data.get('policy_number') or form_data.get('vehicle_number') or 'Draft',
            'readiness_score': c.readiness_score,
            'readiness_label': c.readiness_label,
            'status': c.status,
            'created_at': c.created_at.isoformat() if c.created_at else None
        })
    return jsonify({
        'claims': result,
        'total': total,
        'page': page,
        'pages': (total + per_page - 1) // per_page
    })

@app.route('/api/claims', methods=['POST'])
def create_claim():
    data = request.json
    claim = Claim(
        insurance_type_id=data.get('insurance_type_id'),
        uploaded_docs=json.dumps(data.get('uploaded_docs', [])),
        status='draft'
    )
    db.session.add(claim)
    db.session.commit()
    log_status(claim.id, 'draft', 'Claim created. Documents checklist started.')
    return jsonify({'id': claim.id, 'message': 'Claim created successfully'}), 201

@app.route('/api/claims/<int:claim_id>', methods=['PUT'])
def update_claim(claim_id):
    claim = Claim.query.get_or_404(claim_id)
    data = request.json
    if 'form_data' in data:
        claim.form_data = json.dumps(data['form_data'])
    if 'uploaded_docs' in data:
        claim.uploaded_docs = json.dumps(data['uploaded_docs'])
    db.session.commit()
    return jsonify({'message': 'Claim updated successfully'})

@app.route('/api/claims/<int:claim_id>/validate', methods=['POST'])
def validate_claim_endpoint(claim_id):
    claim = Claim.query.get_or_404(claim_id)

    # Import Phase 4 validators
    try:
        from data_validator import validate_field
        from consistency_validator import validate_consistency
        from fraud_detector import detect_fraud
        VALIDATORS_AVAILABLE = True
    except ImportError:
        VALIDATORS_AVAILABLE = False

    # ── Run rule engine inline ────────────────────────────────────────────
    import json as _json
    from datetime import datetime as _dt

    all_rules         = Rule.query.filter_by(insurance_type_id=claim.insurance_type_id).all()
    doc_rules         = [r for r in all_rules if r.rule_type == 'document']
    field_rules       = [r for r in all_rules if r.rule_type == 'field']
    consistency_rules = [r for r in all_rules if r.rule_type == 'consistency']

    uploaded_docs = json.loads(claim.uploaded_docs) if claim.uploaded_docs else []
    form_data     = json.loads(claim.form_data)     if claim.form_data     else {}

    violations = []
    field_errors = []
    consistency_issues = []
    fraud_detection = {'fraud_score': 0.0, 'risk_level': 'low', 'flags': []}

    # Document score (40 pts)
    required_docs  = [r for r in doc_rules if r.is_required]
    max_doc_weight = sum(r.weight for r in required_docs)
    earned_weight  = sum(r.weight for r in required_docs if r.name in uploaded_docs)
    document_score = (earned_weight / max_doc_weight * 40) if max_doc_weight > 0 else 0

    for rule in required_docs:
        if rule.name not in uploaded_docs:
            violations.append({'rule_name': rule.name, 'message': f'Missing required document: {rule.label}',
                                'suggestion': rule.suggestion, 'severity': rule.severity})

    # Field score (35 pts)
    required_fields = [r for r in field_rules if r.is_required]
    total_fields    = len(required_fields)
    filled_fields   = sum(1 for r in required_fields if form_data.get(r.name))
    field_score     = (filled_fields / total_fields * 35) if total_fields > 0 else 0

    for rule in required_fields:
        if not form_data.get(rule.name):
            violations.append({'rule_name': rule.name, 'message': f'Missing required field: {rule.label}',
                                'suggestion': rule.suggestion, 'severity': rule.severity})

    # Consistency score (25 pts)
    consistency_score = 25
    ins_type = db.session.get(InsuranceType, claim.insurance_type_id)

    def add_v(name, deduction):
        rule = next((r for r in consistency_rules if r.name == name), None)
        if rule:
            violations.append({'rule_name': rule.name, 'message': rule.label,
                                'suggestion': rule.suggestion, 'severity': rule.severity})
        return deduction

    def parse_date(s):
        try: return _dt.strptime(s, '%Y-%m-%d')
        except: return None

    if ins_type:
        code = ins_type.code
        if code == 'health':
            adm = parse_date(form_data.get('admission_date',''))
            dis = parse_date(form_data.get('discharge_date',''))
            if adm and dis and dis <= adm:
                consistency_score -= add_v('discharge_after_admission', 15)
            amt = form_data.get('claim_amount'); cov = form_data.get('policy_coverage')
            if amt and cov and float(amt) > float(cov):
                consistency_score -= add_v('claim_within_coverage', 10)

        elif code == 'vehicle':
            amt = form_data.get('claim_amount'); cov = form_data.get('policy_coverage')
            if amt and cov and float(amt) > float(cov):
                consistency_score -= add_v('claim_within_coverage', 10)

        elif code == 'life':
            amt = form_data.get('claim_amount'); sa = form_data.get('sum_assured')
            if amt and sa and abs(float(amt) - float(sa)) > 1000:
                consistency_score -= add_v('claim_matches_sum_assured', 10)

        elif code == 'property':
            amt = form_data.get('claim_amount'); val = form_data.get('property_value')
            if amt and val and float(amt) > float(val):
                consistency_score -= add_v('claim_within_value', 10)

        elif code == 'travel':
            s = parse_date(form_data.get('travel_start_date',''))
            e = parse_date(form_data.get('travel_end_date',''))
            i = parse_date(form_data.get('incident_date',''))
            if s and e and e <= s:
                consistency_score -= add_v('travel_end_after_start', 15)
            if s and e and i and (i < s or i > e):
                consistency_score -= add_v('incident_during_travel', 15)

        elif code == 'crop':
            sow = parse_date(form_data.get('sowing_date',''))
            dmg = parse_date(form_data.get('damage_date',''))
            if sow and dmg and dmg <= sow:
                consistency_score -= add_v('damage_after_sowing', 15)

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
            latest_analysis = ClaimDocumentAnalysis.query.filter_by(claim_id=claim_id).order_by(
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
    final_score = max(0, min(100, round(final_score)))

    if final_score >= 80:   readiness_label = 'Ready to Submit';   new_status = 'ready'
    elif final_score >= 50: readiness_label = 'Needs Attention';   new_status = 'needs_attention'
    else:                   readiness_label = 'Incomplete';         new_status = 'incomplete'

    # Compute overall risk based on readiness_score and fraud_score
    if final_score < 50 or fraud_detection['fraud_score'] > 0.6:
        overall_risk = 'HIGH'
    elif final_score < 70 or fraud_detection['fraud_score'] > 0.3:
        overall_risk = 'MEDIUM'
    else:
        overall_risk = 'LOW'

    claim.readiness_score = final_score
    claim.score_breakdown = json.dumps({
        'document': round(document_score, 1), 'field': round(field_score, 1),
        'consistency': round(consistency_score, 1), 'data_quality_adjustment': data_quality_adjustment,
        'doc_earned': earned_weight, 'doc_max': max_doc_weight,
        'doc_pct': round(earned_weight / max_doc_weight * 100, 1) if max_doc_weight else 0,
        'field_filled': filled_fields, 'field_total': total_fields,
        'field_pct': round(filled_fields / total_fields * 100, 1) if total_fields else 0,
    })
    claim.readiness_label = readiness_label
    claim.status = new_status

    Violation.query.filter_by(claim_id=claim_id).delete()
    for v in violations:
        db.session.add(Violation(claim_id=claim_id, rule_name=v['rule_name'],
                                  message=v['message'], suggestion=v['suggestion'], severity=v['severity']))
    db.session.commit()
    log_status(claim_id, new_status, f'Validation complete. Score: {final_score}/100.')

    # Generate AI report
    from ai_report import generate_ai_report
    rules_list   = Rule.query.filter_by(insurance_type_id=claim.insurance_type_id).all()
    ai_report    = generate_ai_report(claim, violations, rules_list, uploaded_docs)
    claim.ai_report = json.dumps(ai_report)
    db.session.commit()

    result = {'readiness_score': final_score,
              'readiness_label': readiness_label,
              'breakdown': json.loads(claim.score_breakdown),
              'field_errors': field_errors,
              'consistency_issues': consistency_issues,
              'fraud_detection': {
                  'fraud_score': fraud_detection['fraud_score'],
                  'risk_level': fraud_detection['risk_level'],
                  'flags': fraud_detection['flags']
              },
              'overall_risk': overall_risk,
              'violations': violations,
              'ai_report': ai_report}
    return jsonify(result)

@app.route('/api/claims/<int:claim_id>/report', methods=['GET'])
def get_claim_report(claim_id):
    claim = Claim.query.get_or_404(claim_id)
    violations = Violation.query.filter_by(claim_id=claim_id).all()
    ins_type = InsuranceType.query.get(claim.insurance_type_id)
    form_data = json.loads(claim.form_data) if claim.form_data else {}

    # Build document status breakdown
    all_doc_rules      = Rule.query.filter_by(insurance_type_id=claim.insurance_type_id, rule_type='document').all()
    all_field_rules    = Rule.query.filter_by(insurance_type_id=claim.insurance_type_id, rule_type='field').all()
    uploaded_docs_list = json.loads(claim.uploaded_docs) if claim.uploaded_docs else []
    form_data_dict     = json.loads(claim.form_data) if claim.form_data else {}

    required_docs  = [r for r in all_doc_rules if r.is_required]
    optional_docs  = [r for r in all_doc_rules if not r.is_required]
    uploaded_req   = [r for r in required_docs if r.name in uploaded_docs_list]
    uploaded_opt   = [r for r in optional_docs if r.name in uploaded_docs_list]
    missing_req    = [r for r in required_docs if r.name not in uploaded_docs_list]

    required_fields = [r for r in all_field_rules if r.is_required]
    filled_fields   = [r for r in required_fields if form_data_dict.get(r.name)]
    missing_fields  = [r for r in required_fields if not form_data_dict.get(r.name)]

    doc_stats = {
        'total_required':   len(required_docs),
        'total_optional':   len(optional_docs),
        'uploaded_required': len(uploaded_req),
        'uploaded_optional': len(uploaded_opt),
        'missing_required': len(missing_req),
        'upload_rate':      round((len(uploaded_req) / len(required_docs) * 100) if required_docs else 0, 1),
        'required_docs':    [{'name': r.name, 'label': r.label, 'uploaded': r.name in uploaded_docs_list, 'weight': r.weight, 'severity': r.severity} for r in required_docs],
        'optional_docs':    [{'name': r.name, 'label': r.label, 'uploaded': r.name in uploaded_docs_list, 'weight': r.weight, 'severity': r.severity} for r in optional_docs],
    }

    field_stats = {
        'total_fields':   len(required_fields),
        'filled_fields':  len(filled_fields),
        'missing_fields': len(missing_fields),
        'fill_rate':      round((len(filled_fields) / len(required_fields) * 100) if required_fields else 0, 1),
        'fields':         [{'name': r.name, 'label': r.label, 'filled': bool(form_data_dict.get(r.name))} for r in required_fields],
    }

    return jsonify({
        'id': claim.id,
        'insurance_type': ins_type.name if ins_type else None,
        'insurance_type_code': ins_type.code if ins_type else None,
        'form_data': form_data_dict,
        'uploaded_docs': uploaded_docs_list,
        'readiness_score': claim.readiness_score,
        'score_breakdown': json.loads(claim.score_breakdown) if claim.score_breakdown else {},
        'readiness_label': claim.readiness_label,
        'ai_report': json.loads(claim.ai_report) if claim.ai_report else None,
        'doc_stats': doc_stats,
        'field_stats': field_stats,
        'status': claim.status,
        'violations': [{'rule_name': v.rule_name, 'message': v.message, 'suggestion': v.suggestion, 'severity': v.severity} for v in violations],
        'created_at': claim.created_at.isoformat() if claim.created_at else None
    })

@app.route('/api/claims/<int:claim_id>/upload', methods=['POST'])
def upload_document(claim_id):
    claim = Claim.query.get_or_404(claim_id)

    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    document_type = request.form.get('document_type')

    if not document_type:
        return jsonify({'error': 'Document type is required'}), 400
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    if not allowed_file(file.filename):
        return jsonify({'error': 'Only PDF, PNG, JPG files allowed'}), 400

    claim_folder = os.path.join(app.config['UPLOAD_FOLDER'], str(claim_id))
    os.makedirs(claim_folder, exist_ok=True)

    filename = secure_filename(file.filename)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    unique_filename = f"{document_type}_{timestamp}_{filename}"
    file_path = os.path.join(claim_folder, unique_filename)
    file.save(file_path)

    claim_doc = ClaimDocument(
        claim_id=claim_id,
        document_type=document_type,
        file_name=filename,
        file_path=file_path,
        file_size=os.path.getsize(file_path)
    )
    db.session.add(claim_doc)

    uploaded_docs = json.loads(claim.uploaded_docs) if claim.uploaded_docs else []
    if document_type not in uploaded_docs:
        uploaded_docs.append(document_type)
        claim.uploaded_docs = json.dumps(uploaded_docs)

    db.session.commit()

    return jsonify({
        'id': claim_doc.id,
        'document_type': document_type,
        'file_name': filename,
        'file_size': claim_doc.file_size,
        'uploaded_at': claim_doc.uploaded_at.isoformat(),
        'message': 'File uploaded successfully'
    }), 201

@app.route('/api/claims/<int:claim_id>/documents', methods=['GET'])
def get_claim_documents(claim_id):
    documents = ClaimDocument.query.filter_by(claim_id=claim_id).all()
    return jsonify([{
        'id': doc.id, 'document_type': doc.document_type,
        'file_name': doc.file_name, 'file_size': doc.file_size,
        'uploaded_at': doc.uploaded_at.isoformat()
    } for doc in documents])

@app.route('/api/claims/<int:claim_id>/documents/<int:doc_id>', methods=['DELETE'])
def delete_document(claim_id, doc_id):
    claim = Claim.query.get_or_404(claim_id)
    document = ClaimDocument.query.filter_by(id=doc_id, claim_id=claim_id).first_or_404()

    if os.path.exists(document.file_path):
        os.remove(document.file_path)

    doc_type = document.document_type
    db.session.delete(document)
    db.session.flush()

    remaining = ClaimDocument.query.filter_by(claim_id=claim_id, document_type=doc_type).count()
    if remaining == 0:
        uploaded_docs = json.loads(claim.uploaded_docs) if claim.uploaded_docs else []
        if doc_type in uploaded_docs:
            uploaded_docs.remove(doc_type)
            claim.uploaded_docs = json.dumps(uploaded_docs)

    db.session.commit()
    return jsonify({'message': 'Document deleted successfully'})

# ── Document Intelligence Routes ────────────────────────────────────────────

@app.route('/api/claims/<int:claim_id>/analyze-document', methods=['POST'])
def analyze_document(claim_id):
    """
    Analyze a document: OCR + classification + field extraction.
    
    Returns full analysis with OCR text, document type, and extracted fields.
    """
    if not OCR_AVAILABLE:
        return jsonify({'error': 'OCR service not available'}), 503
    
    claim = Claim.query.get_or_404(claim_id)
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    if not allowed_file(file.filename):
        return jsonify({'error': 'Only PDF, PNG, JPG files allowed'}), 400
    
    # Check file size (max 10MB)
    file.seek(0, 2)
    file_size = file.tell()
    file.seek(0)
    if file_size > 10 * 1024 * 1024:
        return jsonify({'error': 'File too large (max 10MB)'}), 400
    
    try:
        # Save file temporarily
        claim_folder = os.path.join(app.config['UPLOAD_FOLDER'], str(claim_id))
        os.makedirs(claim_folder, exist_ok=True)
        
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        temp_filename = f"ocr_temp_{timestamp}_{filename}"
        temp_file_path = os.path.join(claim_folder, temp_filename)
        
        file.save(temp_file_path)
        
        try:
            # Run analysis pipeline
            start_time = time.time()
            
            # 1. OCR
            ocr_text = extract_text(temp_file_path)
            ocr_confidence = 0.85 if ocr_text else 0.0
            
            # 2. Classification
            classification = classify_document(ocr_text)
            
            # 3. Field extraction
            field_result = extract_fields(ocr_text)
            extracted_fields = field_result.get('fields', {})
            field_confidence = field_result.get('confidence', {})
            field_warnings = field_result.get('warnings', [])
            
            # Calculate overall confidence
            if ocr_text:
                overall_confidence = (ocr_confidence + classification.get('confidence', 0) + 
                                    (sum(field_confidence.values()) / len(field_confidence) if field_confidence else 0)) / 3
            else:
                overall_confidence = 0.0
            
            processing_time = int((time.time() - start_time) * 1000)
            
            # Store analysis in database
            analysis_record = ClaimDocumentAnalysis(
                claim_id=claim_id,
                ocr_text=ocr_text,
                ocr_confidence=ocr_confidence,
                document_type=classification.get('type', 'unknown'),
                classification_confidence=classification.get('confidence', 0),
                extracted_fields=json.dumps(extracted_fields),
                confidence_score=overall_confidence,
            )
            db.session.add(analysis_record)
            db.session.commit()
            
            response = {
                'success': True,
                'analysis': {
                    'ocr': {
                        'text': ocr_text,
                        'confidence': ocr_confidence,
                        'error': None
                    },
                    'classification': {
                        'type': classification.get('type', 'unknown'),
                        'confidence': classification.get('confidence', 0),
                        'keywords_matched': classification.get('keywords_matched', [])
                    },
                    'extracted_fields': {
                        'fields': extracted_fields,
                        'confidence': field_confidence,
                        'field_count': len(extracted_fields),
                        'warnings': field_warnings
                    },
                    'confidence_score': overall_confidence,
                    'processing_time_ms': processing_time
                }
            }
            
            return jsonify(response), 201
            
        finally:
            # Clean up temp file
            if os.path.exists(temp_file_path):
                try:
                    os.remove(temp_file_path)
                except:
                    pass
    
    except Exception as e:
        logging.error(f"Document analysis failed: {e}", exc_info=True)
        return jsonify({'error': f'Analysis failed: {str(e)}'}), 500


@app.route('/api/claims/<int:claim_id>/extract-fields', methods=['POST'])
def extract_fields_endpoint(claim_id):
    """
    Extract fields from text or file.
    
    Accepts JSON with 'text' field, or multipart form with 'file'.
    """
    if not OCR_AVAILABLE:
        return jsonify({'error': 'OCR service not available'}), 503
    
    claim = Claim.query.get_or_404(claim_id)
    
    # Determine input source
    text_input = None
    
    # Check for JSON body with text
    if request.is_json:
        data = request.get_json()
        text_input = data.get('text', '').strip()
    
    # Check for file upload
    elif 'file' in request.files:
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        if not allowed_file(file.filename):
            return jsonify({'error': 'Only PDF, PNG, JPG files allowed'}), 400
        
        # Save file temporarily and extract text
        claim_folder = os.path.join(app.config['UPLOAD_FOLDER'], str(claim_id))
        os.makedirs(claim_folder, exist_ok=True)
        
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        temp_filename = f"ocr_temp_{timestamp}_{filename}"
        temp_file_path = os.path.join(claim_folder, temp_filename)
        
        try:
            file.save(temp_file_path)
            text_input = extract_text(temp_file_path)
        finally:
            if os.path.exists(temp_file_path):
                try:
                    os.remove(temp_file_path)
                except:
                    pass
    
    if not text_input:
        return jsonify({'error': 'No text or file provided'}), 400
    
    if len(text_input) > 50000:
        return jsonify({'error': 'Text too long (max 50000 chars)'}), 400
    
    try:
        field_result = extract_fields(text_input)
        return jsonify({
            'success': True,
            'extracted_fields': field_result.get('fields', {}),
            'confidence': field_result.get('confidence', {}),
            'warnings': field_result.get('warnings', []),
            'field_count': len(field_result.get('fields', {}))
        }), 200
    
    except Exception as e:
        logging.error(f"Field extraction failed: {e}", exc_info=True)
        return jsonify({'error': f'Extraction failed: {str(e)}'}), 500

@app.route('/uploads/<int:claim_id>/<filename>')
def serve_file(claim_id, filename):
    claim_folder = os.path.join(app.config['UPLOAD_FOLDER'], str(claim_id))
    return send_from_directory(claim_folder, filename)

# ── Approved Network ──────────────────────────────────────────────────────────

@app.route('/api/claims/<int:claim_id>/status', methods=['GET'])
def get_claim_status(claim_id):
    claim   = Claim.query.get_or_404(claim_id)
    history = ClaimStatusHistory.query.filter_by(claim_id=claim_id).order_by(ClaimStatusHistory.created_at.asc()).all()

    # Define all possible steps in order
    all_steps = [
        {'key': 'draft',           'label': 'Claim Created',       'icon': '📋', 'desc': 'Claim started and documents checklist opened'},
        {'key': 'documents',       'label': 'Documents Uploaded',  'icon': '📎', 'desc': 'Required documents uploaded and verified'},
        {'key': 'details',         'label': 'Details Filled',      'icon': '✏️',  'desc': 'Claim form filled with all required information'},
        {'key': 'incomplete',      'label': 'Validation Failed',   'icon': '⚠️',  'desc': 'Critical issues found — needs correction'},
        {'key': 'needs_attention', 'label': 'Needs Attention',     'icon': '🔔', 'desc': 'Some issues found — review recommended'},
        {'key': 'ready',           'label': 'Ready to Submit',     'icon': '✅', 'desc': 'All checks passed — claim is ready'},
        {'key': 'submitted',       'label': 'Submitted to Insurer','icon': '🚀', 'desc': 'Claim forwarded to insurance company'},
        {'key': 'under_review',    'label': 'Under Review',        'icon': '🔍', 'desc': 'Insurance company is reviewing your claim'},
        {'key': 'approved',        'label': 'Approved',            'icon': '🎉', 'desc': 'Claim approved by insurance company'},
        {'key': 'rejected',        'label': 'Rejected',            'icon': '❌', 'desc': 'Claim rejected — contact insurer for details'},
    ]

    # Determine which steps are completed based on history
    completed_statuses = {h.status for h in history}
    current_status     = claim.status

    # Auto-add document step if docs uploaded
    uploaded_docs = json.loads(claim.uploaded_docs) if claim.uploaded_docs else []
    if uploaded_docs:
        completed_statuses.add('documents')

    # Auto-add details step if form filled
    form_data = json.loads(claim.form_data) if claim.form_data else {}
    if form_data:
        completed_statuses.add('details')

    # Build timeline
    # For normal flow skip the failure steps if not in history
    failure_steps = {'incomplete', 'rejected'}
    timeline = []
    for step in all_steps:
        if step['key'] in failure_steps and step['key'] not in completed_statuses:
            continue  # skip failure steps unless they happened
        is_done    = step['key'] in completed_statuses
        is_current = step['key'] == current_status
        # Find note from history
        note = next((h.note for h in reversed(history) if h.status == step['key']), step['desc'])
        # Find timestamp
        ts   = next((h.created_at.isoformat() for h in history if h.status == step['key']), None)
        timeline.append({
            'key':     step['key'],
            'label':   step['label'],
            'icon':    step['icon'],
            'desc':    note,
            'done':    is_done,
            'current': is_current,
            'ts':      ts,
        })

    return jsonify({
        'claim_id':       claim_id,
        'current_status': current_status,
        'timeline':       timeline,
        'history': [{
            'status':     h.status,
            'note':       h.note,
            'created_at': h.created_at.isoformat()
        } for h in history]
    })

@app.route('/api/claims/<int:claim_id>/status', methods=['PUT'])
def update_claim_status(claim_id):
    """Manually update claim status (for admin/insurer updates)."""
    claim  = Claim.query.get_or_404(claim_id)
    data   = request.json
    status = data.get('status')
    note   = data.get('note', '')

    valid_statuses = ['draft','documents','details','incomplete','needs_attention','ready','submitted','under_review','approved','rejected']
    if status not in valid_statuses:
        return jsonify({'error': 'Invalid status'}), 400

    claim.status = status
    db.session.commit()
    log_status(claim_id, status, note)
    return jsonify({'message': 'Status updated', 'status': status})
def get_approved_network(insurance_type):
    from approved_network import get_recommendation
    city    = request.args.get('city', '')
    claim_id = request.args.get('claim_id')
    score   = 0
    if claim_id:
        claim = Claim.query.get(int(claim_id))
        if claim:
            score = claim.readiness_score or 0
    result = get_recommendation(insurance_type, score, city)
    return jsonify(result)

# ── Smart Document Analyzer ───────────────────────────────────────────────────

@app.route('/api/claims/<int:claim_id>/deadline', methods=['GET'])
def get_claim_deadline(claim_id):
    claim    = Claim.query.get_or_404(claim_id)
    ins_type = InsuranceType.query.get(claim.insurance_type_id)
    form_data = json.loads(claim.form_data) if claim.form_data else {}
    if not ins_type:
        return jsonify({'deadline': None})
    from deadline_tracker import calculate_deadline
    deadline = calculate_deadline(ins_type.code, form_data)
    return jsonify({'deadline': deadline})

@app.route('/api/claims/<int:claim_id>/comparison', methods=['GET'])
def get_claim_comparison(claim_id):
    claim      = Claim.query.get_or_404(claim_id)
    violations = Violation.query.filter_by(claim_id=claim_id).all()
    ins_type   = InsuranceType.query.get(claim.insurance_type_id)
    form_data  = json.loads(claim.form_data) if claim.form_data else {}

    # Get all past claims for this user
    past_claims = Claim.query.filter(
        Claim.user_id == claim.user_id,
        Claim.id != claim_id
    ).all() if claim.user_id else []

    from claim_comparison import compare_claims, get_rejection_predictor
    comparison = compare_claims(claim, past_claims, [{'severity': v.severity} for v in violations])
    rejection  = get_rejection_predictor(
        ins_type.code if ins_type else 'health',
        form_data,
        [{'severity': v.severity} for v in violations]
    )
    return jsonify({'comparison': comparison, 'rejection': rejection})

@app.route('/api/claims/<int:claim_id>/analyze', methods=['POST'])
def analyze_claim_documents(claim_id):
    claim = Claim.query.get_or_404(claim_id)
    documents = ClaimDocument.query.filter_by(claim_id=claim_id).all()

    if not documents:
        return jsonify({'findings': [], 'message': 'No documents uploaded yet'})

    uploaded_file_paths = {doc.document_type: doc.file_path for doc in documents}

    from document_analyzer import analyze_documents
    findings = analyze_documents(claim, uploaded_file_paths)

    return jsonify({
        'findings':        findings,
        'total':           len(findings),
        'issues':          len([f for f in findings if f['type'] in ['mismatch']]),
        'confirmations':   len([f for f in findings if f['type'] == 'match']),
        'analyzed_docs':   len(documents),
    })

# ── Claim Package (PDF Download) ──────────────────────────────────────────────

@app.route('/api/claims/<int:claim_id>/package', methods=['GET'])
def download_claim_package(claim_id):
    from flask import send_file
    claim      = Claim.query.get_or_404(claim_id)
    violations = Violation.query.filter_by(claim_id=claim_id).all()
    rules      = Rule.query.filter_by(insurance_type_id=claim.insurance_type_id).all()
    ai_report  = json.loads(claim.ai_report) if claim.ai_report else None

    # Generate PDF
    packages_dir = os.path.join(os.path.dirname(__file__), 'packages')
    os.makedirs(packages_dir, exist_ok=True)
    output_path = os.path.join(packages_dir, f'claim_{claim_id}_package.pdf')

    from claim_package import generate_claim_package
    generate_claim_package(claim, rules, violations, ai_report, output_path)

    return send_file(
        output_path,
        as_attachment=True,
        download_name=f'ClaimGuard_Claim_{claim_id}_Package.pdf',
        mimetype='application/pdf'
    )

# ── QR Code ──────────────────────────────────────────────────────────────────

@app.route('/api/claims/<int:claim_id>/qr', methods=['GET'])
def get_claim_qr(claim_id):
    """Generate QR code that links to the claim report page."""
    import qrcode
    import io
    import base64

    claim = Claim.query.get_or_404(claim_id)

    # URL that QR will point to — the public report page
    frontend_url = f'http://localhost:3000/report/{claim_id}'

    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(frontend_url)
    qr.make(fit=True)

    img = qr.make_image(fill_color='#3b82f6', back_color='#0c1120')

    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)

    img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

    ins_type = InsuranceType.query.get(claim.insurance_type_id)
    form_data = json.loads(claim.form_data) if claim.form_data else {}

    return jsonify({
        'qr_image':    f'data:image/png;base64,{img_base64}',
        'claim_url':   frontend_url,
        'claim_id':    claim_id,
        'insurance_type': ins_type.name if ins_type else None,
        'policy_number':  form_data.get('policy_number') or form_data.get('vehicle_number') or 'N/A',
        'readiness_score': claim.readiness_score,
        'readiness_label': claim.readiness_label,
    })

# ── Insurance Company Submit ──────────────────────────────────────────────────

INSURANCE_COMPANIES = [
    {'id': 1, 'name': 'Star Health Insurance',      'code': 'star_health',   'types': ['health'],              'email': 'claims@starhealth.in',    'logo': '⭐'},
    {'id': 2, 'name': 'HDFC ERGO',                  'code': 'hdfc_ergo',     'types': ['health','vehicle','property'], 'email': 'claims@hdfcergo.com', 'logo': '🏦'},
    {'id': 3, 'name': 'ICICI Lombard',              'code': 'icici_lombard', 'types': ['health','vehicle','travel'],   'email': 'claims@icicilombard.com', 'logo': '🔵'},
    {'id': 4, 'name': 'Bajaj Allianz',              'code': 'bajaj_allianz', 'types': ['health','vehicle','life','property'], 'email': 'claims@bajajallianz.co.in', 'logo': '🟠'},
    {'id': 5, 'name': 'LIC of India',               'code': 'lic',           'types': ['life'],                'email': 'claims@licindia.in',      'logo': '🇮🇳'},
    {'id': 6, 'name': 'New India Assurance',        'code': 'new_india',     'types': ['property','crop','vehicle'], 'email': 'claims@newindia.co.in', 'logo': '🏛️'},
    {'id': 7, 'name': 'Agriculture Insurance Co.', 'code': 'aic',           'types': ['crop'],                'email': 'claims@aicofindia.com',   'logo': '🌾'},
    {'id': 8, 'name': 'Tata AIG',                  'code': 'tata_aig',      'types': ['travel','vehicle','health'], 'email': 'claims@tataaig.com',  'logo': '🔴'},
]

@app.route('/api/insurance-companies', methods=['GET'])
def get_insurance_companies():
    """Return list of partner insurance companies."""
    ins_type_code = request.args.get('type', '')
    if ins_type_code:
        filtered = [c for c in INSURANCE_COMPANIES if ins_type_code in c['types']]
    else:
        filtered = INSURANCE_COMPANIES
    return jsonify(filtered)

@app.route('/api/claims/<int:claim_id>/submit', methods=['POST'])
def submit_to_insurer(claim_id):
    """Submit claim to selected insurance company."""
    claim    = Claim.query.get_or_404(claim_id)
    data     = request.json
    company_id = data.get('company_id')

    if not company_id:
        return jsonify({'error': 'Company ID is required'}), 400

    company = next((c for c in INSURANCE_COMPANIES if c['id'] == company_id), None)
    if not company:
        return jsonify({'error': 'Insurance company not found'}), 404

    if claim.readiness_score is None or claim.readiness_score < 50:
        return jsonify({'error': 'Claim score is too low to submit. Please fix all issues first.'}), 400

    ins_type = InsuranceType.query.get(claim.insurance_type_id)
    form_data = json.loads(claim.form_data) if claim.form_data else {}

    # Mark claim as submitted
    claim.status = 'submitted'
    db.session.commit()
    log_status(claim_id, 'submitted', f'Claim submitted to {company["name"]}. Reference will be generated.')

    # In production this would send an actual API call / email to the insurer
    # For now we simulate a successful submission
    return jsonify({
        'success':          True,
        'message':          f'Claim successfully submitted to {company["name"]}',
        'company':          company["name"],
        'reference_number': f'CG-{claim_id}-{company["code"].upper()}-{datetime.now().strftime("%Y%m%d%H%M")}',
        'submitted_at':     datetime.utcnow().isoformat(),
        'next_steps':       f'You will receive a confirmation email at your registered address. {company["name"]} will contact you within 3-5 business days.',
        'claim_id':         claim_id,
        'insurance_type':   ins_type.name if ins_type else None,
        'score':            claim.readiness_score,
    })

# ── Agent Routes ──────────────────────────────────────────────────────────────

@app.route('/api/agent/clients', methods=['GET'])
@jwt_required()
def get_agent_clients():
    agent_id = get_jwt_identity()
    agent = db.session.get(User, agent_id)
    if not agent or agent.role != 'agent':
        return jsonify({'error': 'Agent access required'}), 403

    links = AgentClient.query.filter_by(agent_id=agent_id).all()
    clients = []
    for link in links:
        client = db.session.get(User, link.client_id)
        if not client: continue
        claims = Claim.query.filter_by(user_id=link.client_id).all()
        scores = [c.readiness_score for c in claims if c.readiness_score is not None]
        clients.append({
            'id':           client.id,
            'full_name':    client.full_name,
            'email':        client.email,
            'total_claims': len(claims),
            'avg_score':    round(sum(scores)/len(scores), 1) if scores else 0,
            'ready_claims': len([c for c in claims if c.status == 'ready']),
            'pending_claims': len([c for c in claims if c.status in ['draft','incomplete','needs_attention']]),
            'submitted_claims': len([c for c in claims if c.status in ['submitted','under_review','approved']]),
            'linked_at':    link.created_at.isoformat(),
        })
    return jsonify({'clients': clients, 'total': len(clients)})

@app.route('/api/agent/clients', methods=['POST'])
@jwt_required()
def add_agent_client():
    agent_id = get_jwt_identity()
    agent = db.session.get(User, agent_id)
    if not agent or agent.role != 'agent':
        return jsonify({'error': 'Agent access required'}), 403

    data = request.json
    client_email = data.get('email', '').strip().lower()
    client = User.query.filter_by(email=client_email).first()
    if not client:
        return jsonify({'error': 'No user found with this email'}), 404
    if client.role != 'customer':
        return jsonify({'error': 'Can only add customers as clients'}), 400

    existing = AgentClient.query.filter_by(agent_id=agent_id, client_id=client.id).first()
    if existing:
        return jsonify({'error': 'Client already added'}), 409

    link = AgentClient(agent_id=agent_id, client_id=client.id)
    db.session.add(link)
    db.session.commit()
    return jsonify({'message': f'{client.full_name} added as client', 'client_id': client.id}), 201

@app.route('/api/agent/clients/<int:client_id>', methods=['DELETE'])
@jwt_required()
def remove_agent_client(client_id):
    agent_id = get_jwt_identity()
    link = AgentClient.query.filter_by(agent_id=agent_id, client_id=client_id).first_or_404()
    db.session.delete(link)
    db.session.commit()
    return jsonify({'message': 'Client removed'})

@app.route('/api/agent/clients/<int:client_id>/claims', methods=['GET'])
@jwt_required()
def get_client_claims(client_id):
    agent_id = get_jwt_identity()
    agent = db.session.get(User, agent_id)
    if not agent or agent.role != 'agent':
        return jsonify({'error': 'Agent access required'}), 403

    link = AgentClient.query.filter_by(agent_id=agent_id, client_id=client_id).first()
    if not link:
        return jsonify({'error': 'Client not in your portfolio'}), 403

    claims = Claim.query.filter_by(user_id=client_id).order_by(Claim.created_at.desc()).all()
    result = []
    for c in claims:
        form_data = json.loads(c.form_data) if c.form_data else {}
        ins_type  = db.session.get(InsuranceType, c.insurance_type_id)
        result.append({
            'id': c.id, 'insurance_type': ins_type.name if ins_type else None,
            'policy_number': form_data.get('policy_number', 'N/A'),
            'readiness_score': c.readiness_score, 'readiness_label': c.readiness_label,
            'status': c.status, 'created_at': c.created_at.isoformat()
        })
    return jsonify({'claims': result})

@app.route('/api/agent/stats', methods=['GET'])
@jwt_required()
def get_agent_stats():
    agent_id = get_jwt_identity()
    agent = db.session.get(User, agent_id)
    if not agent or agent.role != 'agent':
        return jsonify({'error': 'Agent access required'}), 403

    links = AgentClient.query.filter_by(agent_id=agent_id).all()
    client_ids = [l.client_id for l in links]
    all_claims = Claim.query.filter(Claim.user_id.in_(client_ids)).all() if client_ids else []
    scores = [c.readiness_score for c in all_claims if c.readiness_score is not None]

    return jsonify({
        'total_clients':    len(links),
        'total_claims':     len(all_claims),
        'avg_score':        round(sum(scores)/len(scores), 1) if scores else 0,
        'ready_to_submit':  len([c for c in all_claims if c.status == 'ready']),
        'submitted':        len([c for c in all_claims if c.status in ['submitted','under_review']]),
        'approved':         len([c for c in all_claims if c.status == 'approved']),
        'needs_attention':  len([c for c in all_claims if c.status in ['incomplete','needs_attention']]),
    })

# ── Insurer Routes ────────────────────────────────────────────────────────────

@app.route('/api/insurer/claims', methods=['GET'])
@jwt_required()
def get_insurer_claims():
    user_id = get_jwt_identity()
    user = db.session.get(User, user_id)
    if not user or user.role != 'insurer':
        return jsonify({'error': 'Insurer access required'}), 403

    status_filter = request.args.get('status', '')
    page     = request.args.get('page', 1, type=int)
    per_page = 15

    query = Claim.query.filter(Claim.status.in_(['submitted','under_review','approved','rejected']))
    if status_filter:
        query = query.filter_by(status=status_filter)
    total = query.count()
    claims = query.order_by(Claim.created_at.desc()).offset((page-1)*per_page).limit(per_page).all()

    result = []
    for c in claims:
        form_data = json.loads(c.form_data) if c.form_data else {}
        ins_type  = db.session.get(InsuranceType, c.insurance_type_id)
        claimant  = db.session.get(User, c.user_id) if c.user_id else None
        result.append({
            'id':              c.id,
            'insurance_type':  ins_type.name if ins_type else None,
            'insurance_code':  ins_type.code if ins_type else None,
            'claimant_name':   claimant.full_name if claimant else 'Unknown',
            'claimant_email':  claimant.email if claimant else None,
            'policy_number':   form_data.get('policy_number', 'N/A'),
            'claim_amount':    form_data.get('claim_amount', 0),
            'readiness_score': c.readiness_score,
            'readiness_label': c.readiness_label,
            'status':          c.status,
            'insurer_notes':   c.insurer_notes,
            'assigned_insurer': c.assigned_insurer,
            'created_at':      c.created_at.isoformat(),
        })
    return jsonify({'claims': result, 'total': total, 'page': page, 'pages': (total+per_page-1)//per_page})

@app.route('/api/insurer/claims/<int:claim_id>/review', methods=['PUT'])
@jwt_required()
def review_claim(claim_id):
    user_id = get_jwt_identity()
    user = db.session.get(User, user_id)
    if not user or user.role != 'insurer':
        return jsonify({'error': 'Insurer access required'}), 403

    claim  = Claim.query.get_or_404(claim_id)
    data   = request.json
    action = data.get('action')  # approve | reject | request_info | under_review
    notes  = data.get('notes', '')

    status_map = {
        'approve':      'approved',
        'reject':       'rejected',
        'request_info': 'needs_attention',
        'under_review': 'under_review',
    }

    if action not in status_map:
        return jsonify({'error': 'Invalid action'}), 400

    new_status = status_map[action]
    claim.status = new_status
    claim.insurer_notes = notes
    db.session.commit()
    log_status(claim_id, new_status, f'Insurer action: {action}. Notes: {notes}')

    return jsonify({
        'message':    f'Claim {action}d successfully',
        'claim_id':   claim_id,
        'new_status': new_status,
        'notes':      notes,
    })

@app.route('/api/insurer/stats', methods=['GET'])
@jwt_required()
def get_insurer_stats():
    user_id = get_jwt_identity()
    user = db.session.get(User, user_id)
    if not user or user.role != 'insurer':
        return jsonify({'error': 'Insurer access required'}), 403

    submitted    = Claim.query.filter_by(status='submitted').count()
    under_review = Claim.query.filter_by(status='under_review').count()
    approved     = Claim.query.filter_by(status='approved').count()
    rejected     = Claim.query.filter_by(status='rejected').count()
    total        = submitted + under_review + approved + rejected

    scores = [c.readiness_score for c in Claim.query.filter(
        Claim.status.in_(['submitted','under_review','approved','rejected']),
        Claim.readiness_score.isnot(None)
    ).all()]

    return jsonify({
        'total_received':  total,
        'pending_review':  submitted + under_review,
        'approved':        approved,
        'rejected':        rejected,
        'approval_rate':   round(approved / total * 100, 1) if total else 0,
        'avg_claim_score': round(sum(scores)/len(scores), 1) if scores else 0,
    })

def seed_default_users():
    """Seed default test users on first run if no users exist."""
    with app.app_context():
        # Check if any users exist
        if User.query.first():
            return  # Users already exist, don't seed
        
        # Create default test users
        test_users = [
            ('Test Customer', 'customer@test.com', 'password123', 'customer', None),
            ('Test Agent', 'agent@test.com', 'password123', 'agent', None),
            ('Test Insurer', 'insurer@test.com', 'password123', 'insurer', 'Test Insurance Co'),
        ]
        
        for full_name, email, password, role, company in test_users:
            hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            user = User(full_name=full_name, email=email, password=hashed_pw, role=role, company=company)
            db.session.add(user)
        
        db.session.commit()
        print("✓ Default test users seeded on first run")

if __name__ == '__main__':
    # Auto-seed default users on first run
    seed_default_users()
    app.run(debug=True, port=5000)
