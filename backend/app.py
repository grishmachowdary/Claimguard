from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
import bcrypt
import json
import os

app = Flask(__name__)
CORS(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///claimguard.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'claimguard-secret-key-change-in-production'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=7)
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'uploads')
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

# ── Auth Routes ──────────────────────────────────────────────────────────────

@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.json
    full_name = data.get('full_name', '').strip()
    email     = data.get('email', '').strip().lower()
    password  = data.get('password', '')

    if not full_name or not email or not password:
        return jsonify({'error': 'All fields are required'}), 400
    if len(password) < 6:
        return jsonify({'error': 'Password must be at least 6 characters'}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Email already registered'}), 409

    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    user = User(full_name=full_name, email=email, password=hashed)
    db.session.add(user)
    db.session.commit()

    token = create_access_token(identity=str(user.id))
    return jsonify({
        'token': token,
        'user': {'id': user.id, 'full_name': user.full_name, 'email': user.email}
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
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    return jsonify({'id': user.id, 'full_name': user.full_name, 'email': user.email})

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
    all_claims = Claim.query.order_by(Claim.created_at.desc()).all()
    result = []
    for c in all_claims:
        form_data = json.loads(c.form_data) if c.form_data else {}
        ins_type = InsuranceType.query.get(c.insurance_type_id)
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
    return jsonify(result)

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
def validate_claim(claim_id):
    claim = Claim.query.get_or_404(claim_id)
    from rule_engine import validate_claim as run_validation
    result = run_validation(claim)

    # Update status based on score
    if result['score'] >= 80:
        claim.status = 'ready'
        note = f'Validation complete. Score: {result["score"]}/100. Claim is ready to submit.'
    elif result['score'] >= 50:
        claim.status = 'needs_attention'
        note = f'Validation complete. Score: {result["score"]}/100. Some issues need attention.'
    else:
        claim.status = 'incomplete'
        note = f'Validation complete. Score: {result["score"]}/100. Critical issues found.'
    db.session.commit()
    log_status(claim_id, claim.status, note)

    # Generate AI report
    from ai_report import generate_ai_report
    rules        = Rule.query.filter_by(insurance_type_id=claim.insurance_type_id).all()
    uploaded_docs = json.loads(claim.uploaded_docs) if claim.uploaded_docs else []
    ai_report    = generate_ai_report(claim, result['violations'], rules, uploaded_docs)
    claim.ai_report = json.dumps(ai_report)
    db.session.commit()

    result['ai_report'] = ai_report
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

if __name__ == '__main__':
    app.run(debug=True, port=5000)
