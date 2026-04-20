import React from 'react';
import './ViolationCard.css';

function ViolationCard({ violation }) {
  const getIcon = (severity) => {
    if (severity === 'high') return '🔴';
    if (severity === 'medium') return '🟡';
    return '🔵';
  };

  return (
    <div className={`violation-card card severity-${violation.severity}`}>
      <div className="violation-header">
        <span className="violation-icon">{getIcon(violation.severity)}</span>
        <span className={`severity-badge severity-${violation.severity}`}>
          {violation.severity}
        </span>
      </div>
      <h4 className="violation-message">{violation.message}</h4>
      <p className="violation-suggestion">{violation.suggestion}</p>
    </div>
  );
}

export default ViolationCard;
