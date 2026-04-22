import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getInsuranceTypes } from '../api';
import './Home.css';

function Home() {
  const [insuranceTypes, setInsuranceTypes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error,   setError]   = useState('');
  const navigate = useNavigate();

  useEffect(() => { loadInsuranceTypes(); }, []);

  const loadInsuranceTypes = async () => {
    try {
      const response = await getInsuranceTypes();
      setInsuranceTypes(response.data);
    } catch (err) {
      setError('Failed to load. Make sure the backend is running.');
    } finally {
      setLoading(false);
    }
  };

  const handleSelectType = (type) => {
    navigate(`/documents/${type.code}`);
  };

  const icons = {
    health: '❤️',
    vehicle: '🚗',
    life: '🛡️',
    property: '🏠',
    travel: '✈️',
    crop: '🌾'
  };

  return (
    <div className="home">
      <div className="container">
        <div className="header">
          <h1>ClaimGuard</h1>
          <p>Validate your insurance claims before submission</p>
        </div>

        {loading ? (
          <div style={{ textAlign: 'center', padding: '3rem', color: '#475569' }}>
            <div className="spinner" style={{ margin: '0 auto 1rem' }} />
            <p>Loading...</p>
          </div>
        ) : error ? (
          <div style={{ textAlign: 'center', padding: '3rem', color: '#ef4444' }}>
            <p>{error}</p>
            <button className="btn btn-primary" onClick={loadInsuranceTypes}>Retry</button>
          </div>
        ) : (
          <div className="insurance-grid">
            {insuranceTypes.map((type) => (
              <div key={type.id} className="insurance-card card" onClick={() => handleSelectType(type)}>
                <div className="insurance-icon">{icons[type.code] || '📋'}</div>
                <h3>{type.name}</h3>
                <p>Click to start validation</p>
              </div>
            ))}
          </div>
        )}

        <div className="dashboard-link">
          <button className="btn btn-secondary" onClick={() => navigate('/dashboard')}>
            View Past Claims
          </button>
        </div>
      </div>
    </div>
  );
}

export default Home;
