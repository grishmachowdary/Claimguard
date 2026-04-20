import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getInsuranceTypes } from '../api';
import './Home.css';

function Home() {
  const [insuranceTypes, setInsuranceTypes] = useState([]);
  const navigate = useNavigate();

  useEffect(() => {
    loadInsuranceTypes();
  }, []);

  const loadInsuranceTypes = async () => {
    try {
      const response = await getInsuranceTypes();
      setInsuranceTypes(response.data);
    } catch (error) {
      console.error('Error loading insurance types:', error);
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

        <div className="insurance-grid">
          {insuranceTypes.map((type) => (
            <div
              key={type.id}
              className="insurance-card card"
              onClick={() => handleSelectType(type)}
            >
              <div className="insurance-icon">{icons[type.code] || '📋'}</div>
              <h3>{type.name}</h3>
              <p>Click to start validation</p>
            </div>
          ))}
        </div>

        <div className="dashboard-link">
          <button 
            className="btn btn-secondary"
            onClick={() => navigate('/dashboard')}
          >
            View Past Claims
          </button>
        </div>
      </div>
    </div>
  );
}

export default Home;
