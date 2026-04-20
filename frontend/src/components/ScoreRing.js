import React from 'react';
import './ScoreRing.css';

function ScoreRing({ score, label }) {
  const getColor = () => {
    if (score >= 80) return 'var(--green)';
    if (score >= 50) return 'var(--yellow)';
    return 'var(--red)';
  };

  const circumference = 2 * Math.PI * 70;
  const strokeDashoffset = circumference - (score / 100) * circumference;

  return (
    <div className="score-ring-container">
      <svg className="score-ring" width="200" height="200">
        <circle
          cx="100"
          cy="100"
          r="70"
          fill="none"
          stroke="var(--bg-primary)"
          strokeWidth="12"
        />
        <circle
          cx="100"
          cy="100"
          r="70"
          fill="none"
          stroke={getColor()}
          strokeWidth="12"
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
          strokeLinecap="round"
          transform="rotate(-90 100 100)"
          style={{ transition: 'stroke-dashoffset 1s ease' }}
        />
      </svg>
      <div className="score-content">
        <div className="score-number" style={{ color: getColor() }}>
          {score}
        </div>
        <div className="score-label">{label}</div>
      </div>
    </div>
  );
}

export default ScoreRing;
