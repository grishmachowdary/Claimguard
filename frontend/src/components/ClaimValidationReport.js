import React from 'react';
import { useNavigate } from 'react-router-dom';
import './ClaimValidationReport.css';

/**
 * ClaimValidationReport component
 * Displays validation results in a human-friendly, non-technical format.
 * 
 * Props:
 *   - claim: the claim object (optional, for reference)
 *   - validationResults: the validation response from /api/claims/<id>/validate
 *   - claimId: the claim ID for navigation
 *   - onRevalidate: callback function to rerun validation
 *   - onSaveDraft: callback function to save as draft
 *   - onUploadDocument: callback function when Upload Document is clicked (optional)
 *   - onFixField: callback function when Fix This is clicked (optional)
 *   - onReviewWarning: callback function when Review is clicked (optional)
 */
function ClaimValidationReport({ 
  claim, 
  validationResults, 
  claimId,
  onRevalidate, 
  onSaveDraft,
  onUploadDocument,
  onFixField,
  onReviewWarning
}) {
  const navigate = useNavigate();

  if (!validationResults) {
    return (
      <section className="cvr-container">
        <div className="cvr-empty">
          <p>Loading validation results...</p>
        </div>
      </section>
    );
  }

  // Action handlers
  const handleUploadDocument = (docName) => {
    if (onUploadDocument) {
      onUploadDocument(docName);
    } else if (claimId) {
      // Default behavior: navigate to documents page
      navigate(`/documents/${claimId}`, { state: { focusDoc: docName } });
    }
  };

  const handleFixField = (fieldName) => {
    if (onFixField) {
      onFixField(fieldName);
    } else if (claimId) {
      // Default behavior: navigate to details page
      navigate(`/details/${claimId}`, { state: { focusField: fieldName } });
    }
  };

  const handleReviewWarning = (warningIndex) => {
    if (onReviewWarning) {
      onReviewWarning(warningIndex);
    }
  };

  // Determine status and color
  const status = validationResults.status || 'needs_attention';
  const statusMessages = {
    approved: { icon: '✅', title: 'APPROVED — Your claim is ready to submit!', class: 'approved' },
    ready: { icon: '✅', title: 'READY — No issues found. You can submit.', class: 'ready' },
    needs_attention: { icon: '🟡', title: `NEEDS ATTENTION — Fix ${validationResults.summary?.issues_count || 0} issues below and resubmit.`, class: 'needs_attention' },
  };

  const statusBanner = statusMessages[status] || statusMessages.needs_attention;

  // Extract summary data
  const summary = validationResults.summary || {
    documents_uploaded: 0,
    documents_total: 0,
    fields_filled: 0,
    fields_total: 0,
    issues_count: 0,
  };

  const docProgress = summary.documents_total > 0 ? (summary.documents_uploaded / summary.documents_total) * 100 : 0;
  const fieldProgress = summary.fields_total > 0 ? (summary.fields_filled / summary.fields_total) * 100 : 0;

  // Extract issues
  const missingDocuments = validationResults.missing_documents || [];
  const dataIssues = validationResults.data_issues || [];
  const warnings = validationResults.warnings || [];

  return (
    <section className="cvr-container">
      {/* Status Banner */}
      <div className={`cvr-banner ${statusBanner.class}`}>
        <span className="cvr-banner-icon">{statusBanner.icon}</span>
        <div className="cvr-banner-content">
          <h2 className="cvr-banner-title">{statusBanner.title}</h2>
        </div>
      </div>

      {/* Quick Summary Card */}
      <article className="cvr-summary-card">
        <h3 className="cvr-summary-title">Quick Summary</h3>
        
        {/* Documents */}
        <div className="cvr-summary-row">
          <div className="cvr-summary-label">
            <span className="cvr-summary-text">Documents: {summary.documents_uploaded} of {summary.documents_total} uploaded</span>
          </div>
          <div className="cvr-summary-progress">
            <div className="cvr-progress-bar-track">
              <div className="cvr-progress-bar-fill" style={{ width: `${docProgress}%` }} />
            </div>
          </div>
        </div>

        {/* Fields */}
        <div className="cvr-summary-row">
          <div className="cvr-summary-label">
            <span className="cvr-summary-text">Information: {summary.fields_filled} of {summary.fields_total} fields filled</span>
          </div>
          <div className="cvr-summary-progress">
            <div className="cvr-progress-bar-track">
              <div className="cvr-progress-bar-fill" style={{ width: `${fieldProgress}%` }} />
            </div>
          </div>
        </div>

        {/* Issues */}
        <div className="cvr-summary-row">
          <div className="cvr-summary-label">
            <span className="cvr-summary-text">Issues found: {summary.issues_count}</span>
          </div>
          <div className="cvr-summary-progress">
            <div className={`cvr-issues-count ${summary.issues_count > 0 ? 'has-issues' : 'no-issues'}`}>
              {summary.issues_count > 0 ? `${summary.issues_count} found` : 'All clear'}
            </div>
          </div>
        </div>
      </article>

      {/* Missing Documents Section */}
      {missingDocuments.length > 0 && (
        <section className="cvr-group">
          <h3 className="cvr-group-header">MISSING DOCUMENTS ({missingDocuments.length})</h3>
          {missingDocuments.map((doc, idx) => (
            <article key={idx} className="cvr-issue-card">
              <span className="cvr-issue-icon">📄</span>
              <div className="cvr-issue-body">
                <h4 className="cvr-issue-name">{doc.name || 'Unnamed Document'}</h4>
                <p className="cvr-issue-message">{doc.reason || 'This document is required for your claim.'}</p>
                <button 
                  className="cvr-btn cvr-btn-upload"
                  onClick={() => handleUploadDocument(doc.name)}
                >
                  Upload Document
                </button>
              </div>
            </article>
          ))}
        </section>
      )}

      {/* Data Issues Section */}
      {dataIssues.length > 0 && (
        <section className="cvr-group">
          <h3 className="cvr-group-header">DATA ISSUES ({dataIssues.length})</h3>
          {dataIssues.map((issue, idx) => {
            // Format field name: replace underscores with spaces, capitalize
            const fieldLabel = (issue.field || 'unknown')
              .split('_')
              .map(word => word.charAt(0).toUpperCase() + word.slice(1))
              .join(' ');
            
            return (
              <article key={idx} className="cvr-issue-card">
                <span className="cvr-issue-icon">⚠️</span>
                <div className="cvr-issue-body">
                  <h4 className="cvr-issue-name">{fieldLabel}</h4>
                  <p className="cvr-issue-message">{issue.message || 'There is an issue with this field.'}</p>
                  {issue.suggestion && (
                    <p className="cvr-issue-suggestion">{issue.suggestion}</p>
                  )}
                  <button 
                    className="cvr-btn cvr-btn-fix"
                    onClick={() => handleFixField(issue.field)}
                  >
                    Fix This
                  </button>
                </div>
              </article>
            );
          })}
        </section>
      )}

      {/* Warnings Section */}
      {warnings.length > 0 && (
        <section className="cvr-group">
          <h3 className="cvr-group-header">WARNINGS ({warnings.length})</h3>
          {warnings.map((warning, idx) => (
            <article key={idx} className="cvr-issue-card">
              <span className="cvr-issue-icon">ℹ️</span>
              <div className="cvr-issue-body">
                <p className="cvr-issue-message">{warning.message || 'Please review this item.'}</p>
                {warning.suggestion && (
                  <p className="cvr-issue-suggestion">{warning.suggestion}</p>
                )}
                <button 
                  className="cvr-btn cvr-btn-review"
                  onClick={() => handleReviewWarning(idx)}
                >
                  Review
                </button>
              </div>
            </article>
          ))}
        </section>
      )}

      {/* Next Steps Section */}
      <div className="cvr-next-steps">
        {onRevalidate && (
          <button className="cvr-btn cvr-btn-revalidate" onClick={onRevalidate}>
            Validate Again
          </button>
        )}
        {onSaveDraft && (
          <button className="cvr-btn cvr-btn-save" onClick={onSaveDraft}>
            Save & Continue Later
          </button>
        )}
      </div>
    </section>
  );
}

export default ClaimValidationReport;
