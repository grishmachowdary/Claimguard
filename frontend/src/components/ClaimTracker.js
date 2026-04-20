import React, { useState, useEffect } from 'react';
import { getClaimStatus } from '../api';
import './ClaimTracker.css';

function ClaimTracker({ claimId }) {
  const [data,    setData]    = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    load();
  }, [claimId]); // eslint-disable-line

  const load = async () => {
    try {
      const res = await getClaimStatus(claimId);
      setData(res.data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (iso) => {
    if (!iso) return null;
    return new Date(iso).toLocaleString('en-IN', {
      day: '2-digit', month: 'short', year: 'numeric',
      hour: '2-digit', minute: '2-digit'
    });
  };

  if (loading) return <div className="tracker-loading"><div className="spinner" /></div>;
  if (!data)   return null;

  const { timeline, current_status } = data;

  return (
    <div className="claim-tracker">
      <div className="tracker-header">
        <h3>📊 Claim Status Tracker</h3>
        <span className={`current-status-pill status-pill-${current_status}`}>
          {timeline.find(t => t.key === current_status)?.label || current_status}
        </span>
      </div>

      <div className="tracker-timeline">
        {timeline.map((step, index) => {
          const isLast = index === timeline.length - 1;
          return (
            <div key={step.key} className={`tracker-step ${step.done ? 'step-done' : ''} ${step.current ? 'step-current' : ''} ${step.key === 'incomplete' || step.key === 'rejected' ? 'step-failed' : ''}`}>
              {/* Connector line */}
              {!isLast && (
                <div className={`step-line ${step.done ? 'line-done' : ''}`} />
              )}

              {/* Icon */}
              <div className={`step-icon-wrap ${step.done ? 'icon-done' : ''} ${step.current ? 'icon-current' : ''} ${step.key === 'incomplete' || step.key === 'rejected' ? 'icon-failed' : ''}`}>
                <span className="step-icon">{step.icon}</span>
              </div>

              {/* Content */}
              <div className="step-content">
                <div className="step-label-row">
                  <span className="step-label">{step.label}</span>
                  {step.current && <span className="step-now-badge">Current</span>}
                </div>
                <p className="step-desc">{step.desc}</p>
                {step.ts && (
                  <p className="step-time">🕐 {formatDate(step.ts)}</p>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* What happens next */}
      <div className="tracker-next">
        {current_status === 'draft' && (
          <p>👉 <strong>Next:</strong> Upload all required documents to proceed</p>
        )}
        {current_status === 'documents' && (
          <p>👉 <strong>Next:</strong> Fill in your claim details and run validation</p>
        )}
        {current_status === 'incomplete' && (
          <p>👉 <strong>Action needed:</strong> Fix all critical issues and re-validate your claim</p>
        )}
        {current_status === 'needs_attention' && (
          <p>👉 <strong>Recommended:</strong> Review and fix issues, then submit to insurer</p>
        )}
        {current_status === 'ready' && (
          <p>👉 <strong>Next:</strong> Click "Submit to Insurer" to send your claim for processing</p>
        )}
        {current_status === 'submitted' && (
          <p>👉 <strong>Waiting:</strong> Your claim is with the insurer. Expect a response in 3–5 business days</p>
        )}
        {current_status === 'under_review' && (
          <p>👉 <strong>In progress:</strong> The insurer is reviewing your documents. Stay available for queries</p>
        )}
        {current_status === 'approved' && (
          <p>🎉 <strong>Congratulations!</strong> Your claim has been approved. Settlement will be processed shortly</p>
        )}
        {current_status === 'rejected' && (
          <p>❌ <strong>Rejected:</strong> Contact your insurer for the reason. You may appeal within 30 days</p>
        )}
      </div>
    </div>
  );
}

export default ClaimTracker;
