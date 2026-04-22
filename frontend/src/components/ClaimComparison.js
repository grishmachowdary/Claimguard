import React from 'react';
import './ClaimComparison.css';

function ClaimComparison({ comparison, rejection }) {
  if (!comparison && !rejection) return null;

  return (
    <div className="comparison-section">
      {/* History Comparison */}
      {comparison && (
        <div className="comparison-card">
          <h3>📈 Claim History Comparison</h3>
          <div className="comparison-scores">
            <div className="comp-score-item">
              <span className="comp-score-label">Previous Claim #{comparison.previous_claim_id}</span>
              <span className="comp-score-val" style={{ color: comparison.previous_score >= 80 ? '#22c55e' : comparison.previous_score >= 50 ? '#f59e0b' : '#ef4444' }}>
                {comparison.previous_score}
              </span>
            </div>
            <div className="comp-arrow">
              <span style={{ color: comparison.score_diff >= 0 ? '#22c55e' : '#ef4444' }}>
                {comparison.score_diff >= 0 ? '▲' : '▼'} {Math.abs(comparison.score_diff)} pts
              </span>
            </div>
            <div className="comp-score-item">
              <span className="comp-score-label">This Claim</span>
              <span className="comp-score-val" style={{ color: comparison.current_score >= 80 ? '#22c55e' : comparison.current_score >= 50 ? '#f59e0b' : '#ef4444' }}>
                {comparison.current_score}
              </span>
            </div>
          </div>

          <p className="comp-summary">{comparison.summary}</p>

          <div className="comp-lists">
            {comparison.improvements.length > 0 && (
              <div className="comp-list">
                <h4>✅ What Improved</h4>
                {comparison.improvements.map((item, i) => (
                  <p key={i} className="comp-item comp-ok">+ {item}</p>
                ))}
              </div>
            )}
            {comparison.regressions.length > 0 && (
              <div className="comp-list">
                <h4>⚠ What Got Worse</h4>
                {comparison.regressions.map((item, i) => (
                  <p key={i} className="comp-item comp-bad">- {item}</p>
                ))}
              </div>
            )}
          </div>

          <div className="comp-stats">
            <span>Past claims: {comparison.total_past_claims}</span>
            <span>Average score: {comparison.avg_past_score}</span>
          </div>
        </div>
      )}

      {/* Rejection Predictor */}
      {rejection && (
        <div className="rejection-card">
          <h3>🎯 Rejection Risk Predictor</h3>
          <div className="rejection-header">
            <div className="rejection-ring">
              <svg width="100" height="100">
                <circle cx="50" cy="50" r="40" fill="none" stroke="#141e35" strokeWidth="10" />
                <circle cx="50" cy="50" r="40" fill="none"
                  stroke={rejection.risk_color}
                  strokeWidth="10"
                  strokeDasharray={`${2 * Math.PI * 40}`}
                  strokeDashoffset={`${2 * Math.PI * 40 * (1 - rejection.rejection_probability / 100)}`}
                  strokeLinecap="round"
                  transform="rotate(-90 50 50)"
                  style={{ transition: 'stroke-dashoffset 1s ease' }}
                />
              </svg>
              <div className="rejection-ring-text">
                <span style={{ color: rejection.risk_color }}>{rejection.rejection_probability}%</span>
                <span>Risk</span>
              </div>
            </div>
            <div className="rejection-info">
              <span className="rejection-level" style={{ color: rejection.risk_color }}>
                {rejection.risk_level}
              </span>
              <p className="rejection-rec">{rejection.recommendation}</p>
            </div>
          </div>

          {rejection.risk_factors.length > 0 && (
            <div className="risk-factors">
              <h4>Risk Factors</h4>
              {rejection.risk_factors.map((f, i) => (
                <div key={i} className={`risk-factor risk-${f.impact}`}>
                  <div className="risk-factor-top">
                    <span className="risk-factor-label">{f.factor}</span>
                    <span className={`risk-badge rbadge-${f.impact}`}>{f.impact}</span>
                  </div>
                  <p className="risk-note">{f.note}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default ClaimComparison;
