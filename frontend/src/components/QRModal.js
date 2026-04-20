import React, { useState, useEffect } from 'react';
import { getClaimQR } from '../api';
import './QRModal.css';

function QRModal({ claimId, onClose }) {
  const [qrData,   setQrData]   = useState(null);
  const [loading,  setLoading]  = useState(true);
  const [copied,   setCopied]   = useState(false);

  useEffect(() => {
    loadQR();
  }, [claimId]); // eslint-disable-line

  const loadQR = async () => {
    try {
      const res = await getClaimQR(claimId);
      setQrData(res.data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleCopyLink = () => {
    navigator.clipboard.writeText(qrData.claim_url);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = () => {
    const link = document.createElement('a');
    link.href = qrData.qr_image;
    link.download = `claimguard-qr-${claimId}.png`;
    link.click();
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-box" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Claim QR Code</h2>
          <button className="modal-close" onClick={onClose}>✕</button>
        </div>

        {loading ? (
          <div className="modal-loading">
            <div className="spinner" />
            <p>Generating QR code...</p>
          </div>
        ) : qrData ? (
          <>
            <div className="qr-info">
              <p>Share this QR code with hospitals, doctors, or insurers. Anyone who scans it will see your claim details instantly.</p>
            </div>

            <div className="qr-image-wrap">
              <img src={qrData.qr_image} alt="Claim QR Code" className="qr-image" />
            </div>

            <div className="qr-details">
              <div className="qr-detail-row">
                <span className="qd-label">Insurance Type</span>
                <span className="qd-value">{qrData.insurance_type}</span>
              </div>
              <div className="qr-detail-row">
                <span className="qd-label">Policy Number</span>
                <span className="qd-value">{qrData.policy_number}</span>
              </div>
              <div className="qr-detail-row">
                <span className="qd-label">Claim Score</span>
                <span className="qd-value" style={{
                  color: qrData.readiness_score >= 80 ? '#22c55e' : qrData.readiness_score >= 50 ? '#f59e0b' : '#ef4444'
                }}>
                  {qrData.readiness_score}/100 — {qrData.readiness_label}
                </span>
              </div>
              <div className="qr-detail-row">
                <span className="qd-label">Claim URL</span>
                <span className="qd-value qd-url">{qrData.claim_url}</span>
              </div>
            </div>

            <div className="qr-actions">
              <button className="qr-btn qr-btn-secondary" onClick={handleCopyLink}>
                {copied ? '✓ Copied!' : '🔗 Copy Link'}
              </button>
              <button className="qr-btn qr-btn-primary" onClick={handleDownload}>
                ⬇ Download QR
              </button>
            </div>

            <p className="qr-note">
              💡 Keep this QR code on your phone. Show it at the hospital or insurance office — they can scan it to instantly access your claim status.
            </p>
          </>
        ) : (
          <p className="modal-error">Failed to generate QR code.</p>
        )}
      </div>
    </div>
  );
}

export default QRModal;
