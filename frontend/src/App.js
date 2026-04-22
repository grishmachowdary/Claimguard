import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import ErrorBoundary from './components/ErrorBoundary';
import { AuthProvider } from './context/AuthContext';
import { LanguageProvider } from './context/LanguageContext';
import ProtectedRoute from './components/ProtectedRoute';
import Navbar from './components/Navbar';
import Home from './pages/Home';
import Login from './pages/Login';
import Register from './pages/Register';
import Documents from './pages/Documents';
import Details from './pages/Details';
import Report from './pages/Report';
import Dashboard from './pages/Dashboard';
import AgentDashboard from './pages/AgentDashboard';
import InsurerPortal from './pages/InsurerPortal';
import './App.css';

function App() {
  return (
    <ErrorBoundary>
      <AuthProvider>
        <LanguageProvider>
          <Router>
            <Navbar />
            <Routes>
          {/* Public routes */}
          <Route path="/login"    element={<Login />} />
          <Route path="/register" element={<Register />} />

          {/* Protected routes */}
          <Route path="/" element={<ProtectedRoute><Home /></ProtectedRoute>} />
          <Route path="/documents/:insuranceType" element={<ProtectedRoute><Documents /></ProtectedRoute>} />
          <Route path="/details/:claimId"         element={<ProtectedRoute><Details /></ProtectedRoute>} />
          <Route path="/report/:claimId"          element={<ProtectedRoute><Report /></ProtectedRoute>} />
          <Route path="/dashboard"                element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
          <Route path="/agent"                    element={<ProtectedRoute><AgentDashboard /></ProtectedRoute>} />
          <Route path="/insurer"                  element={<ProtectedRoute><InsurerPortal /></ProtectedRoute>} />

          {/* Fallback */}
          <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
          </Router>
        </LanguageProvider>
      </AuthProvider>
    </ErrorBoundary>
  );
}

export default App;
