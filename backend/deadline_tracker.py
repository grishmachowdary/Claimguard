"""
Claim Deadline Tracker
Calculates submission deadlines based on insurance type and incident date.
Most Indian insurers require claim submission within 30 days of incident/discharge.
"""
from datetime import datetime, timedelta

# Deadline rules per insurance type (days from incident/discharge)
DEADLINE_RULES = {
    'health':   {'days': 30,  'from_field': 'discharge_date',  'label': 'hospital discharge'},
    'vehicle':  {'days': 30,  'from_field': 'incident_date',   'label': 'incident'},
    'life':     {'days': 90,  'from_field': 'date_of_death',   'label': 'date of death'},
    'property': {'days': 30,  'from_field': 'incident_date',   'label': 'incident'},
    'travel':   {'days': 30,  'from_field': 'incident_date',   'label': 'incident'},
    'crop':     {'days': 72,  'from_field': 'damage_date',     'label': 'crop damage', 'unit': 'hours'},
}

def calculate_deadline(insurance_type_code, form_data):
    """Calculate submission deadline and days remaining."""
    rule = DEADLINE_RULES.get(insurance_type_code)
    if not rule:
        return None

    date_str = form_data.get(rule['from_field'])
    if not date_str:
        return None

    try:
        incident_date = datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        return None

    unit = rule.get('unit', 'days')
    if unit == 'hours':
        deadline = incident_date + timedelta(hours=rule['days'])
        total_window = rule['days']
        unit_label = 'hours'
    else:
        deadline = incident_date + timedelta(days=rule['days'])
        total_window = rule['days']
        unit_label = 'days'

    now = datetime.now()
    remaining = deadline - now

    if unit == 'hours':
        remaining_val = max(0, int(remaining.total_seconds() / 3600))
    else:
        remaining_val = max(0, remaining.days)

    elapsed = now - incident_date
    elapsed_days = elapsed.days

    # Progress percentage (how much of the window has been used)
    if unit == 'hours':
        elapsed_hours = elapsed.total_seconds() / 3600
        progress = min(100, (elapsed_hours / total_window) * 100)
    else:
        progress = min(100, (elapsed_days / total_window) * 100)

    # Urgency level
    if remaining_val <= 0:
        urgency = 'expired'
        urgency_color = '#ef4444'
        urgency_msg = 'Deadline has passed. Contact your insurer immediately.'
    elif (unit == 'hours' and remaining_val <= 12) or (unit == 'days' and remaining_val <= 3):
        urgency = 'critical'
        urgency_color = '#ef4444'
        urgency_msg = f'Only {remaining_val} {unit_label} left! Submit immediately.'
    elif (unit == 'hours' and remaining_val <= 24) or (unit == 'days' and remaining_val <= 7):
        urgency = 'warning'
        urgency_color = '#f59e0b'
        urgency_msg = f'{remaining_val} {unit_label} remaining. Submit soon.'
    else:
        urgency = 'ok'
        urgency_color = '#22c55e'
        urgency_msg = f'You have {remaining_val} {unit_label} to submit.'

    return {
        'incident_date':   date_str,
        'deadline':        deadline.strftime('%Y-%m-%d'),
        'deadline_display': deadline.strftime('%d %b %Y'),
        'remaining':       remaining_val,
        'unit':            unit_label,
        'total_window':    total_window,
        'progress':        round(progress, 1),
        'urgency':         urgency,
        'urgency_color':   urgency_color,
        'urgency_msg':     urgency_msg,
        'from_label':      rule['label'],
        'is_expired':      remaining_val <= 0,
    }
