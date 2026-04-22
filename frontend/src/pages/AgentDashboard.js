import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import api from '../api';
import './AgentDashboard.css';
import '../pages/Portal.css';

function AgentDashboard() {
  const { user } = useAuth();
  const navigate = useNavigate();

  const [stats,      setStats]      = useState(null);
  const [clients,    setClients]    = useState([]);
  const [selected,   setSelected]   = useState(null);
  const [clientClaims, setClientClaims] = useState([]);
  const [addEmail,   setAddEmail]   = useState('');
  const [addError,   setAddError]   = useState('');
  const [addSuccess, setAddSuccess] = useState('');
  const [loading,    setLoading]    = useState(true);
  const [tab,        setTab]        = useState('overview'); // overview | clients | claims

  useEffect(() => {
    if (user?.role !== 'agent') { navigate('/'); return; }
    loadAll();
  }, []); // eslint-disable-line

  const loadAll = async () => {
    try {
      const [statsRes, clientsRes] = await Promise.all([
        api.get('/agent/stats'),
        api.get('/agent/clients'),
      ]);
      setStats(statsRes.data);
      setClients(clientsRes.data.clients || []);
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  };

  const loadClientClaims = async (clientId) => {
    try {
      const res = await api.get(`/agent/clients/${clientId}/claims`);
      setClientClaims(res.data.claims || []);
    } catch (e) { console.error(e); }
  };

  const handleSelectClient = (client) => {
    setSelected(client);
    setTab('claims');
    loadClientClaims(client.id);
  };

  const handleAddClient = async () => {
    setAddError(''); setAddSuccess('');
    if (!addEmail.trim()) { setAddError('Enter client email'); return; }
    try {
      await api.post('/agent/clients', { email: addEmail.trim() });
      setAddSuccess('Client added successfully!');
      setAddEmail('');
      loadAll();
    } catch (e) {
      setAddError(e.response?.data?.error || 'Failed to add client');
    }
  };

  const handleRemoveClient = async (clientId) => {
    if (!window.confirm('Remove this client from your portfolio?')) return;
    try {
      await api.delete(`/agent/clients/${clientId}`);
      loadAll();
      if (selected?.id === clientId) { setSelected(null); setTab('overview'); }
    } catch (e) { console.error(e); }
  };

  const scoreColor = (s) => !s ? '#475569' : s >= 80 ? '#22c55e' : s >= 50 ? '#f59e0b' : '#ef4444';
  const formatDate = (d) => d ? new Date(d).toLocaleDateString('en-IN', { day:'2-digit', month:'short', year:'numeric' }) : '—';

  if (loading) return <div className="portal-loading"><div className="spinner" /><p>Loading agent dashboard...</p></div>;

  return (
    <div className="portal-page">
      <div className="portal-container">

        {/* Header */}
        <div className="portal-header">
          <div>
            <div className="portal-badge agent-badge">🤝 Agent Portal</div>
            <h1>Agent Dashboard</h1>
            <p>Welcome, {user?.full_name} — manage your client portfolio</p>
          </div>
          <button className="portal-back-btn" onClick={() => navigate('/')}>← Back to App</button>
        </div>

        {/* Stats */}
        {stats && (
          <div className="portal-stats">
            {[
              { label: 'Total Clients',    val: stats.total_clients,   color: '#3b82f6' },
              { label: 'Total Claims',     val: stats.total_claims,    color: '#06b6d4' },
              { label: 'Avg Score',        val: stats.avg_score,       color: '#f59e0b' },
              { label: 'Ready to Submit',  val: stats.ready_to_submit, color: '#22c55e' },
              { label: 'Submitted',        val: stats.submitted,       color: '#3b82f6' },
              { label: 'Approved',         val: stats.approved,        color: '#22c55e' },
              { label: 'Needs Attention',  val: stats.needs_attention, color: '#ef4444' },
            ].map(({ label, val, color }) => (
              <div key={label} className="portal-stat-card">
                <span className="pstat-val" style={{ color }}>{val}</span>
                <span className="pstat-label">{label}</span>
              </div>
            ))}
          </div>
        )}

        {/* Tabs */}
        <div className="portal-tabs">
          <button className={`ptab ${tab === 'overview' ? 'ptab-active' : ''}`} onClick={() => setTab('overview')}>Overview</button>
          <button className={`ptab ${tab === 'clients'  ? 'ptab-active' : ''}`} onClick={() => setTab('clients')}>Clients ({clients.length})</button>
          {selected && (
            <button className={`ptab ${tab === 'claims' ? 'ptab-active' : ''}`} onClick={() => setTab('claims')}>
              {selected.full_name}'s Claims
            </button>
          )}
        </div>

        {/* Overview Tab */}
        {tab === 'overview' && (
          <div className="portal-section">
            <h3>Add New Client</h3>
            <p className="portal-hint">Enter the email of a registered ClaimGuard user to add them to your portfolio.</p>
            <div className="add-client-row">
              <input
                className="portal-input"
                type="email"
                placeholder="client@example.com"
                value={addEmail}
                onChange={e => { setAddEmail(e.target.value); setAddError(''); setAddSuccess(''); }}
                onKeyDown={e => e.key === 'Enter' && handleAddClient()}
              />
              <button className="portal-btn-primary" onClick={handleAddClient}>Add Client</button>
            </div>
            {addError   && <p className="portal-error">⚠ {addError}</p>}
            {addSuccess && <p className="portal-success">✓ {addSuccess}</p>}

            <h3 style={{ marginTop: '2rem' }}>Recent Clients</h3>
            {clients.length === 0 ? (
              <div className="portal-empty">
                <p>No clients yet. Add your first client above.</p>
              </div>
            ) : (
              <div className="clients-grid">
                {clients.slice(0, 6).map(c => (
                  <div key={c.id} className="client-card" onClick={() => handleSelectClient(c)}>
                    <div className="client-avatar">{c.full_name.charAt(0).toUpperCase()}</div>
                    <div className="client-info">
                      <p className="client-name">{c.full_name}</p>
                      <p className="client-email">{c.email}</p>
                    </div>
                    <div className="client-stats">
                      <span className="client-stat">{c.total_claims} claims</span>
                      <span className="client-score" style={{ color: scoreColor(c.avg_score) }}>{c.avg_score || '—'}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Clients Tab */}
        {tab === 'clients' && (
          <div className="portal-section">
            <div className="section-header">
              <h3>All Clients ({clients.length})</h3>
              <div className="add-client-row">
                <input className="portal-input" type="email" placeholder="Add client by email"
                  value={addEmail} onChange={e => { setAddEmail(e.target.value); setAddError(''); setAddSuccess(''); }} />
                <button className="portal-btn-primary" onClick={handleAddClient}>+ Add</button>
              </div>
            </div>
            {addError   && <p className="portal-error">⚠ {addError}</p>}
            {addSuccess && <p className="portal-success">✓ {addSuccess}</p>}

            <div className="clients-table">
              <div className="ct-head">
                <span>Client</span><span>Claims</span><span>Avg Score</span>
                <span>Ready</span><span>Pending</span><span>Actions</span>
              </div>
              {clients.map(c => (
                <div key={c.id} className="ct-row">
                  <div className="ct-client">
                    <div className="client-avatar sm">{c.full_name.charAt(0).toUpperCase()}</div>
                    <div>
                      <p className="ct-name">{c.full_name}</p>
                      <p className="ct-email">{c.email}</p>
                    </div>
                  </div>
                  <span className="ct-val">{c.total_claims}</span>
                  <span className="ct-val" style={{ color: scoreColor(c.avg_score) }}>{c.avg_score || '—'}</span>
                  <span className="ct-val" style={{ color: '#22c55e' }}>{c.ready_claims}</span>
                  <span className="ct-val" style={{ color: '#f59e0b' }}>{c.pending_claims}</span>
                  <div className="ct-actions">
                    <button className="ct-btn" onClick={() => handleSelectClient(c)}>View Claims</button>
                    <button className="ct-btn ct-btn-danger" onClick={() => handleRemoveClient(c.id)}>Remove</button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Client Claims Tab */}
        {tab === 'claims' && selected && (
          <div className="portal-section">
            <div className="section-header">
              <div>
                <h3>{selected.full_name}'s Claims</h3>
                <p className="portal-hint">{selected.email}</p>
              </div>
              <button className="portal-btn-secondary" onClick={() => { setTab('clients'); setSelected(null); }}>← Back to Clients</button>
            </div>

            {clientClaims.length === 0 ? (
              <div className="portal-empty"><p>No claims found for this client.</p></div>
            ) : (
              <div className="claims-table">
                <div className="claims-head">
                  <span>Claim</span><span>Insurance</span><span>Policy No.</span>
                  <span>Score</span><span>Status</span><span>Date</span><span>Action</span>
                </div>
                {clientClaims.map(c => (
                  <div key={c.id} className="claims-row">
                    <span className="cr-id">#{c.id}</span>
                    <span className="cr-type">{c.insurance_type}</span>
                    <span className="cr-policy">{c.policy_number}</span>
                    <span className="cr-score" style={{ color: scoreColor(c.readiness_score) }}>
                      {c.readiness_score || '—'}
                    </span>
                    <span className={`cr-status status-${c.status}`}>{c.status?.replace(/_/g,' ')}</span>
                    <span className="cr-date">{formatDate(c.created_at)}</span>
                    <button className="ct-btn" onClick={() => navigate(`/report/${c.id}`)}>View</button>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

      </div>
    </div>
  );
}

export default AgentDashboard;
