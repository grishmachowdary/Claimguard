import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getRules, createClaim } from '../api';
import './Documents.css';

function Documents() {
  const { insuranceType } = useParams();
  const navigate = useNavigate();

  const [, setInsuranceInfo] = useState(null);
  const [documents, setDocuments] = useState([]);
  const [checkedDocs, setCheckedDocs] = useState({});
  const [uploadedFiles, setUploadedFiles] = useState({});
  const [uploading, setUploading] = useState({});
  const [claimId, setClaimId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const fileInputRefs = useRef({});

  useEffect(() => {
    init();
  }, [insuranceType]); // eslint-disable-line

  const init = async () => {
    try {
      setLoading(true);
      setError('');

      // Load rules
      const rulesRes = await getRules(insuranceType);
      const data = rulesRes.data;
      setInsuranceInfo({ id: data.insurance_type_id, code: insuranceType });
      setDocuments(data.documents || []);

      // Create claim
      const claimRes = await createClaim({ insurance_type_id: data.insurance_type_id, uploaded_docs: [] });
      setClaimId(claimRes.data.id);
      localStorage.setItem('claim_id', claimRes.data.id);
      localStorage.setItem('insurance_type', insuranceType);

      setLoading(false);
    } catch (err) {
      console.error(err);
      setError('Failed to load documents. Make sure the backend is running.');
      setLoading(false);
    }
  };

  const toggleCheck = (docName) => {
    setCheckedDocs(prev => ({ ...prev, [docName]: !prev[docName] }));
  };

  const handleUploadClick = (docName) => {
    if (fileInputRefs.current[docName]) {
      fileInputRefs.current[docName].click();
    }
  };

  const handleFileChange = async (docName, e) => {
    const file = e.target.files[0];
    if (!file) return;

    const allowed = ['application/pdf', 'image/png', 'image/jpeg', 'image/jpg'];
    if (!allowed.includes(file.type)) {
      alert('Only PDF, PNG, JPG files are allowed');
      return;
    }
    if (file.size > 16 * 1024 * 1024) {
      alert('File must be under 16MB');
      return;
    }

    setUploading(prev => ({ ...prev, [docName]: true }));

    const formData = new FormData();
    formData.append('file', file);
    formData.append('document_type', docName);

    try {
      const res = await fetch(`http://localhost:5000/api/claims/${claimId}/upload`, {
        method: 'POST',
        body: formData,
      });
      const result = await res.json();
      if (!res.ok) throw new Error(result.error || 'Upload failed');

      setUploadedFiles(prev => ({ ...prev, [docName]: file.name }));
      setCheckedDocs(prev => ({ ...prev, [docName]: true }));
    } catch (err) {
      alert('Upload failed: ' + err.message);
    } finally {
      setUploading(prev => ({ ...prev, [docName]: false }));
      e.target.value = '';
    }
  };

  const handleRemoveFile = (docName) => {
    setUploadedFiles(prev => { const n = { ...prev }; delete n[docName]; return n; });
    setCheckedDocs(prev => ({ ...prev, [docName]: false }));
  };

  const requiredDocs = documents.filter(d => d.is_required);
  const checkedRequired = requiredDocs.filter(d => checkedDocs[d.name]);
  const progress = requiredDocs.length > 0 ? (checkedRequired.length / requiredDocs.length) * 100 : 0;
  const allRequiredDone = requiredDocs.length > 0 && checkedRequired.length === requiredDocs.length;
  const missingRequired = requiredDocs.filter(d => !checkedDocs[d.name]);

  const progressColor = progress >= 80 ? '#22c55e' : progress >= 41 ? '#f59e0b' : '#ef4444';

  const icons = { health: '❤️', vehicle: '🚗', life: '🛡️', property: '🏠', travel: '✈️', crop: '🌾' };

  if (loading) {
    return (
      <div className="docs-loading">
        <div className="spinner" />
        <p>Loading documents...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="docs-error">
        <p>{error}</p>
        <button className="btn btn-primary" onClick={init}>Retry</button>
      </div>
    );
  }

  return (
    <div className="documents-page">
      <div className="docs-container">

        {/* Header */}
        <div className="docs-header">
          <button className="back-btn" onClick={() => navigate('/')}>← Back</button>
          <div className="docs-title">
            <span className="docs-icon">{icons[insuranceType] || '📋'}</span>
            <div>
              <h1>Documents Required</h1>
              <p className="docs-subtitle">{insuranceType.charAt(0).toUpperCase() + insuranceType.slice(1)} Insurance</p>
            </div>
          </div>
        </div>

        {/* Progress bar */}
        <div className="progress-section">
          <div className="progress-info">
            <span>{checkedRequired.length} of {requiredDocs.length} required documents ready</span>
            <span style={{ color: progressColor }}>{Math.round(progress)}%</span>
          </div>
          <div className="progress-track">
            <div className="progress-fill" style={{ width: `${progress}%`, backgroundColor: progressColor }} />
          </div>
        </div>

        {/* Missing warning */}
        {missingRequired.length > 0 && (
          <div className="missing-warning">
            <strong>⚠ {missingRequired.length} required document{missingRequired.length > 1 ? 's' : ''} still missing:</strong>
            <ul>
              {missingRequired.map(d => <li key={d.name}>{d.label}</li>)}
            </ul>
          </div>
        )}

        {/* Document list */}
        <div className="docs-list">
          {documents.map((doc) => {
            const isChecked = !!checkedDocs[doc.name];
            const isUploaded = !!uploadedFiles[doc.name];
            const isUploading = !!uploading[doc.name];

            return (
              <div key={doc.name} className={`doc-card ${isChecked ? 'doc-checked' : ''}`}>

                {/* Checkbox */}
                <div className="doc-left">
                  <div
                    className={`doc-checkbox ${isChecked ? 'checked' : ''}`}
                    onClick={() => toggleCheck(doc.name)}
                  >
                    {isChecked && <span>✓</span>}
                  </div>
                </div>

                {/* Info */}
                <div className="doc-body" onClick={() => toggleCheck(doc.name)}>
                  <div className="doc-name-row">
                    <span className="doc-name">{doc.label}</span>
                    <span className={`doc-badge ${doc.is_required ? 'badge-required' : 'badge-optional'}`}>
                      {doc.is_required ? 'Required' : 'Optional'}
                    </span>
                  </div>
                  <p className="doc-suggestion">{doc.suggestion}</p>
                  <div className="doc-meta">
                    <span className={`severity-dot severity-${doc.severity}`}>{doc.severity}</span>
                    <span className="weight-label">Score weight: {doc.weight}pts</span>
                  </div>
                </div>

                {/* Upload area */}
                <div className="doc-right" onClick={e => e.stopPropagation()}>
                  <input
                    type="file"
                    accept=".pdf,.png,.jpg,.jpeg"
                    style={{ display: 'none' }}
                    ref={el => fileInputRefs.current[doc.name] = el}
                    onChange={(e) => handleFileChange(doc.name, e)}
                  />

                  {isUploaded ? (
                    <div className="upload-done">
                      <span className="upload-check">✓</span>
                      <span className="upload-filename">{uploadedFiles[doc.name]}</span>
                      <button className="remove-btn" onClick={() => handleRemoveFile(doc.name)}>✕</button>
                    </div>
                  ) : (
                    <button
                      className="upload-btn"
                      onClick={() => handleUploadClick(doc.name)}
                      disabled={isUploading}
                    >
                      {isUploading ? 'Uploading...' : '📎 Upload'}
                    </button>
                  )}
                </div>

              </div>
            );
          })}
        </div>

        {/* Next button */}
        <div className="docs-footer">
          <button
            className={`next-btn ${allRequiredDone ? 'next-active' : 'next-disabled'}`}
            disabled={!allRequiredDone}
            onClick={() => navigate(`/details/${claimId}`, { state: { insuranceType } })}
          >
            Next: Fill Claim Details →
          </button>
        </div>

      </div>
    </div>
  );
}

export default Documents;
