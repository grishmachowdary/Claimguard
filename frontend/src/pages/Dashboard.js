import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getClaims } from '../api';
import { useAuth } from '../context/AuthContext';
import './Dashboard.css';

function Dashboard() {
  const [claims,  setClaims]  = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();
  const { user }  = useAuth();

  useEffect(() => { loadClaims(); }, []);

  const loadClaims = async () => {
    try {
      const res = await getClaims();
      setClaims(res.data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const scoreColor = (s) => s >= 80 ? '#22c55e' : s >= 50 ? '#f59e0b' : '#ef4444';
  const scoreBg    = (s) => s >= 80 ? 'rgba(34,197,94,0.1)' : s >= 50 ? 'rgba(245,158,11,0.1)' : 'rgba(239,68,68,0.1)';
  const formatDate = (d) => d ? new Date(d).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' }) : '—';
  const icons = { 'Health Insurance': '❤️', 'Vehicle Insurance': '🚗', 'Life Insurance': '🛡️', 'Property Insurance': '🏠', 'Travel Insurance': '✈️', 'Crop Insurance': '🌾' };

  const getStatusLabel = (status) => {
    const labels = {
      draft: 'Draft', documents: 'Docs Uploaded', details: 'Details Filled',
      incomplete: 'Incomplete', needs_attention: 'Needs Attention',
      ready: 'Ready to Submit', submitted: 'Submitted',
      under_review: 'Under Review', approved: 'Approved', rejected: 'Rejected'
    };
    return labels[status] || 'Draft';
  };

  if (loading) return (
    <div className="dash-loading">
      <div className="spinner" /><p>Loading claims...</p>
    </div>
  );

  return (
    <div className="dashboard-page">
      <div className="dash-container">

        <div className="dash-header">
          <div>
            <h1>My Claims</h1>
            <p>Welcome back, {user?.full_name} — {claims.length} claim{claims.length !== 1 ? 's' : ''} found</p>
          </div>
          <button className="new-claim-btn" onClick={() => navigate('/')}>+ New Claim</button>
        </div>

        {claims.length > 0 && (
          <div className="dash-stats">
            {[
              { num: claims.length, label: 'Total Claims', color: '#e2e8f0' },
              { num: claims.filter(c => c.readiness_score >= 80).length, label: 'Ready to Submit', color: '#22c55e' },
              { num: claims.filter(c => c.readiness_score >= 50 && c.readiness_score < 80).length, label: 'Needs Attention', color: '#f59e0b' },
              { num: claims.filter(c => !c.readiness_score || c.readiness_score < 50).length, label: 'Incomplete', color: '#ef4444' },
            ].map(({ num, label, color }) => (
              <div key={label} className="stat-card">
                <span className="stat-num" style={{ color }}>{num}</span>
                <span className="stat-label">{label}</span>
              </div>
            ))}
          </div>
        )}

        {claims.length === 0 ? (
          <div className="dash-empty">
            <div className="empty-icon">📋</div>
            <h3>No claims yet</h3>
            <p>Start your first insurance claim validation</p>
            <button className="new-claim-btn" onClick={() => navigate('/')}>+ Start New Claim</button>
          </div>
        ) : (
          <div className="claims-grid">
            {claims.map((claim) => {
              const score = claim.readiness_score || 0;
              return (
                <div key={claim.id} className="claim-card" onClick={() => navigate(`/report/${claim.id}`)}>
                  <div className="claim-top">
                    <div className="claim-type">
                      <span className="claim-icon">{icons[claim.insurance_type_name] || '📋'}</span>
                      <div>
                        <p className="claim-type-name">{claim.insurance_type_name}</p>
                        <p className="claim-id">Claim #{claim.id}</p>
                      </div>
                    </div>
                    <div className="claim-score-badge" style={{ color: scoreColor(score), backgroundColor: scoreBg(score) }}>
                      {score}
                    </div>
                  </div>
                  {claim.primary_field && claim.primary_field !== 'Draft' && (
                    <p className="claim-policy">{claim.primary_field}</p>
                  )}
                  <div className="claim-bottom">
                    <span className="claim-label" style={{ color: scoreColor(score), backgroundColor: scoreBg(score) }}>
                      {claim.readiness_label || 'Not Validated'}
                    </span>
                    <span className="claim-date">{formatDate(claim.created_at)}</span>
                  </div>
                  <div className="claim-status-mini">
                    <span className={`mini-status-dot dot-${claim.status || 'draft'}`} />
                    <span className="mini-status-text">{getStatusLabel(claim.status)}</span>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}

export default Dashboard;
