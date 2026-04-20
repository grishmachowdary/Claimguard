import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import './Navbar.css';

function Navbar() {
  const { user, logoutUser } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logoutUser();
    navigate('/login');
  };

  if (!user) return null;

  return (
    <nav className="navbar">
      <div className="navbar-inner">
        <div className="navbar-brand" onClick={() => navigate('/')}>
          <span>🛡️</span>
          <span className="navbar-name">ClaimGuard</span>
        </div>
        <div className="navbar-right">
          <button className="navbar-link" onClick={() => navigate('/dashboard')}>My Claims</button>
          <div className="navbar-user">
            <span className="navbar-avatar">{user.full_name.charAt(0).toUpperCase()}</span>
            <span className="navbar-username">{user.full_name}</span>
          </div>
          <button className="navbar-logout" onClick={handleLogout}>Sign Out</button>
        </div>
      </div>
    </nav>
  );
}

export default Navbar;
