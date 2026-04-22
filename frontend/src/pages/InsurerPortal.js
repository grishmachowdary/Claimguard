import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import api from '../api';
import './InsurerPortal.css';
import '../pages/Portal.css';

function InsurerPortal() {
  const { user } = useAuth();
  const navigate = useNavigate();

  const [stats,    setStats]    = useState(null);
  const [claims,   setClaims]   = useState([]);
  const [total,    setTotal]    = useState(0);
  const [pages,    setPages]    = useState(1);
  const [page,     setPage]     = useState(1);
  const [filter,   setFilter]   = useState('');
  const [selected, setSelected] = useState(null);
  const [notes,    setNotes]    = useState('');
  const [acting,   setActing]   = useState(false);
  const [loading,  setLoading]  = useState(true);
  const [msg,      setMsg]      = useState('');

  useEffect(() => {
    if (user?.role !== 'insurer') { navigate('/'); return; }
    loadStats();
  }, []); // eslint-disable-line

  useEffect(() => { loadClaims(); }, [page, filter]); // eslint-disable-line

  const loadStats = async () => {
    try {
      const res = await api.get('/insurer/stats');
      setStats(res.data);
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  };

  const loadClaims = async () => {
    try {
      const res = await api.get(`/insurer/claims?page=${page}&status=${filter}`);
      setClaims(res.data.claims || []);
      setTotal(res.data.total || 0);
      setPages(res.data.pages || 1);
    } catch (e) { console.error(e); }
  };

  const handleAction = async (action) => {
    if (!selected) return;
    setActing(true);
    setMsg('');
    try {
      const res = await api.put(`/insurer/claims/${selected.id}/review`, { action, notes });
      setMsg(`✓ Claim #${selected.id} ${action}d successfully`);
      setSelected(prev => ({ ...prev, status: res.data.new_status, insurer_notes: notes }));
      loadClaims();
      loadStats();
    } catch (e) {
      setMsg('⚠ ' + (e.response?.data?.error || 'Action failed'));
    } finally {
      setActing(false);
    }
  };

  const scoreColor = (s) => !s ? '#475569' : s >= 80 ? '#22c55e' : s >= 50 ? '#f59e0b' : '#ef4444';
  const formatDate = (d) => d ? new Date(d).toLocaleDateString('en-IN', { day:'2-digit', month:'short', year:'numeric' }) : '—';

  const STATUS_FILTERS = [
    { val: '',             label: 'All Submitted' },
    { val: 'submitted',    label: 'New' },
    { val: 'under_review', label: 'Under Review' },
    { val: 'approved',     label: 'Approved' },
    { val: 'rejected',     label: 'Rejected' },
  ];

  if (loading) return <div className="portal-loading"><div className="spinner" /><p>Loading insurer portal...</p></div>;

  return (
    <div className="portal-page">
      <div className="portal-container">

        {/* Header */}
        <div className="portal-header">
          <div>
            <div className="portal-badge insurer-badge">🏛️ Insurer Portal</div>
            <h1>Claims Review Portal</h1>
            <p>{user?.company || user?.full_name} — review and process submitted claims</p>
          </div>
          <button className="portal-back-btn" onClick={() => navigate('/')}>← Back to App</button>
        </div>

        {/* Stats */}
        {stats && (
          <div className="portal-stats">
            {[
              { label: 'Total Received',  val: stats.total_received,  color: '#3b82f6' },
              { label: 'Pending Review',  val: stats.pending_review,  color: '#f59e0b' },
              { label: 'Approved',        val: stats.approved,        color: '#22c55e' },
              { label: 'Rejected',        val: stats.rejected,        color: '#ef4444' },
              { label: 'Approval Rate',   val: `${stats.approval_rate}%`, color: '#22c55e' },
              { label: 'Avg Claim Score', val: stats.avg_claim_score, color: '#06b6d4' },
            ].map(({ label, val, color }) => (
              <div key={label} className="portal-stat-card">
                <span className="pstat-val" style={{ color }}>{val}</span>
                <span className="pstat-label">{label}</span>
              </div>
            ))}
          </div>
        )}

        <div className="insurer-layout">

          {/* Left: Claims list */}
          <div className="claims-panel">
            {/* Filter tabs */}
            <div className="filter-tabs">
              {STATUS_FILTERS.map(f => (
                <button key={f.val}
                  className={`ftab ${filter === f.val ? 'ftab-active' : ''}`}
                  onClick={() => { setFilter(f.val); setPage(1); setSelected(null); }}
                >
                  {f.label}
                </button>
              ))}
            </div>

            <p className="claims-count">{total} claim{total !== 1 ? 's' : ''}</p>

            <div className="insurer-claims-list">
              {claims.length === 0 ? (
                <div className="portal-empty"><p>No claims found.</p></div>
              ) : claims.map(c => (
                <div
                  key={c.id}
                  className={`insurer-claim-card ${selected?.id === c.id ? 'icc-selected' : ''}`}
                  onClick={() => { setSelected(c); setNotes(c.insurer_notes || ''); setMsg(''); }}
                >
                  <div className="icc-top">
                    <span className="icc-id">#{c.id}</span>
                    <span className={`icc-status istatus-${c.status}`}>{c.status?.replace(/_/g,' ')}</span>
                  </div>
                  <p className="icc-name">{c.claimant_name}</p>
                  <p className="icc-type">{c.insurance_type} · {c.policy_number}</p>
                  <div className="icc-bottom">
                    <span className="icc-amount">₹{Number(c.claim_amount||0).toLocaleString('en-IN')}</span>
                    <span className="icc-score" style={{ color: scoreColor(c.readiness_score) }}>
                      Score: {c.readiness_score || '—'}
                    </span>
                  </div>
                  <p className="icc-date">{formatDate(c.created_at)}</p>
                </div>
              ))}
            </div>

            {/* Pagination */}
            {pages > 1 && (
              <div className="portal-pagination">
                <button className="portal-btn-secondary" disabled={page === 1} onClick={() => setPage(p => p-1)}>← Prev</button>
                <span>{page}/{pages}</span>
                <button className="portal-btn-secondary" disabled={page === pages} onClick={() => setPage(p => p+1)}>Next →</button>
              </div>
            )}
          </div>

          {/* Right: Claim detail */}
          <div className="review-panel">
            {!selected ? (
              <div className="review-empty">
                <div className="review-empty-icon">📋</div>
                <p>Select a claim from the list to review it</p>
              </div>
            ) : (
              <>
                <div className="review-header">
                  <h3>Claim #{selected.id}</h3>
                  <span className={`icc-status istatus-${selected.status}`}>{selected.status?.replace(/_/g,' ')}</span>
                </div>

                {/* Claimant info */}
                <div className="review-section">
                  <h4>Claimant</h4>
                  <div className="review-grid">
                    <div className="rg-item"><span>Name</span><strong>{selected.claimant_name}</strong></div>
                    <div className="rg-item"><span>Email</span><strong>{selected.claimant_email}</strong></div>
                    <div className="rg-item"><span>Insurance</span><strong>{selected.insurance_type}</strong></div>
                    <div className="rg-item"><span>Policy No.</span><strong>{selected.policy_number}</strong></div>
                    <div className="rg-item"><span>Claim Amount</span><strong>₹{Number(selected.claim_amount||0).toLocaleString('en-IN')}</strong></div>
                    <div className="rg-item"><span>Submitted</span><strong>{formatDate(selected.created_at)}</strong></div>
                  </div>
                </div>

                {/* Validation score */}
                <div className="review-section">
                  <h4>Validation Score</h4>
                  <div className="score-display">
                    <div className="score-big" style={{ color: scoreColor(selected.readiness_score) }}>
                      {selected.readiness_score || 0}
                      <span>/100</span>
                    </div>
                    <div>
                      <p className="score-label" style={{ color: scoreColor(selected.readiness_score) }}>
                        {selected.readiness_label || 'Not Validated'}
                      </p>
                      <p className="score-hint">
                        {selected.readiness_score >= 80
                          ? 'Well-prepared claim — low risk'
                          : selected.readiness_score >= 50
                          ? 'Moderate preparation — review carefully'
                          : 'Low preparation — high risk claim'}
                      </p>
                    </div>
                  </div>
                </div>

                {/* View full report */}
                <button className="portal-btn-secondary full-width" onClick={() => navigate(`/report/${selected.id}`)}>
                  📊 View Full Validation Report
                </button>

                {/* Notes */}
                <div className="review-section">
                  <h4>Review Notes</h4>
                  <textarea
                    className="review-notes"
                    rows={4}
                    placeholder="Add notes about this claim (reason for approval/rejection, additional info required...)"
                    value={notes}
                    onChange={e => setNotes(e.target.value)}
                  />
                </div>

                {/* Actions */}
                {msg && (
                  <p className={`review-msg ${msg.startsWith('✓') ? 'msg-ok' : 'msg-err'}`}>{msg}</p>
                )}

                <div className="review-actions">
                  <button className="action-btn action-review"
                    onClick={() => handleAction('under_review')} disabled={acting}>
                    🔍 Mark Under Review
                  </button>
                  <button className="action-btn action-info"
                    onClick={() => handleAction('request_info')} disabled={acting}>
                    📩 Request Info
                  </button>
                  <button className="action-btn action-approve"
                    onClick={() => handleAction('approve')} disabled={acting}>
                    ✅ Approve
                  </button>
                  <button className="action-btn action-reject"
                    onClick={() => handleAction('reject')} disabled={acting}>
                    ❌ Reject
                  </button>
                </div>

                {selected.insurer_notes && (
                  <div className="prev-notes">
                    <h4>Previous Notes</h4>
                    <p>{selected.insurer_notes}</p>
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default InsurerPortal;
