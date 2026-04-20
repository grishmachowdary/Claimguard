"""
Approved Network — Insurance-approved hospitals, garages, and service providers.
"""

APPROVED_NETWORK = {
    'health': [
        {'id': 1,  'name': 'Apollo Hospitals',           'city': 'Mumbai',    'state': 'Maharashtra', 'insurers': ['Star Health', 'HDFC ERGO', 'ICICI Lombard', 'Bajaj Allianz'], 'type': 'hospital', 'cashless': True,  'rating': 4.8, 'speciality': 'Multi-specialty'},
        {'id': 2,  'name': 'Fortis Healthcare',          'city': 'Delhi',     'state': 'Delhi',       'insurers': ['Star Health', 'HDFC ERGO', 'Bajaj Allianz'],                  'type': 'hospital', 'cashless': True,  'rating': 4.7, 'speciality': 'Multi-specialty'},
        {'id': 3,  'name': 'Manipal Hospitals',          'city': 'Bangalore', 'state': 'Karnataka',   'insurers': ['Star Health', 'ICICI Lombard', 'Tata AIG'],                   'type': 'hospital', 'cashless': True,  'rating': 4.6, 'speciality': 'Multi-specialty'},
        {'id': 4,  'name': 'Max Healthcare',             'city': 'Delhi',     'state': 'Delhi',       'insurers': ['HDFC ERGO', 'ICICI Lombard', 'Bajaj Allianz'],                'type': 'hospital', 'cashless': True,  'rating': 4.7, 'speciality': 'Cardiac & Neuro'},
        {'id': 5,  'name': 'Narayana Health',            'city': 'Bangalore', 'state': 'Karnataka',   'insurers': ['Star Health', 'HDFC ERGO', 'New India'],                      'type': 'hospital', 'cashless': True,  'rating': 4.5, 'speciality': 'Cardiac'},
        {'id': 6,  'name': 'Kokilaben Hospital',         'city': 'Mumbai',    'state': 'Maharashtra', 'insurers': ['HDFC ERGO', 'ICICI Lombard', 'Bajaj Allianz'],                'type': 'hospital', 'cashless': True,  'rating': 4.8, 'speciality': 'Oncology'},
        {'id': 7,  'name': 'AIIMS Delhi',                'city': 'Delhi',     'state': 'Delhi',       'insurers': ['Star Health', 'HDFC ERGO', 'New India', 'Bajaj Allianz'],     'type': 'hospital', 'cashless': False, 'rating': 4.9, 'speciality': 'All specialities'},
        {'id': 8,  'name': 'Medanta The Medicity',       'city': 'Gurugram',  'state': 'Haryana',     'insurers': ['HDFC ERGO', 'ICICI Lombard', 'Tata AIG'],                     'type': 'hospital', 'cashless': True,  'rating': 4.7, 'speciality': 'Multi-specialty'},
        {'id': 9,  'name': 'Lilavati Hospital',          'city': 'Mumbai',    'state': 'Maharashtra', 'insurers': ['Star Health', 'Bajaj Allianz', 'New India'],                  'type': 'hospital', 'cashless': True,  'rating': 4.6, 'speciality': 'Multi-specialty'},
        {'id': 10, 'name': 'Christian Medical College', 'city': 'Vellore',   'state': 'Tamil Nadu',  'insurers': ['Star Health', 'HDFC ERGO', 'New India'],                      'type': 'hospital', 'cashless': True,  'rating': 4.9, 'speciality': 'All specialities'},
    ],
    'vehicle': [
        {'id': 1,  'name': 'Maruti Suzuki Authorized Service', 'city': 'Mumbai',    'state': 'Maharashtra', 'insurers': ['HDFC ERGO', 'Bajaj Allianz', 'ICICI Lombard'], 'type': 'garage', 'cashless': True,  'rating': 4.5, 'speciality': 'Maruti vehicles'},
        {'id': 2,  'name': 'Hyundai Authorized Workshop',      'city': 'Delhi',     'state': 'Delhi',       'insurers': ['HDFC ERGO', 'Tata AIG', 'Bajaj Allianz'],      'type': 'garage', 'cashless': True,  'rating': 4.4, 'speciality': 'Hyundai vehicles'},
        {'id': 3,  'name': 'Tata Motors Service Center',       'city': 'Pune',      'state': 'Maharashtra', 'insurers': ['Tata AIG', 'HDFC ERGO', 'New India'],          'type': 'garage', 'cashless': True,  'rating': 4.3, 'speciality': 'Tata vehicles'},
        {'id': 4,  'name': 'Honda Cars Service',               'city': 'Bangalore', 'state': 'Karnataka',   'insurers': ['ICICI Lombard', 'Bajaj Allianz', 'Tata AIG'],  'type': 'garage', 'cashless': True,  'rating': 4.5, 'speciality': 'Honda vehicles'},
        {'id': 5,  'name': 'Toyota Authorized Garage',         'city': 'Chennai',   'state': 'Tamil Nadu',  'insurers': ['HDFC ERGO', 'ICICI Lombard', 'New India'],     'type': 'garage', 'cashless': True,  'rating': 4.6, 'speciality': 'Toyota vehicles'},
        {'id': 6,  'name': 'Mahindra Service Center',          'city': 'Mumbai',    'state': 'Maharashtra', 'insurers': ['Bajaj Allianz', 'New India', 'HDFC ERGO'],     'type': 'garage', 'cashless': True,  'rating': 4.3, 'speciality': 'Mahindra vehicles'},
        {'id': 7,  'name': 'Hero MotoCorp Service',            'city': 'Delhi',     'state': 'Delhi',       'insurers': ['Bajaj Allianz', 'ICICI Lombard', 'Tata AIG'],  'type': 'garage', 'cashless': True,  'rating': 4.2, 'speciality': 'Two-wheelers'},
        {'id': 8,  'name': 'Bajaj Auto Service',               'city': 'Pune',      'state': 'Maharashtra', 'insurers': ['Bajaj Allianz', 'HDFC ERGO', 'New India'],     'type': 'garage', 'cashless': True,  'rating': 4.1, 'speciality': 'Two-wheelers'},
    ],
    'property': [
        {'id': 1, 'name': 'Godrej Construction Services', 'city': 'Mumbai',    'state': 'Maharashtra', 'insurers': ['HDFC ERGO', 'New India', 'Bajaj Allianz'], 'type': 'contractor', 'cashless': False, 'rating': 4.5, 'speciality': 'Residential'},
        {'id': 2, 'name': 'L&T Construction',             'city': 'Chennai',   'state': 'Tamil Nadu',  'insurers': ['New India', 'HDFC ERGO', 'ICICI Lombard'], 'type': 'contractor', 'cashless': False, 'rating': 4.7, 'speciality': 'Commercial & Residential'},
        {'id': 3, 'name': 'Shapoorji Pallonji',           'city': 'Mumbai',    'state': 'Maharashtra', 'insurers': ['HDFC ERGO', 'Bajaj Allianz'],              'type': 'contractor', 'cashless': False, 'rating': 4.6, 'speciality': 'Large scale'},
        {'id': 4, 'name': 'DLF Repair Services',          'city': 'Gurugram',  'state': 'Haryana',     'insurers': ['HDFC ERGO', 'New India', 'Bajaj Allianz'], 'type': 'contractor', 'cashless': False, 'rating': 4.4, 'speciality': 'Residential'},
    ],
    'travel': [
        {'id': 1, 'name': 'Apollo Munich Travel Clinic',  'city': 'Mumbai',    'state': 'Maharashtra', 'insurers': ['Tata AIG', 'HDFC ERGO', 'ICICI Lombard'], 'type': 'clinic',    'cashless': True,  'rating': 4.5, 'speciality': 'Travel medicine'},
        {'id': 2, 'name': 'SOS International',            'city': 'Delhi',     'state': 'Delhi',       'insurers': ['Tata AIG', 'ICICI Lombard'],               'type': 'emergency', 'cashless': True,  'rating': 4.8, 'speciality': 'Emergency assistance'},
        {'id': 3, 'name': 'Europ Assistance India',       'city': 'Bangalore', 'state': 'Karnataka',   'insurers': ['HDFC ERGO', 'Bajaj Allianz', 'Tata AIG'],  'type': 'emergency', 'cashless': True,  'rating': 4.6, 'speciality': 'Travel emergency'},
    ],
    'life': [
        {'id': 1, 'name': 'LIC Branch Office',            'city': 'Mumbai',    'state': 'Maharashtra', 'insurers': ['LIC of India'],                            'type': 'office',    'cashless': False, 'rating': 4.2, 'speciality': 'Life claims'},
        {'id': 2, 'name': 'HDFC Life Service Center',     'city': 'Delhi',     'state': 'Delhi',       'insurers': ['HDFC ERGO'],                               'type': 'office',    'cashless': False, 'rating': 4.4, 'speciality': 'Life claims'},
        {'id': 3, 'name': 'Bajaj Allianz Life Office',    'city': 'Pune',      'state': 'Maharashtra', 'insurers': ['Bajaj Allianz'],                           'type': 'office',    'cashless': False, 'rating': 4.3, 'speciality': 'Life claims'},
    ],
    'crop': [
        {'id': 1, 'name': 'AIC District Office',          'city': 'Nagpur',    'state': 'Maharashtra', 'insurers': ['Agriculture Insurance Co.'],               'type': 'office',    'cashless': False, 'rating': 4.0, 'speciality': 'Crop claims'},
        {'id': 2, 'name': 'PMFBY Facilitation Center',    'city': 'Pune',      'state': 'Maharashtra', 'insurers': ['Agriculture Insurance Co.', 'New India'],  'type': 'office',    'cashless': False, 'rating': 4.1, 'speciality': 'PMFBY claims'},
        {'id': 3, 'name': 'Krishi Vigyan Kendra',         'city': 'Nashik',    'state': 'Maharashtra', 'insurers': ['Agriculture Insurance Co.'],               'type': 'office',    'cashless': False, 'rating': 4.2, 'speciality': 'Crop assessment'},
    ],
}

def get_network(insurance_type, city=None, insurer=None):
    providers = APPROVED_NETWORK.get(insurance_type, [])
    if city:
        providers = [p for p in providers if city.lower() in p['city'].lower() or city.lower() in p['state'].lower()]
    if insurer:
        providers = [p for p in providers if any(insurer.lower() in i.lower() for i in p['insurers'])]
    return providers

def get_recommendation(insurance_type, score, city=None):
    """Return network recommendation based on claim risk level."""
    providers = get_network(insurance_type, city)
    if score < 50:
        msg = f'Your claim risk is HIGH. Visiting an approved {_provider_type(insurance_type)} will significantly increase your approval chances.'
    elif score < 80:
        msg = f'Your claim has moderate risk. Consider using an approved {_provider_type(insurance_type)} for faster processing.'
    else:
        msg = f'Your claim looks good. Here are approved {_provider_type(insurance_type)}s for your reference.'
    return {'message': msg, 'providers': providers[:5], 'total': len(providers)}

def _provider_type(insurance_type):
    types = {'health': 'hospital', 'vehicle': 'garage', 'property': 'contractor', 'travel': 'clinic', 'life': 'office', 'crop': 'office'}
    return types.get(insurance_type, 'provider')
