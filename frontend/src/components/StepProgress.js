import React from 'react';
import './StepProgress.css';

const STEPS = [
  { label: 'Select Type', icon: '🏷️' },
  { label: 'Documents',   icon: '📎' },
  { label: 'Details',     icon: '✏️' },
  { label: 'Report',      icon: '📊' },
];

function StepProgress({ current }) {
  // current: 0=home, 1=documents, 2=details, 3=report
  return (
    <div className="step-progress">
      {STEPS.map((step, i) => (
        <React.Fragment key={i}>
          <div className={`sp-step ${i < current ? 'sp-done' : i === current ? 'sp-active' : 'sp-pending'}`}>
            <div className="sp-icon">
              {i < current ? '✓' : step.icon}
            </div>
            <span className="sp-label">{step.label}</span>
          </div>
          {i < STEPS.length - 1 && (
            <div className={`sp-line ${i < current ? 'sp-line-done' : ''}`} />
          )}
        </React.Fragment>
      ))}
    </div>
  );
}

export default StepProgress;
