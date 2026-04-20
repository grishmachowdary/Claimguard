from app import app, db, InsuranceType, Rule

def seed_database():
    with app.app_context():
        db.create_all()
        
        # Clear existing data
        Rule.query.delete()
        InsuranceType.query.delete()
        db.session.commit()
        
        # Create Health Insurance type
        health = InsuranceType(
            name='Health Insurance',
            code='health',
            icon='heart',
            is_active=True
        )
        db.session.add(health)
        db.session.commit()
        
        # Document rules
        documents = [
            ('Insurance Policy Card', 20, 'high', 'Upload a clear photo of your insurance policy card showing policy number and coverage details'),
            ('Patient Photo ID', 15, 'high', 'Upload government-issued photo ID (Aadhaar, PAN, Passport, or Driver License)'),
            ('Hospital Discharge Summary', 20, 'high', 'Request discharge summary from hospital with admission and discharge dates'),
            ('Itemized Hospital Bill', 20, 'high', 'Get itemized bill showing all charges, procedures, and medications'),
            ('Doctor Prescription', 10, 'high', 'Include original prescription from treating doctor'),
            ('Lab and Diagnostic Reports', 10, 'medium', 'Attach all lab reports, X-rays, MRI, CT scans performed during treatment'),
            ('Pharmacy Bills', 8, 'medium', 'Include pharmacy bills for medicines purchased'),
            ('Bank Account Details', 15, 'high', 'Provide cancelled cheque or bank statement for claim reimbursement')
        ]
        
        for doc_name, weight, severity, suggestion in documents:
            rule = Rule(
                insurance_type_id=health.id,
                rule_type='document',
                name=doc_name.lower().replace(' ', '_'),
                label=doc_name,
                is_required=True,
                weight=weight,
                severity=severity,
                suggestion=suggestion
            )
            db.session.add(rule)
        
        # Field rules
        fields = [
            ('patient_name', 'Patient Name'),
            ('policy_number', 'Policy Number'),
            ('admission_date', 'Admission Date'),
            ('discharge_date', 'Discharge Date'),
            ('hospital_name', 'Hospital Name'),
            ('diagnosis', 'Diagnosis'),
            ('claim_amount', 'Claim Amount'),
            ('policy_coverage', 'Policy Coverage')
        ]
        
        for field_name, label in fields:
            rule = Rule(
                insurance_type_id=health.id,
                rule_type='field',
                name=field_name,
                label=label,
                is_required=True,
                weight=0,
                severity='high',
                suggestion=f'Please provide {label.lower()}'
            )
            db.session.add(rule)
        
        # Consistency rules
        consistency_rules = [
            ('discharge_after_admission', 'Discharge date must be after admission date', 'high', 
             'Check your dates. Discharge date should be later than admission date'),
            ('claim_within_coverage', 'Claim amount must not exceed policy coverage', 'medium',
             'Your claim amount exceeds policy coverage. Review your policy limits or reduce claim amount')
        ]
        
        for rule_name, label, severity, suggestion in consistency_rules:
            rule = Rule(
                insurance_type_id=health.id,
                rule_type='consistency',
                name=rule_name,
                label=label,
                is_required=False,
                weight=0,
                severity=severity,
                suggestion=suggestion
            )
            db.session.add(rule)
        
        db.session.commit()
        print('Database seeded successfully!')

if __name__ == '__main__':
    seed_database()
