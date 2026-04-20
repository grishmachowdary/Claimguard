import React, { useState, useEffect } from 'react';
import { getInsuranceCompanies, submitToInsurer } from '../api';
import './SubmitModal.css';

function SubmitModal({ claimId, insuranceTypeCode, score, onClose }) {
  const [companies,  setCompanies]  = useState([]);
  const [selected,   setSelected]   = useState(null);
  const [loading,    setLoading]    = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [result,     setResult]     = useState(null);
  const [error,      setError]      = useState('');

  useEffect(() => {
    loadCompanies();
  }, []); // eslint-disable-line

  const loadCompanies = async () => {
    try {
      const res = await getInsuranceCompanies(insuranceTypeCode);
      setCompanies(res.data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async () => {
    if (!selected) { setError('Please select an insurance company'); return; }
    setError('');
    setSubmitting(true);
    try {
      const res = await submitToInsurer(claimId, { company_id: selected.id });
      setResult(res.data);
    } catch (e) {
      setError(e.response?.data?.error || 'Submission failed. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-box submit-modal-box" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Submit to Insurance Company</h2>
          <button className="modal-close" onClick={onClose}>✕</button>
        </div>

        {result ? (
          /* ── Success State ── */
          <div className="submit-success">
            <div className="success-icon">✓</div>
            <h3>Claim Submitted!</h3>
            <p className="success-company">Submitted to <strong>{result.company}</strong></p>

            <div className="result-details">
              <div className="result-row">
                <span>Reference Number</span>
                <span className="result-ref">{result.reference_number}</span>
              </div>
              <div className="result-row">
                <span>Submitted At</span>
                <span>{new Date(result.submitted_at).toLocaleString()}</span>
              </div>
              <div className="result-row">
                <span>Claim Score</span>
                <span style={{ color: '#22c55e' }}>{result.score}/100</span>
              </div>
            </div>

            <div className="next-steps-box">
              <p>📋 <strong>Next Steps:</strong></p>
              <p>{result.next_steps}</p>
            </div>

            <button className="qr-btn qr-btn-primary" onClick={onClose} style={{ width: '100%', marginTop: '1rem' }}>
              Done
            </button>
          </div>
        ) : (
          <>
            {/* Score check */}
            <div className={`score-check ${score >= 80 ? 'score-ok' : score >= 50 ? 'score-warn' : 'score-bad'}`}>
              <span className="score-check-num">{score}/100</span>
              <div>
                <p className="score-check-label">
                  {score >= 80 ? '✓ Ready to Submit' : score >= 50 ? '⚠ Submittable with issues' : '✕ Score too low to submit'}
                </p>
                <p className="score-check-msg">
                  {score >= 80
                    ? 'Your claim is well-prepared. Select a company below.'
                    : score >= 50
                    ? 'You can submit but some issues may delay processing.'
                    : 'Please fix all critical issues before submitting.'}
                </p>
              </div>
            </div>

            {score >= 50 && (
              <>
                <p className="companies-label">Select Insurance Company</p>

                {loading ? (
                  <div className="modal-loading"><div className="spinner" /></div>
                ) : (
                  <div className="companies-list">
                    {companies.map(company => (
                      <div
                        key={company.id}
                        className={`company-card ${selected?.id === company.id ? 'company-selected' : ''}`}
                        onClick={() => { setSelected(company); setError(''); }}
                      >
                        <span className="company-logo">{company.logo}</span>
                        <div className="company-info">
                          <p className="company-name">{company.name}</p>
                          <p className="company-types">{company.types.join(', ')}</p>
                        </div>
                        {selected?.id === company.id && (
                          <span className="company-check">✓</span>
                        )}
                      </div>
                    ))}
                  </div>
                )}

                {error && <p className="submit-error-msg">⚠ {error}</p>}

                <div className="submit-disclaimer">
                  <p>By submitting, you confirm that all information provided is accurate and complete. ClaimGuard will forward your claim details to the selected insurer.</p>
                </div>

                <div className="submit-actions">
                  <button className="qr-btn qr-btn-secondary" onClick={onClose}>Cancel</button>
                  <button
                    className="qr-btn qr-btn-primary"
                    onClick={handleSubmit}
                    disabled={submitting || !selected}
                  >
                    {submitting ? 'Submitting...' : `Submit to ${selected?.name || 'Insurer'} →`}
                  </button>
                </div>
              </>
            )}

            {score < 50 && (
              <button className="qr-btn qr-btn-secondary" onClick={onClose} style={{ width: '100%', marginTop: '1rem' }}>
                Go Back and Fix Issues
              </button>
            )}
          </>
        )}
      </div>
    </div>
  );
}

export default SubmitModal;
