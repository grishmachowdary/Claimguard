import React from 'react';
import './DeadlineTracker.css';

function DeadlineTracker({ deadline }) {
  if (!deadline) return null;

  const { remaining, unit, deadline_display, urgency, urgency_color,
          urgency_msg, progress, from_label, is_expired, total_window } = deadline;

  return (
    <div className={`deadline-card deadline-${urgency}`}>
      <div className="deadline-header">
        <div className="deadline-icon-wrap">
          {is_expired ? '⏰' : urgency === 'critical' ? '🚨' : urgency === 'warning' ? '⚠️' : '📅'}
        </div>
        <div>
          <h4 className="deadline-title">Submission Deadline</h4>
          <p className="deadline-sub">Based on {from_label} date</p>
        </div>
        <div className="deadline-remaining" style={{ color: urgency_color }}>
          {is_expired ? 'EXPIRED' : `${remaining} ${unit}`}
        </div>
      </div>

      <div className="deadline-bar-wrap">
        <div className="deadline-bar">
          <div
            className="deadline-fill"
            style={{ width: `${progress}%`, backgroundColor: urgency_color }}
          />
        </div>
        <div className="deadline-bar-labels">
          <span>Incident</span>
          <span>Deadline: {deadline_display}</span>
        </div>
      </div>

      <p className="deadline-msg" style={{ color: urgency_color }}>{urgency_msg}</p>

      <p className="deadline-note">
        Most insurers require submission within {total_window} {unit === 'hours' ? 'hours' : 'days'} of {from_label}.
      </p>
    </div>
  );
}

export default DeadlineTracker;
