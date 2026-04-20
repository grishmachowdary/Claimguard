from app import app, db, InsuranceType, Rule

def seed():
    with app.app_context():
        db.create_all()
        Rule.query.delete()
        InsuranceType.query.delete()
        db.session.commit()

        types = [
            ('Health Insurance',    'health',   'heart'),
            ('Vehicle Insurance',   'vehicle',  'car'),
            ('Life Insurance',      'life',     'shield'),
            ('Property Insurance',  'property', 'home'),
            ('Travel Insurance',    'travel',   'plane'),
            ('Crop Insurance',      'crop',     'wheat'),
        ]

        ids = {}
        for name, code, icon in types:
            t = InsuranceType(name=name, code=code, icon=icon, is_active=True)
            db.session.add(t)
            db.session.flush()
            ids[code] = t.id
        db.session.commit()

        # ── HEALTH ──────────────────────────────────────────────────────────
        add_docs(ids['health'], [
            ('insurance_policy',   'Insurance Policy Card',           True,  20, 'high',   'Upload a clear copy of your insurance policy card'),
            ('patient_id',         'Patient Photo ID',                True,  15, 'high',   'Upload government-issued photo ID'),
            ('discharge_summary',  'Hospital Discharge Summary',      True,  20, 'high',   'Request discharge summary from the hospital'),
            ('hospital_bill',      'Itemized Hospital Bill',          True,  20, 'high',   'Get itemized bill showing all charges'),
            ('doctor_prescription','Doctor Prescription',             True,  10, 'high',   'Include original prescription from treating doctor'),
            ('lab_reports',        'Lab and Diagnostic Reports',      True,  10, 'medium', 'Attach all lab reports, X-rays, MRI, CT scans'),
            ('pharmacy_bills',     'Pharmacy Bills and Receipts',     True,   8, 'medium', 'Include pharmacy bills for medicines purchased'),
            ('bank_details',       'Bank Account Details',            True,  15, 'high',   'Provide cancelled cheque or bank statement'),
            ('pre_auth_letter',    'Pre-Authorization Letter',        False,  5, 'medium', 'Include pre-auth letter if treatment was planned'),
            ('doctors_certificate','Attending Doctor Certificate',    False,  5, 'low',    'Certificate from attending doctor if available'),
        ])
        add_fields(ids['health'], [
            ('patient_name',    'Patient Name'),
            ('policy_number',   'Policy Number'),
            ('admission_date',  'Admission Date'),
            ('discharge_date',  'Discharge Date'),
            ('hospital_name',   'Hospital Name'),
            ('diagnosis',       'Diagnosis'),
            ('claim_amount',    'Claim Amount'),
            ('policy_coverage', 'Policy Coverage'),
        ])
        add_consistency(ids['health'], [
            ('discharge_after_admission', 'Discharge date must be after admission date',   'high',   'Check your dates — discharge must be after admission'),
            ('claim_within_coverage',     'Claim amount must not exceed policy coverage',  'medium', 'Reduce claim amount or review your policy coverage'),
        ])

        # ── VEHICLE ─────────────────────────────────────────────────────────
        add_docs(ids['vehicle'], [
            ('insurance_policy', 'Insurance Policy Document',     True,  20, 'high',   'Upload current vehicle insurance policy'),
            ('vehicle_rc',       'Vehicle RC Book',               True,  15, 'high',   'Upload Registration Certificate of the vehicle'),
            ('driving_license',  'Driving License of Driver',     True,  20, 'high',   'Upload valid driving license of driver at time of incident'),
            ('fir_report',       'FIR / Police Report',           True,  15, 'high',   'File FIR at nearest police station and upload copy'),
            ('claim_form',       'Filled Claim Form',             True,  10, 'medium', 'Download and fill the insurer claim form'),
            ('damage_photos',    'Photos of Damage',              True,  10, 'medium', 'Take clear photos of vehicle damage from all angles'),
            ('surveyor_report',  'Surveyor Inspection Report',    True,  10, 'medium', 'Get surveyor report from insurance company'),
            ('repair_estimate',  'Garage Repair Estimate',        True,  10, 'medium', 'Get written repair estimate from authorized garage'),
            ('original_keys',    'Original Vehicle Keys',         False,  5, 'medium', 'Submit original keys for theft claims'),
            ('noc_financer',     'NOC from Financer',             False,  5, 'low',    'Get NOC from bank/financer if vehicle is on loan'),
        ])
        add_fields(ids['vehicle'], [
            ('vehicle_number',       'Vehicle Registration Number'),
            ('policy_number',        'Policy Number'),
            ('incident_date',        'Incident Date'),
            ('incident_location',    'Incident Location'),
            ('incident_description', 'Incident Description'),
            ('driver_name',          'Driver Name'),
            ('claim_amount',         'Claim Amount'),
            ('policy_coverage',      'Policy Coverage'),
        ])
        add_consistency(ids['vehicle'], [
            ('claim_within_coverage', 'Claim amount must not exceed policy coverage', 'medium', 'Review your policy limits'),
        ])

        # ── LIFE ────────────────────────────────────────────────────────────
        add_docs(ids['life'], [
            ('policy_bond',       'Original Policy Bond',                True,  20, 'high',   'Submit original life insurance policy bond'),
            ('death_certificate', 'Death Certificate',                   True,  25, 'high',   'Original death certificate from municipal authority'),
            ('nominee_id',        'Nominee Photo ID',                    True,  15, 'high',   'Government-issued ID of the nominee'),
            ('nominee_bank',      'Nominee Bank Account Details',        True,  15, 'high',   'Cancelled cheque or bank statement of nominee'),
            ('claim_form',        'Filled Claim Form',                   True,  10, 'high',   'Fill and sign the insurer claim form'),
            ('medical_records',   'Medical Records / Death Summary',     True,  10, 'high',   'Hospital records related to cause of death'),
            ('post_mortem',       'Post Mortem Report',                  False,  8, 'high',   'Required for accidental or unnatural death'),
            ('fir_report',        'FIR / Police Report',                 False,  8, 'high',   'Required for accidental death claims'),
            ('legal_heir',        'Legal Heir Certificate',              False,  5, 'medium', 'Required if no nominee is registered'),
        ])
        add_fields(ids['life'], [
            ('policy_number',             'Policy Number'),
            ('insured_name',              'Insured Person Name'),
            ('date_of_death',             'Date of Death'),
            ('cause_of_death',            'Cause of Death'),
            ('claimant_name',             'Claimant Name'),
            ('relationship_with_insured', 'Relationship with Insured'),
            ('claim_amount',              'Claim Amount'),
            ('sum_assured',               'Sum Assured'),
        ])
        add_consistency(ids['life'], [
            ('claim_matches_sum_assured', 'Claim amount should match sum assured', 'medium', 'Verify claim amount equals the sum assured in policy'),
        ])

        # ── PROPERTY ────────────────────────────────────────────────────────
        add_docs(ids['property'], [
            ('insurance_policy',  'Insurance Policy Document',        True,  20, 'high',   'Upload current property insurance policy'),
            ('ownership_proof',   'Property Ownership Proof',         True,  20, 'high',   'Sale deed, property deed or ownership document'),
            ('claim_form',        'Filled Claim Form',                True,  10, 'high',   'Fill and sign the insurer claim form'),
            ('damage_photos',     'Photos and Videos of Damage',      True,  15, 'high',   'Take clear photos/videos of all damaged areas'),
            ('fir_report',        'FIR for Theft or Vandalism',       True,  10, 'high',   'File FIR at nearest police station'),
            ('surveyor_report',   'Surveyor Loss Assessor Report',    True,  10, 'high',   'Get loss assessment report from insurer surveyor'),
            ('repair_estimate',   'Repair Estimate from Contractor',  True,  10, 'medium', 'Get written estimate from licensed contractor'),
            ('fire_brigade_report','Fire Brigade Report',             False,  8, 'high',   'Required for fire damage claims'),
            ('purchase_bills',    'Original Purchase Bills',          False,  5, 'medium', 'Bills for items damaged or stolen'),
        ])
        add_fields(ids['property'], [
            ('policy_number',     'Policy Number'),
            ('owner_name',        'Property Owner Name'),
            ('property_address',  'Property Address'),
            ('incident_date',     'Incident Date'),
            ('incident_type',     'Incident Type (Fire / Theft / Natural Disaster)'),
            ('damage_description','Damage Description'),
            ('claim_amount',      'Claim Amount'),
            ('property_value',    'Insured Property Value'),
        ])
        add_consistency(ids['property'], [
            ('claim_within_value', 'Claim amount must not exceed insured property value', 'medium', 'Review property valuation'),
        ])

        # ── TRAVEL ──────────────────────────────────────────────────────────
        add_docs(ids['travel'], [
            ('travel_policy',       'Travel Insurance Policy',              True,  20, 'high',   'Upload your travel insurance policy document'),
            ('passport_copy',       'Passport Copy',                        True,  15, 'high',   'Upload clear copy of passport with visa stamps'),
            ('visa_copy',           'Visa Copy',                            True,  10, 'high',   'Upload visa copy for destination country'),
            ('flight_tickets',      'Flight Tickets and Boarding Passes',   True,  15, 'high',   'Upload all flight tickets and boarding passes'),
            ('hotel_bookings',      'Hotel and Accommodation Bookings',     True,  10, 'medium', 'Upload hotel booking confirmations'),
            ('medical_bills_abroad','Medical Bills Abroad',                 False, 10, 'high',   'Upload all medical bills if claiming medical expenses'),
            ('airline_certificate', 'Airline Delay Certificate',            False,  8, 'medium', 'Get delay certificate from airline for delay claims'),
            ('pir_report',          'PIR Report from Airline',              False, 10, 'high',   'Property Irregularity Report for lost baggage'),
            ('police_report_abroad','Police Report Filed Abroad',           False,  8, 'high',   'Required for theft or loss claims abroad'),
        ])
        add_fields(ids['travel'], [
            ('policy_number',    'Policy Number'),
            ('traveler_name',    'Traveler Name'),
            ('travel_start_date','Travel Start Date'),
            ('travel_end_date',  'Travel End Date'),
            ('destination',      'Destination'),
            ('incident_type',    'Incident Type'),
            ('incident_date',    'Incident Date'),
            ('claim_amount',     'Claim Amount'),
        ])
        add_consistency(ids['travel'], [
            ('travel_end_after_start',  'Travel end date must be after start date',       'high',   'Check your travel dates'),
            ('incident_during_travel',  'Incident must occur during travel period',        'high',   'Incident date must fall between travel start and end dates'),
        ])

        # ── CROP ────────────────────────────────────────────────────────────
        add_docs(ids['crop'], [
            ('land_record',          'Sowing Certificate and Land Record',    True,  20, 'high',   'Upload 7/12 extract or land record with sowing certificate'),
            ('bank_passbook',        'Bank Passbook Linked to Aadhaar',       True,  20, 'high',   'Upload bank passbook first page linked to Aadhaar'),
            ('aadhaar_card',         'Aadhaar Card',                          True,  15, 'high',   'Upload clear copy of Aadhaar card'),
            ('enrollment_receipt',   'Insurance Enrollment Receipt',          True,  15, 'high',   'Upload PMFBY or crop insurance enrollment receipt'),
            ('loss_intimation',      'Crop Loss Intimation Form',             True,  15, 'high',   'Fill and submit crop loss intimation within 72 hours'),
            ('damage_photos',        'Photos and Videos of Crop Damage',      True,  10, 'medium', 'Take clear photos of damaged crops from multiple angles'),
            ('patwari_certificate',  'Patwari Certificate of Loss',           True,  10, 'high',   'Get crop loss certificate from local Patwari'),
            ('meteorological_report','Meteorological Report',                 False,  5, 'medium', 'Weather report from IMD if claiming weather damage'),
        ])
        add_fields(ids['crop'], [
            ('policy_number',    'Policy Number'),
            ('farmer_name',      'Farmer Name'),
            ('land_survey_number','Land Survey Number'),
            ('crop_type',        'Crop Type'),
            ('sowing_date',      'Sowing Date'),
            ('damage_date',      'Damage Date'),
            ('damage_cause',     'Cause of Damage'),
            ('claim_amount',     'Claim Amount'),
        ])
        add_consistency(ids['crop'], [
            ('damage_after_sowing', 'Damage date must be after sowing date', 'high', 'Crop damage cannot occur before sowing'),
        ])

        db.session.commit()
        print('✓ All 6 insurance types seeded with correct document names!')

def add_docs(type_id, docs):
    for name, label, required, weight, severity, suggestion in docs:
        db.session.add(Rule(
            insurance_type_id=type_id, rule_type='document',
            name=name, label=label, is_required=required,
            weight=weight, severity=severity, suggestion=suggestion
        ))

def add_fields(type_id, fields):
    for name, label in fields:
        db.session.add(Rule(
            insurance_type_id=type_id, rule_type='field',
            name=name, label=label, is_required=True,
            weight=0, severity='high', suggestion=f'Please provide {label.lower()}'
        ))

def add_consistency(type_id, rules):
    for name, label, severity, suggestion in rules:
        db.session.add(Rule(
            insurance_type_id=type_id, rule_type='consistency',
            name=name, label=label, is_required=False,
            weight=0, severity=severity, suggestion=suggestion
        ))

if __name__ == '__main__':
    seed()
