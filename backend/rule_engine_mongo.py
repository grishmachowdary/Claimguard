from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime

client = MongoClient('mongodb://localhost:27017/')
db = client['claimguard']

def validate_claim(claim, claim_id):
    violations_list = []
    
    # Get all rules for this insurance type
    type_rules = list(db.rules.find({'insurance_type_id': claim['insurance_type_id']}))
    
    # Separate rules by type
    doc_rules = [r for r in type_rules if r['rule_type'] == 'document']
    field_rules = [r for r in type_rules if r['rule_type'] == 'field']
    consistency_rules = [r for r in type_rules if r['rule_type'] == 'consistency']
    
    # Get data
    uploaded_docs = claim.get('uploaded_docs', [])
    form_data = claim.get('form_data', {})
    
    # Calculate document score
    doc_score = 0
    max_doc_score = sum(r['weight'] for r in doc_rules if r['is_required'])
    
    for rule in doc_rules:
        if rule['is_required']:
            if rule['name'] in uploaded_docs:
                doc_score += rule['weight']
            else:
                violations_list.append({
                    'rule_name': rule['name'],
                    'message': f"Missing required document: {rule['label']}",
                    'suggestion': rule['suggestion'],
                    'severity': rule['severity']
                })
    
    document_score = (doc_score / max_doc_score * 40) if max_doc_score > 0 else 0
    
    # Calculate field score
    filled_fields = 0
    total_fields = len(field_rules)
    
    for rule in field_rules:
        if form_data.get(rule['name']):
            filled_fields += 1
        else:
            violations_list.append({
                'rule_name': rule['name'],
                'message': f"Missing required field: {rule['label']}",
                'suggestion': rule['suggestion'],
                'severity': rule['severity']
            })
    
    field_score = (filled_fields / total_fields * 35) if total_fields > 0 else 0
    
    # Calculate consistency score
    consistency_score = 25
    
    # Get insurance type
    ins_type = db.insurance_types.find_one({'_id': ObjectId(claim['insurance_type_id'])})
    
    if ins_type:
        if ins_type['code'] == 'health':
            consistency_score = check_health_consistency(form_data, consistency_rules, violations_list, consistency_score)
        elif ins_type['code'] == 'vehicle':
            consistency_score = check_vehicle_consistency(form_data, consistency_rules, violations_list, consistency_score)
        elif ins_type['code'] == 'life':
            consistency_score = check_life_consistency(form_data, consistency_rules, violations_list, consistency_score)
        elif ins_type['code'] == 'property':
            consistency_score = check_property_consistency(form_data, consistency_rules, violations_list, consistency_score)
        elif ins_type['code'] == 'travel':
            consistency_score = check_travel_consistency(form_data, consistency_rules, violations_list, consistency_score)
        elif ins_type['code'] == 'crop':
            consistency_score = check_crop_consistency(form_data, consistency_rules, violations_list, consistency_score)
    
    consistency_score = max(0, consistency_score)
    
    # Calculate final score
    final_score = int(document_score + field_score + consistency_score)
    final_score = max(0, min(100, final_score))
    
    # Determine readiness label
    if final_score >= 80:
        readiness_label = 'Ready to Submit'
    elif final_score >= 50:
        readiness_label = 'Needs Attention'
    else:
        readiness_label = 'Incomplete'
    
    # Update claim
    db.claims.update_one(
        {'_id': ObjectId(claim_id)},
        {'$set': {
            'readiness_score': final_score,
            'score_breakdown': {
                'document': round(document_score, 1),
                'field': round(field_score, 1),
                'consistency': round(consistency_score, 1)
            },
            'readiness_label': readiness_label
        }}
    )
    
    # Clear old violations
    db.violations.delete_many({'claim_id': claim_id})
    
    # Save new violations
    for v in violations_list:
        v['claim_id'] = claim_id
        db.violations.insert_one(v)
    
    return {
        'score': final_score,
        'breakdown': {
            'document': round(document_score, 1),
            'field': round(field_score, 1),
            'consistency': round(consistency_score, 1)
        },
        'readiness_label': readiness_label,
        'violations': violations_list
    }

def check_health_consistency(form_data, rules, violations, score):
    admission_date = form_data.get('admission_date')
    discharge_date = form_data.get('discharge_date')
    claim_amount = form_data.get('claim_amount')
    policy_coverage = form_data.get('policy_coverage')
    
    if admission_date and discharge_date:
        try:
            adm = datetime.strptime(admission_date, '%Y-%m-%d')
            dis = datetime.strptime(discharge_date, '%Y-%m-%d')
            if dis <= adm:
                rule = next((r for r in rules if r['name'] == 'discharge_after_admission'), None)
                if rule:
                    violations.append({
                        'rule_name': rule['name'],
                        'message': rule['label'],
                        'suggestion': rule['suggestion'],
                        'severity': rule['severity']
                    })
                    score -= 15
        except:
            pass
    
    if claim_amount and policy_coverage:
        try:
            if float(claim_amount) > float(policy_coverage):
                rule = next((r for r in rules if r['name'] == 'claim_within_coverage'), None)
                if rule:
                    violations.append({
                        'rule_name': rule['name'],
                        'message': rule['label'],
                        'suggestion': rule['suggestion'],
                        'severity': rule['severity']
                    })
                    score -= 10
        except:
            pass
    
    return score

def check_vehicle_consistency(form_data, rules, violations, score):
    claim_amount = form_data.get('claim_amount')
    policy_coverage = form_data.get('policy_coverage')
    
    if claim_amount and policy_coverage:
        try:
            if float(claim_amount) > float(policy_coverage):
                rule = next((r for r in rules if r['name'] == 'claim_within_coverage'), None)
                if rule:
                    violations.append({
                        'rule_name': rule['name'],
                        'message': rule['label'],
                        'suggestion': rule['suggestion'],
                        'severity': rule['severity']
                    })
                    score -= 10
        except:
            pass
    
    return score

def check_life_consistency(form_data, rules, violations, score):
    claim_amount = form_data.get('claim_amount')
    sum_assured = form_data.get('sum_assured')
    
    if claim_amount and sum_assured:
        try:
            if abs(float(claim_amount) - float(sum_assured)) > 1000:
                rule = next((r for r in rules if r['name'] == 'claim_matches_sum_assured'), None)
                if rule:
                    violations.append({
                        'rule_name': rule['name'],
                        'message': rule['label'],
                        'suggestion': rule['suggestion'],
                        'severity': rule['severity']
                    })
                    score -= 10
        except:
            pass
    
    return score

def check_property_consistency(form_data, rules, violations, score):
    claim_amount = form_data.get('claim_amount')
    property_value = form_data.get('property_value')
    
    if claim_amount and property_value:
        try:
            if float(claim_amount) > float(property_value):
                rule = next((r for r in rules if r['name'] == 'claim_within_value'), None)
                if rule:
                    violations.append({
                        'rule_name': rule['name'],
                        'message': rule['label'],
                        'suggestion': rule['suggestion'],
                        'severity': rule['severity']
                    })
                    score -= 10
        except:
            pass
    
    return score

def check_travel_consistency(form_data, rules, violations, score):
    travel_start = form_data.get('travel_start_date')
    travel_end = form_data.get('travel_end_date')
    incident_date = form_data.get('incident_date')
    
    if travel_start and travel_end:
        try:
            start = datetime.strptime(travel_start, '%Y-%m-%d')
            end = datetime.strptime(travel_end, '%Y-%m-%d')
            if end <= start:
                rule = next((r for r in rules if r['name'] == 'travel_end_after_start'), None)
                if rule:
                    violations.append({
                        'rule_name': rule['name'],
                        'message': rule['label'],
                        'suggestion': rule['suggestion'],
                        'severity': rule['severity']
                    })
                    score -= 15
        except:
            pass
    
    if travel_start and travel_end and incident_date:
        try:
            start = datetime.strptime(travel_start, '%Y-%m-%d')
            end = datetime.strptime(travel_end, '%Y-%m-%d')
            incident = datetime.strptime(incident_date, '%Y-%m-%d')
            if incident < start or incident > end:
                rule = next((r for r in rules if r['name'] == 'incident_during_travel'), None)
                if rule:
                    violations.append({
                        'rule_name': rule['name'],
                        'message': rule['label'],
                        'suggestion': rule['suggestion'],
                        'severity': rule['severity']
                    })
                    score -= 15
        except:
            pass
    
    return score

def check_crop_consistency(form_data, rules, violations, score):
    sowing_date = form_data.get('sowing_date')
    damage_date = form_data.get('damage_date')
    
    if sowing_date and damage_date:
        try:
            sow = datetime.strptime(sowing_date, '%Y-%m-%d')
            damage = datetime.strptime(damage_date, '%Y-%m-%d')
            if damage <= sow:
                rule = next((r for r in rules if r['name'] == 'damage_after_sowing'), None)
                if rule:
                    violations.append({
                        'rule_name': rule['name'],
                        'message': rule['label'],
                        'suggestion': rule['suggestion'],
                        'severity': rule['severity']
                    })
                    score -= 15
        except:
            pass
    
    return score
