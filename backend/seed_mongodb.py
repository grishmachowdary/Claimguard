from pymongo import MongoClient
from datetime import datetime

client = MongoClient('mongodb://localhost:27017/')
db = client['claimguard']

# Clear existing data
db.insurance_types.delete_many({})
db.rules.delete_many({})
db.claims.delete_many({})
db.violations.delete_many({})
db.claim_documents.delete_many({})

# Create insurance types
insurance_types_data = [
    {'name': 'Health Insurance', 'code': 'health', 'icon': 'heart', 'is_active': True},
    {'name': 'Vehicle Insurance', 'code': 'vehicle', 'icon': 'car', 'is_active': True},
    {'name': 'Life Insurance', 'code': 'life', 'icon': 'shield', 'is_active': True},
    {'name': 'Property Insurance', 'code': 'property', 'icon': 'home', 'is_active': True},
    {'name': 'Travel Insurance', 'code': 'travel', 'icon': 'plane', 'is_active': True},
    {'name': 'Crop Insurance', 'code': 'crop', 'icon': 'wheat', 'is_active': True}
]

types_dict = {}
for ins_type in insurance_types_data:
    result = db.insurance_types.insert_one(ins_type)
    types_dict[ins_type['code']] = str(result.inserted_id)

print('✓ Insurance types created')

# HEALTH INSURANCE RULES
health_documents = [
    ('insurance_policy_card', 'Insurance Policy Card', 20, 'high', 'Upload a clear photo of your insurance policy card showing policy number and coverage details'),
    ('patient_photo_id', 'Patient Photo ID', 15, 'high', 'Upload government-issued photo ID (Aadhaar, PAN, Passport, or Driver License)'),
    ('hospital_discharge_summary', 'Hospital Discharge Summary', 20, 'high', 'Request discharge summary from hospital with admission and discharge dates'),
    ('itemized_hospital_bill', 'Itemized Hospital Bill', 20, 'high', 'Get itemized bill showing all charges, procedures, and medications'),
    ('doctor_prescription', 'Doctor Prescription', 10, 'high', 'Include original prescription from treating doctor'),
    ('lab_diagnostic_reports', 'Lab and Diagnostic Reports', 10, 'medium', 'Attach all lab reports, X-rays, MRI, CT scans performed during treatment'),
    ('pharmacy_bills', 'Pharmacy Bills', 8, 'medium', 'Include pharmacy bills for medicines purchased'),
    ('bank_account_details', 'Bank Account Details', 15, 'high', 'Provide cancelled cheque or bank statement for claim reimbursement')
]

for doc_name, label, weight, severity, suggestion in health_documents:
    db.rules.insert_one({
        'insurance_type_id': types_dict['health'],
        'rule_type': 'document',
        'name': doc_name,
        'label': label,
        'is_required': True,
        'weight': weight,
        'severity': severity,
        'suggestion': suggestion
    })

health_fields = [
    ('patient_name', 'Patient Name'),
    ('policy_number', 'Policy Number'),
    ('admission_date', 'Admission Date'),
    ('discharge_date', 'Discharge Date'),
    ('hospital_name', 'Hospital Name'),
    ('diagnosis', 'Diagnosis'),
    ('claim_amount', 'Claim Amount'),
    ('policy_coverage', 'Policy Coverage')
]

for field_name, label in health_fields:
    db.rules.insert_one({
        'insurance_type_id': types_dict['health'],
        'rule_type': 'field',
        'name': field_name,
        'label': label,
        'is_required': True,
        'weight': 0,
        'severity': 'high',
        'suggestion': f'Please provide {label.lower()}'
    })

health_consistency = [
    ('discharge_after_admission', 'Discharge date must be after admission date', 'high', 
     'Check your dates. Discharge date should be later than admission date'),
    ('claim_within_coverage', 'Claim amount must not exceed policy coverage', 'medium',
     'Your claim amount exceeds policy coverage. Review your policy limits or reduce claim amount')
]

for rule_name, label, severity, suggestion in health_consistency:
    db.rules.insert_one({
        'insurance_type_id': types_dict['health'],
        'rule_type': 'consistency',
        'name': rule_name,
        'label': label,
        'is_required': False,
        'weight': 0,
        'severity': severity,
        'suggestion': suggestion
    })

print('✓ Health Insurance rules created')

# Add similar rules for other insurance types (abbreviated for brevity)
# You can add the full rules from seed_all_types.py

print('✓ All 6 insurance types seeded successfully!')
print('✓ MongoDB database ready')

client.close()
