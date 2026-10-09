import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getClaimReport, validateClaim, getApprovedNetwork, analyzeDocuments, downloadPackage, getClaimDeadline, getClaimComparison } from '../api';
import QRModal from '../components/QRModal';
import SubmitModal from '../components/SubmitModal';
import ClaimTracker from '../components/ClaimTracker';
import DeadlineTracker from '../components/DeadlineTracker';
import ClaimComparison from '../components/ClaimComparison';
import ClaimValidationReport from '../components/ClaimValidationReport';
import './Report.css';

// ── Score Ring ────────────────────────────────────────────────────────────
function ScoreRing({ score, label, color }) {
  const r    = 70;
  const circ = 2 * Math.PI * r;
  const offset = circ - (score / 100) * circ;
  return (
    <div className="ring-wrap">
      <svg width="180" height="180">
        <circle cx="90" cy="90" r={r} fill="none" stroke="#141e35" strokeWidth="14" />
        <circle cx="90" cy="90" r={r} fill="none" stroke={color} strokeWidth="14"
          strokeDasharray={circ} strokeDashoffset={offset}
          strokeLinecap="round" transform="rotate(-90 90 90)"
          style={{ transition: 'stroke-dashoffset 1.2s ease' }}
        />
      </svg>
      <div className="ring-text">
        <span className="ring-num" style={{ color }}>{score}</span>
        <span className="ring-out">/ 100</span>
        <span className="ring-pct" style={{ color }}>{score}%</span>
        <span className="ring-sub">{label}</span>
      </div>
    </div>
  );
}

// ── Approval Ring ─────────────────────────────────────────────────────────
function ApprovalRing({ pct, color }) {
  const r    = 80;
  const circ = 2 * Math.PI * r;
  const offset = circ - (pct / 100) * circ;
  return (
    <div className="approval-ring-wrap">
      <svg width="200" height="200">
        <circle cx="100" cy="100" r={r} fill="none" stroke="#141e35" strokeWidth="16" />
        <circle cx="100" cy="100" r={r} fill="none" stroke={color} strokeWidth="16"
          strokeDasharray={circ} strokeDashoffset={offset}
          strokeLinecap="round" transform="rotate(-90 100 100)"
          style={{ transition: 'stroke-dashoffset 1.5s ease' }}
        />
      </svg>
      <div className="approval-ring-text">
        <span className="approval-pct" style={{ color }}>{pct}%</span>
        <span className="approval-label">Approval Rate</span>
      </div>
    </div>
  );
}

// ── Main Report ───────────────────────────────────────────────────────────
function Report() {
  const { claimId } = useParams();
  const navigate    = useNavigate();
  const [report,  setReport]  = useState(null);
  const [loading, setLoading] = useState(true);
  const [error,   setError]   = useState('');
  const [showQR,  setShowQR]  = useState(false);
  const [showSubmit, setShowSubmit] = useState(false);
  const [network,    setNetwork]    = useState(null);
  const [analysis,   setAnalysis]   = useState(null);
  const [analyzing,  setAnalyzing]  = useState(false);
  const [deadline,   setDeadline]   = useState(null);
  const [comparison, setComparison] = useState(null);
  const [rejection,  setRejection]  = useState(null);

  useEffect(() => { loadReport(); }, [claimId]); // eslint-disable-line

  const loadReport = async () => {
    try {
      const res = await getClaimReport(claimId);
      if (res.data.readiness_score === null || res.data.readiness_score === undefined) {
        await validateClaim(claimId);
        const res2 = await getClaimReport(claimId);
        setReport(res2.data);
        loadNetwork(res2.data);
      } else {
        setReport(res.data);
        loadNetwork(res.data);
      }
    } catch (e) {
      setError('Failed to load report.');
    } finally {
      setLoading(false);
    }
  };

  const loadNetwork = async (reportData) => {
    try {
      const res = await getApprovedNetwork(reportData.insurance_type_code, '', claimId);
      setNetwork(res.data);
    } catch (e) { /* silent */ }
    try {
      const d = await getClaimDeadline(claimId);
      setDeadline(d.data.deadline);
    } catch (e) { /* silent */ }
    try {
      const c = await getClaimComparison(claimId);
      setComparison(c.data.comparison);
      setRejection(c.data.rejection);
    } catch (e) { /* silent */ }
  };

  const handleAnalyze = async () => {
    setAnalyzing(true);
    try {
      const res = await analyzeDocuments(claimId);
      setAnalysis(res.data);
    } catch (e) {
      console.error(e);
    } finally {
      setAnalyzing(false);
    }
  };

  const handleRevalidate = async () => {
    try {
      await validateClaim(claimId);
      await loadReport();
    } catch (e) {
      console.error('Revalidation failed:', e);
    }
  };

  const handleSaveDraft = async () => {
    try {
      // Save draft: in a real app, this would call an API endpoint
      // For now, we show a simple message
      alert('Claim draft saved. You can continue later.');
    } catch (e) {
      console.error('Save draft failed:', e);
    }
  };

  if (loading) return (
    <div className="report-loading">
      <div className="spinner" /><p>Generating report...</p>
    </div>
  );
  if (error || !report) return (
    <div className="report-loading"><p>{error || 'Report not found.'}</p></div>
  );

  const score      = report.readiness_score || 0;
  const breakdown  = report.score_breakdown || {};
  const violations = report.violations || [];
  const uploaded   = report.uploaded_docs || []; // eslint-disable-line
  const formData   = report.form_data || {};
  const ai         = report.ai_report;
  const docStats   = report.doc_stats || {};
  const fieldStats = report.field_stats || {};

  const scoreColor = score >= 80 ? '#22c55e' : score >= 50 ? '#f59e0b' : '#ef4444';
  const icons = { health:'❤️', vehicle:'🚗', life:'🛡️', property:'🏠', travel:'✈️', crop:'🌾' };

  // AI report colors
  const approvalColor = ai
    ? (ai.approval_percentage >= 80 ? '#22c55e' : ai.approval_percentage >= 50 ? '#f59e0b' : '#ef4444')
    : scoreColor;

  const high   = violations.filter(v => v.severity === 'high');
  const medium = violations.filter(v => v.severity === 'medium');
  const low    = violations.filter(v => v.severity === 'low');

  return (
    <div className="report-page">
      <div className="report-container">

        {/* ── Header ── */}
        <div className="report-header">
          <div className="report-title">
            <span>{icons[report.insurance_type_code] || '📋'}</span>
            <div>
              <h1>Claim Validation Report</h1>
              <p>Claim #{report.id} — {report.insurance_type}</p>
            </div>
          </div>
          <span className="report-status-pill" style={{
            color: scoreColor,
            background: score >= 80 ? 'rgba(34,197,94,0.1)' : score >= 50 ? 'rgba(245,158,11,0.1)' : 'rgba(239,68,68,0.1)'
          }}>
            {report.readiness_label}
          </span>
        </div>

        {/* ── CLAIM VALIDATION REPORT (Human-friendly) ── */}
        <ClaimValidationReport
          claim={report}
          validationResults={report}
          claimId={claimId}
          onRevalidate={handleRevalidate}
          onSaveDraft={handleSaveDraft}
        />

        {/* ── STATUS TRACKER ── */}
        <ClaimTracker claimId={report.id} />

        {/* ── DEADLINE TRACKER ── */}
        <DeadlineTracker deadline={deadline} />

        {/* ── AI APPROVAL SECTION ── */}
        {ai && (
          <div className="ai-section">
            <div className="ai-header">
              <span className="ai-badge">✦ AI Analysis</span>
              <h2>Claim Approval Probability</h2>
            </div>

            <div className="ai-body">
              {/* Big approval ring */}
              <div className="ai-ring-col">
                <ApprovalRing pct={ai.approval_percentage} color={approvalColor} />
                <div className="ai-status-box" style={{
                  color: approvalColor,
                  background: ai.approval_percentage >= 80 ? 'rgba(34,197,94,0.08)' : ai.approval_percentage >= 50 ? 'rgba(245,158,11,0.08)' : 'rgba(239,68,68,0.08)',
                  borderColor: approvalColor
                }}>
                  <span className="ai-status-label">{ai.approval_status} Probability</span>
                  <p className="ai-status-msg">{ai.approval_status_msg}</p>
                </div>
              </div>

              {/* Summary + deductions */}
              <div className="ai-detail-col">
                <div className="ai-summary-box">
                  <h4>Summary</h4>
                  <p>{ai.summary}</p>
                </div>

                {ai.deductions && ai.deductions.length > 0 && (
                  <div className="ai-deductions">
                    <h4>Score Deductions</h4>
                    {ai.deductions.map((d, i) => (
                      <div key={i} className="deduction-row">
                        <span className="deduction-reason">{d.reason}</span>
                        <span className="deduction-val">{d.deduction}%</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Issues + Suggestions side by side */}
            <div className="ai-issues-grid">
              {/* Issues */}
              <div className="ai-issues-col">
                <h4>⚠ Issues Found ({ai.total_issues})</h4>
                {ai.issues.length === 0 ? (
                  <p className="ai-clear">No issues found. Claim looks complete.</p>
                ) : (
                  <ul className="ai-issues-list">
                    {ai.issues.map((issue, i) => (
                      <li key={i} className={`ai-issue ai-issue-${issue.severity}`}>
                        <span className={`issue-dot dot-${issue.severity}`} />
                        {issue.label}
                      </li>
                    ))}
                  </ul>
                )}
              </div>

              {/* Suggestions */}
              <div className="ai-suggestions-col">
                <h4>💡 How to Improve</h4>
                {ai.suggestions.length === 0 ? (
                  <p className="ai-clear">Your claim is ready to submit!</p>
                ) : (
                  <ul className="ai-suggestions-list">
                    {ai.suggestions.map((s, i) => (
                      <li key={i} className="ai-suggestion">
                        <span className="suggestion-arrow">→</span>
                        <div>
                          <p className="suggestion-action">{s.action}</p>
                          {s.detail && <p className="suggestion-detail">{s.detail}</p>}
                        </div>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </div>
          </div>
        )}

        {/* ── SCORE BREAKDOWN ── */}
        <div className="report-grid">
          <div className="report-card">
            <h3>Validation Score</h3>
            <ScoreRing score={score} label={report.readiness_label} color={scoreColor} />

            {/* Score meter bar */}
            <div className="score-meter">
              <div className="score-meter-track">
                <div className="score-meter-fill" style={{ width: `${score}%`, backgroundColor: scoreColor }} />
                <div className="score-meter-marker" style={{ left: `${score}%` }} />
              </div>
              <div className="score-meter-labels">
                <span style={{ color: '#ef4444' }}>0</span>
                <span style={{ color: '#f59e0b' }}>50</span>
                <span style={{ color: '#22c55e' }}>100</span>
              </div>
              <div className="score-zones">
                <span className="zone zone-red">Incomplete</span>
                <span className="zone zone-yellow">Needs Attention</span>
                <span className="zone zone-green">Ready</span>
              </div>
            </div>

            <div className="breakdown-list">
              {[
                { label: 'Documents',   key: 'document',    max: 40, color: '#3b82f6',
                  detail: docStats.total_required ? `${docStats.uploaded_required}/${docStats.total_required} uploaded · ${docStats.upload_rate}%` : null },
                { label: 'Fields',      key: 'field',       max: 35, color: '#06b6d4',
                  detail: fieldStats.total_fields ? `${fieldStats.filled_fields}/${fieldStats.total_fields} filled · ${fieldStats.fill_rate}%` : null },
                { label: 'Consistency', key: 'consistency', max: 25, color: '#22c55e',
                  detail: violations.filter(v=>v.severity!=='low').length === 0 ? 'No issues' : `${violations.filter(v=>v.severity!=='low').length} issue(s) found` },
              ].map(({ label, key, max, color, detail }) => {
                const val = breakdown[key] || 0;
                const pct = Math.round((val / max) * 100);
                return (
                  <div key={key} className="breakdown-row">
                    <div className="breakdown-meta">
                      <div>
                        <span>{label}</span>
                        {detail && <span className="breakdown-detail">{detail}</span>}
                      </div>
                      <div className="breakdown-right">
                        <span style={{ color }} className="breakdown-score">{val}/{max}</span>
                        <span className="breakdown-pct" style={{ color }}>{pct}%</span>
                      </div>
                    </div>
                    <div className="breakdown-track">
                      <div className="breakdown-fill" style={{ width: `${pct}%`, backgroundColor: color }} />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Violations */}
          <div className="report-card">
            <div className="violations-pills">
              {high.length   > 0 && <span className="pill pill-high">{high.length} High</span>}
              {medium.length > 0 && <span className="pill pill-med">{medium.length} Medium</span>}
              {low.length    > 0 && <span className="pill pill-low">{low.length} Low</span>}
              {violations.length === 0 && <span className="pill pill-ok">All Clear ✓</span>}
            </div>
            <h3>Rule Violations ({violations.length})</h3>
            {violations.length === 0 ? (
              <div className="all-clear">
                <div className="all-clear-icon">✓</div>
                <p>No rule violations found.</p>
              </div>
            ) : (
              <div className="violations-list">
                {[...high, ...medium, ...low].map((v, i) => (
                  <div key={i} className={`violation-card violation-${v.severity}`}>
                    <span className={`violation-badge badge-${v.severity}`}>{v.severity}</span>
                    <p className="violation-msg">{v.message}</p>
                    <p className="violation-fix">💡 {v.suggestion}</p>
                    {v.rule_name && !v.rule_name.includes('document') && (
                      <button
                        className="fix-now-btn"
                        onClick={() => navigate(-1)}
                      >
                        ✏️ Fix Now
                      </button>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* ── DOCUMENT STATUS TABLE ── */}
        {docStats.required_docs && (
          <div className="report-card full-card">
            <div className="doc-status-header">
              <h3>Document Status</h3>
              <div className="doc-status-pills">
                <span className="ds-pill ds-green">{docStats.uploaded_required}/{docStats.total_required} Required Uploaded</span>
                {docStats.total_optional > 0 && (
                  <span className="ds-pill ds-blue">{docStats.uploaded_optional}/{docStats.total_optional} Optional Uploaded</span>
                )}
                <span className="ds-pill ds-rate">{docStats.upload_rate}% Upload Rate</span>
              </div>
            </div>

            {/* Required docs */}
            <div className="doc-table">
              <div className="doc-table-head">
                <span>Required Documents</span>
                <span>Weight</span>
                <span>Status</span>
              </div>
              {docStats.required_docs.map((doc, i) => (
                <div key={i} className={`doc-table-row ${doc.uploaded ? 'row-ok' : 'row-missing'}`}>
                  <span className="doc-table-name">{doc.label}</span>
                  <span className="doc-table-weight">{doc.weight}pts</span>
                  <span className={`doc-table-status ${doc.uploaded ? 'status-ok' : 'status-missing'}`}>
                    {doc.uploaded ? '✓ Uploaded' : '✕ Missing'}
                  </span>
                </div>
              ))}
            </div>

            {/* Optional docs */}
            {docStats.optional_docs && docStats.optional_docs.length > 0 && (
              <div className="doc-table" style={{ marginTop: '1rem' }}>
                <div className="doc-table-head">
                  <span>Optional Documents</span>
                  <span>Weight</span>
                  <span>Status</span>
                </div>
                {docStats.optional_docs.map((doc, i) => (
                  <div key={i} className={`doc-table-row ${doc.uploaded ? 'row-ok' : 'row-optional'}`}>
                    <span className="doc-table-name">{doc.label}</span>
                    <span className="doc-table-weight">{doc.weight}pts</span>
                    <span className={`doc-table-status ${doc.uploaded ? 'status-ok' : 'status-optional'}`}>
                      {doc.uploaded ? '✓ Uploaded' : '— Not uploaded'}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* ── FIELD STATUS TABLE ── */}
        {fieldStats.fields && (
          <div className="report-card full-card">
            <div className="doc-status-header">
              <h3>Field Completion</h3>
              <div className="doc-status-pills">
                <span className="ds-pill ds-green">{fieldStats.filled_fields}/{fieldStats.total_fields} Fields Filled</span>
                <span className="ds-pill ds-rate">{fieldStats.fill_rate}% Completion Rate</span>
              </div>
            </div>
            <div className="field-grid">
              {fieldStats.fields.map((f, i) => (
                <div key={i} className={`field-status-item ${f.filled ? 'field-ok' : 'field-missing'}`}>
                  <span className={`field-status-icon ${f.filled ? 'icon-ok' : 'icon-missing'}`}>
                    {f.filled ? '✓' : '✕'}
                  </span>
                  <span className="field-status-label">{f.label}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ── CLAIM SUMMARY ── */}
        {Object.keys(formData).length > 0 && (
          <div className="report-card full-card">
            <h3>Claim Summary</h3>
            <div className="summary-grid">
              {Object.entries(formData).map(([k, v]) => (
                <div key={k} className="summary-row">
                  <span className="summary-key">{k.replace(/_/g, ' ')}</span>
                  <span className="summary-val">{v}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ── HISTORY COMPARISON + REJECTION PREDICTOR ── */}
        <ClaimComparison comparison={comparison} rejection={rejection} />

        {/* ── APPROVED NETWORK ── */}
        {network && network.providers && network.providers.length > 0 && (
          <div className="report-card full-card">
            <div className="network-header">
              <div>
                <h3>🏥 Approved Network</h3>
                <p className="network-msg">{network.message}</p>
              </div>
              <span className="network-count">{network.total} providers</span>
            </div>
            <div className="network-grid">
              {network.providers.map((p, i) => (
                <div key={i} className="network-card">
                  <div className="network-top">
                    <span className="network-name">{p.name}</span>
                    {p.cashless && <span className="cashless-badge">Cashless</span>}
                  </div>
                  <p className="network-location">📍 {p.city}, {p.state}</p>
                  <p className="network-speciality">🔬 {p.speciality}</p>
                  <div className="network-insurers">
                    {p.insurers.slice(0,3).map((ins, j) => (
                      <span key={j} className="insurer-tag">{ins}</span>
                    ))}
                  </div>
                  <div className="network-rating">{'★'.repeat(Math.round(p.rating))} {p.rating}</div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ── SMART DOCUMENT ANALYZER ── */}
        <div className="report-card full-card">
          <div className="analyzer-header">
            <div>
              <h3>🔍 Smart Document Analyzer</h3>
              <p className="muted-text">Cross-check names, dates, policy numbers and amounts across your documents</p>
            </div>
            <button className="btn-analyze" onClick={handleAnalyze} disabled={analyzing}>
              {analyzing ? 'Analyzing...' : 'Run Analysis'}
            </button>
          </div>

          {analysis && (
            <div className="analysis-results">
              <div className="analysis-summary">
                <span className="asummary-item">📄 {analysis.analyzed_docs} docs analyzed</span>
                <span className="asummary-item asummary-ok">✓ {analysis.confirmations} confirmed</span>
                <span className="asummary-item asummary-issue">⚠ {analysis.issues} issues</span>
              </div>
              <div className="findings-list">
                {analysis.findings.map((f, i) => (
                  <div key={i} className={`finding-item finding-${f.type === 'match' ? 'ok' : f.severity}`}>
                    <div className="finding-top">
                      <span className="finding-doc">{f.document}</span>
                      <span className={`finding-badge fbadge-${f.type === 'match' ? 'ok' : f.severity}`}>
                        {f.type === 'match' ? '✓ Verified' : f.type === 'mismatch' ? '✗ Mismatch' : 'ℹ Info'}
                      </span>
                    </div>
                    <p className="finding-msg">{f.message}</p>
                    {f.suggestion && <p className="finding-fix">→ {f.suggestion}</p>}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* ── ACTIONS ── */}
        <div className="report-actions">
          <button className="btn-secondary" onClick={() => navigate('/dashboard')}>View All Claims</button>
          <button className="btn-secondary" onClick={() => navigate(-1)}>Edit Details</button>
          <button className="btn-qr"     onClick={() => setShowQR(true)}>📱 QR Code</button>
          <a className="btn-download" href={downloadPackage(report.id)} target="_blank" rel="noreferrer">⬇ Download Package</a>
          <button className="btn-submit" onClick={() => setShowSubmit(true)}>🚀 Submit to Insurer</button>
        </div>

        {/* ── MODALS ── */}
        {showQR && (
          <QRModal claimId={report.id} onClose={() => setShowQR(false)} />
        )}
        {showSubmit && (
          <SubmitModal
            claimId={report.id}
            insuranceTypeCode={report.insurance_type_code}
            score={score}
            onClose={() => setShowSubmit(false)}
          />
        )}

      </div>
    </div>
  );
}

export default Report;
