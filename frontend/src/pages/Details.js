import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import { getRules, updateClaim, validateClaim } from '../api';
import StepProgress from '../components/StepProgress';
import './Details.css';

// Field type detection
const TEXTAREA_FIELDS = ['diagnosis', 'incident_description', 'damage_description', 'damage_cause', 'cause_of_death'];
const NUMBER_FIELDS   = ['claim_amount', 'policy_coverage', 'sum_assured', 'property_value'];
const DATE_FIELDS     = ['admission_date', 'discharge_date', 'incident_date', 'date_of_death',
                         'travel_start_date', 'travel_end_date', 'sowing_date', 'damage_date'];

// Live validation rules
const DATE_PAIRS = [
  { before: 'admission_date',   after: 'discharge_date',   msg: 'Discharge date must be after admission date' },
  { before: 'travel_start_date',after: 'travel_end_date',  msg: 'Travel end date must be after start date' },
  { before: 'sowing_date',      after: 'damage_date',      msg: 'Damage date must be after sowing date' },
];
const AMOUNT_PAIRS = [
  { amount: 'claim_amount', limit: 'policy_coverage', label: 'policy coverage' },
  { amount: 'claim_amount', limit: 'sum_assured',     label: 'sum assured' },
  { amount: 'claim_amount', limit: 'property_value',  label: 'insured property value' },
];

function Details() {
  const { claimId } = useParams();
  const navigate    = useNavigate();
  const location    = useLocation();
  const insuranceType = location.state?.insuranceType || localStorage.getItem('insurance_type') || 'health';

  const [fields,     setFields]     = useState([]);
  const [formData,   setFormData]   = useState(() => {
    // Restore draft from localStorage
    const draft = localStorage.getItem(`draft_${claimId}`);
    return draft ? JSON.parse(draft) : {};
  });
  const [errors,     setErrors]     = useState({});
  const [touched,    setTouched]    = useState({});
  const [loading,    setLoading]    = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [savedDraft, setSavedDraft] = useState(false);

  useEffect(() => { loadFields(); }, [insuranceType]); // eslint-disable-line

  const loadFields = async () => {
    try {
      const res = await getRules(insuranceType);
      setFields(res.data.fields || []);
      setLoading(false);
    } catch (e) {
      console.error(e);
      setLoading(false);
    }
  };

  const validate = (name, value, allData) => {
    const errs = { ...errors };

    // Required check
    if (!value || String(value).trim() === '') {
      errs[name] = 'This field is required';
    } else {
      delete errs[name];
    }

    // Date pair checks
    DATE_PAIRS.forEach(({ before, after, msg }) => {
      if (name === before || name === after) {
        const b = name === before ? value : allData[before];
        const a = name === after  ? value : allData[after];
        if (b && a) {
          if (new Date(a) <= new Date(b)) errs[after] = msg;
          else { delete errs[before]; delete errs[after]; }
        }
      }
    });

    // Amount vs limit checks
    AMOUNT_PAIRS.forEach(({ amount, limit, label }) => {
      if (name === amount || name === limit) {
        const amt = parseFloat(name === amount ? value : allData[amount]);
        const lim = parseFloat(name === limit  ? value : allData[limit]);
        if (amt && lim) {
          if (amt > lim) errs[amount] = `Claim amount cannot exceed ${label}`;
          else delete errs[amount];
        }
      }
    });

    return errs;
  };

  const handleChange = (name, value) => {
    const updated = { ...formData, [name]: value };
    setFormData(updated);
    // Auto-save draft
    localStorage.setItem(`draft_${claimId}`, JSON.stringify(updated));
    setSavedDraft(true);
    setTimeout(() => setSavedDraft(false), 2000);
    if (touched[name]) setErrors(validate(name, value, updated));
  };

  const handleBlur = (name) => {
    setTouched(prev => ({ ...prev, [name]: true }));
    setErrors(validate(name, formData[name] || '', formData));
  };

  const handleSubmit = async () => {
    // Touch all fields
    const allTouched = {};
    fields.forEach(f => allTouched[f.name] = true);
    setTouched(allTouched);

    // Validate all fields at once
    let allErrors = {};
    fields.forEach(f => {
      const val = formData[f.name] || '';
      if (!val || String(val).trim() === '') {
        allErrors[f.name] = 'This field is required';
      }
    });

    // Also run cross-field checks
    DATE_PAIRS.forEach(({ before, after, msg }) => {
      const b = formData[before];
      const a = formData[after];
      if (b && a && new Date(a) <= new Date(b)) {
        allErrors[after] = msg;
      }
    });
    AMOUNT_PAIRS.forEach(({ amount, limit, label }) => {
      const amt = parseFloat(formData[amount]);
      const lim = parseFloat(formData[limit]);
      if (amt && lim && amt > lim) {
        allErrors[amount] = `Claim amount cannot exceed ${label}`;
      }
    });

    setErrors(allErrors);
    if (Object.keys(allErrors).length > 0) return;

    setSubmitting(true);
    try {
      await updateClaim(claimId, { form_data: formData });
      await validateClaim(claimId);
      localStorage.removeItem(`draft_${claimId}`); // clear draft on success
      navigate(`/report/${claimId}`);
    } catch (e) {
      console.error('Submit error:', e);
      setSubmitting(false);
    }
  };

  const getType = (name) => {
    if (TEXTAREA_FIELDS.includes(name)) return 'textarea';
    if (DATE_FIELDS.includes(name))     return 'date';
    if (NUMBER_FIELDS.includes(name))   return 'number';
    return 'text';
  };

  const filledCount = fields.filter(f => formData[f.name] && String(formData[f.name]).trim()).length;
  const progress    = fields.length > 0 ? (filledCount / fields.length) * 100 : 0;
  const hasErrors   = Object.keys(errors).length > 0;

  const icons = { health: '❤️', vehicle: '🚗', life: '🛡️', property: '🏠', travel: '✈️', crop: '🌾' };

  if (loading) return (
    <div className="details-loading">
      <div className="spinner" />
      <p>Loading form...</p>
    </div>
  );

  return (
    <div className="details-page">
      <div className="details-container">

        {/* Header */}
        <div className="details-header">
          <button className="back-btn" onClick={() => navigate(-1)}>← Back</button>
          <div className="details-title">
            <span>{icons[insuranceType] || '📋'}</span>
            <div>
              <h1>Claim Details</h1>
              <p>{insuranceType.charAt(0).toUpperCase() + insuranceType.slice(1)} Insurance</p>
            </div>
            {savedDraft && <span className="draft-saved">✓ Draft saved</span>}
          </div>
        </div>

        <StepProgress current={2} />

        {/* Progress */}
        <div className="form-progress">
          <div className="form-progress-info">
            <span>{filledCount} of {fields.length} fields filled</span>
            <span>{Math.round(progress)}%</span>
          </div>
          <div className="form-progress-track">
            <div className="form-progress-fill" style={{ width: `${progress}%` }} />
          </div>
        </div>

        {/* Form */}
        <div className="details-form">
          {fields.map((field) => {
            const type    = getType(field.name);
            const hasErr  = touched[field.name] && errors[field.name];
            const isFilled = formData[field.name] && String(formData[field.name]).trim();

            return (
              <div key={field.name} className={`field-group ${hasErr ? 'field-error' : isFilled ? 'field-ok' : ''}`}>
                <label className="field-label">
                  {field.label}
                  <span className="field-required">*</span>
                  {isFilled && !hasErr && <span className="field-check">✓</span>}
                </label>

                {type === 'textarea' ? (
                  <textarea
                    className={`field-input ${hasErr ? 'input-error' : isFilled ? 'input-ok' : ''}`}
                    rows={3}
                    value={formData[field.name] || ''}
                    placeholder={`Enter ${field.label.toLowerCase()}`}
                    onChange={e => handleChange(field.name, e.target.value)}
                    onBlur={() => handleBlur(field.name)}
                  />
                ) : type === 'date' ? (
                  <input
                    type="date"
                    className={`field-input ${hasErr ? 'input-error' : isFilled ? 'input-ok' : ''}`}
                    value={formData[field.name] || ''}
                    onChange={e => handleChange(field.name, e.target.value)}
                    onBlur={() => handleBlur(field.name)}
                  />
                ) : type === 'number' ? (
                  <input
                    type="number"
                    className={`field-input ${hasErr ? 'input-error' : isFilled ? 'input-ok' : ''}`}
                    value={formData[field.name] || ''}
                    placeholder={`Enter ${field.label.toLowerCase()}`}
                    min="0"
                    step="0.01"
                    onChange={e => handleChange(field.name, e.target.value)}
                    onBlur={() => handleBlur(field.name)}
                  />
                ) : (
                  <input
                    type="text"
                    className={`field-input ${hasErr ? 'input-error' : isFilled ? 'input-ok' : ''}`}
                    value={formData[field.name] || ''}
                    placeholder={`Enter ${field.label.toLowerCase()}`}
                    onChange={e => handleChange(field.name, e.target.value)}
                    onBlur={() => handleBlur(field.name)}
                  />
                )}

                {hasErr && (
                  <p className="field-error-msg">⚠ {errors[field.name]}</p>
                )}
              </div>
            );
          })}
        </div>

        {/* Submit */}
        <div className="details-footer">
          {hasErrors && Object.keys(touched).length > 0 && (
            <p className="submit-error">Please fix the errors above before continuing</p>
          )}
          <div className="details-actions">
            <button className="btn-back" onClick={() => navigate(-1)}>Back</button>
            <button
              className={`btn-validate ${submitting ? 'btn-loading' : ''}`}
              onClick={handleSubmit}
              disabled={submitting}
            >
              {submitting ? 'Validating...' : 'Save & Validate Claim →'}
            </button>
          </div>
        </div>

      </div>
    </div>
  );
}

export default Details;
