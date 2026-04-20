import React, { useState } from 'react';
import './FileUpload.css';

function FileUpload({ claimId, documentType, documentLabel, onUploadSuccess }) {
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');

  const handleFileSelect = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    // Validate file type
    const allowedTypes = ['application/pdf', 'image/png', 'image/jpeg', 'image/jpg'];
    if (!allowedTypes.includes(file.type)) {
      setError('Only PDF, PNG, and JPG files are allowed');
      return;
    }

    // Validate file size (16MB)
    if (file.size > 16 * 1024 * 1024) {
      setError('File size must be less than 16MB');
      return;
    }

    setError('');
    setUploading(true);

    const formData = new FormData();
    formData.append('file', file);
    formData.append('document_type', documentType);

    try {
      const response = await fetch(`http://localhost:5000/api/claims/${claimId}/upload`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Upload failed');
      }

      const data = await response.json();
      onUploadSuccess(data);
      setUploading(false);
    } catch (err) {
      setError(err.message);
      setUploading(false);
    }
  };

  return (
    <div className="file-upload">
      <input
        type="file"
        id={`upload-${documentType}`}
        accept=".pdf,.png,.jpg,.jpeg"
        onChange={handleFileSelect}
        disabled={uploading}
        style={{ display: 'none' }}
      />
      <label htmlFor={`upload-${documentType}`} className="upload-button">
        {uploading ? 'Uploading...' : '📎 Upload'}
      </label>
      {error && <span className="upload-error">{error}</span>}
    </div>
  );
}

export default FileUpload;
