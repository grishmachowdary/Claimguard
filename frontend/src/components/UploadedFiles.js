import React, { useState, useEffect } from 'react';
import axios from 'axios';
import api from '../api';
import './UploadedFiles.css';

function UploadedFiles({ claimId, documentType, onFilesChange }) {
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadFiles();
  }, [claimId]);

  const loadFiles = async () => {
    try {
      const response = await axios.get(`${api.defaults.baseURL}/claims/${claimId}/documents`);
      const filtered = response.data.filter(doc => doc.document_type === documentType);
      setFiles(filtered);
      setLoading(false);
      if (onFilesChange) {
        onFilesChange(filtered.length > 0);
      }
    } catch (error) {
      console.error('Error loading files:', error);
      setLoading(false);
    }
  };

  const handleDelete = async (docId) => {
    if (!window.confirm('Are you sure you want to delete this file?')) return;

    try {
      await axios.delete(`${api.defaults.baseURL}/claims/${claimId}/documents/${docId}`);
      loadFiles();
    } catch (error) {
      console.error('Error deleting file:', error);
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  if (loading) return null;
  if (files.length === 0) return null;

  return (
    <div className="uploaded-files">
      {files.map((file) => (
        <div key={file.id} className="uploaded-file">
          <div className="file-info">
            <span className="file-icon">📄</span>
            <div className="file-details">
              <span className="file-name">{file.file_name}</span>
              <span className="file-size">{formatFileSize(file.file_size)}</span>
            </div>
          </div>
          <button 
            className="delete-btn"
            onClick={() => handleDelete(file.id)}
            title="Delete file"
          >
            🗑️
          </button>
        </div>
      ))}
    </div>
  );
}

export default UploadedFiles;
