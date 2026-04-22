import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { register } from '../api';
import { useAuth } from '../context/AuthContext';
import './Auth.css';

function Register() {
  const navigate = useNavigate();
  const { loginUser } = useAuth();

  const [form,    setForm]    = useState({ full_name: '', email: '', password: '', confirm: '', role: 'customer', company: '' });
  const [error,   setError]   = useState('');
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    setForm(prev => ({ ...prev, [e.target.name]: e.target.value }));
    setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.full_name || !form.email || !form.password) { setError('All fields are required'); return; }
    if (form.password.length < 6) { setError('Password must be at least 6 characters'); return; }
    if (form.password !== form.confirm) { setError('Passwords do not match'); return; }

    setLoading(true);
    try {
      const res = await register({ full_name: form.full_name, email: form.email, password: form.password, role: form.role, company: form.company });
      loginUser(res.data.token, res.data.user);
      // Redirect based on role
      if (form.role === 'agent')    navigate('/agent');
      else if (form.role === 'insurer') navigate('/insurer');
      else navigate('/');
    } catch (err) {
      setError(err.response?.data?.error || 'Registration failed. Try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-box">
        <div className="auth-logo">
          <span className="auth-logo-icon">🛡️</span>
          <h1>ClaimGuard</h1>
        </div>

        <h2>Create your account</h2>
        <p className="auth-sub">Start validating insurance claims the right way</p>

        <form onSubmit={handleSubmit} className="auth-form">
          <div className="auth-field">
            <label>Full Name</label>
            <input type="text" name="full_name" value={form.full_name} onChange={handleChange}
              placeholder="Your full name" className="auth-input" autoComplete="name" />
          </div>

          <div className="auth-field">
            <label>Email</label>
            <input type="email" name="email" value={form.email} onChange={handleChange}
              placeholder="you@example.com" className="auth-input" autoComplete="email" />
          </div>

          <div className="auth-field">
            <label>I am a</label>
            <div className="role-selector">
              {[
                { val: 'customer', label: '👤 Customer',  desc: 'Filing my own claims' },
                { val: 'agent',    label: '🤝 Agent',     desc: 'Managing client claims' },
                { val: 'insurer',  label: '🏛️ Insurer',   desc: 'Reviewing submitted claims' },
              ].map(r => (
                <div
                  key={r.val}
                  className={`role-option ${form.role === r.val ? 'role-selected' : ''}`}
                  onClick={() => setForm(prev => ({ ...prev, role: r.val }))}
                >
                  <span className="role-label">{r.label}</span>
                  <span className="role-desc">{r.desc}</span>
                </div>
              ))}
            </div>
          </div>

          {form.role === 'insurer' && (
            <div className="auth-field">
              <label>Company Name</label>
              <input type="text" name="company" value={form.company || ''} onChange={handleChange}
                placeholder="e.g. Star Health Insurance" className="auth-input" />
            </div>
          )}

          <div className="auth-field">
            <label>Password</label>
            <input type="password" name="password" value={form.password} onChange={handleChange}
              placeholder="Min 6 characters" className="auth-input" autoComplete="new-password" />
          </div>

          <div className="auth-field">
            <label>Confirm Password</label>
            <input type="password" name="confirm" value={form.confirm} onChange={handleChange}
              placeholder="Repeat your password" className="auth-input" autoComplete="new-password" />
          </div>

          {error && <p className="auth-error">⚠ {error}</p>}

          <button type="submit" className="auth-btn" disabled={loading}>
            {loading ? 'Creating account...' : 'Create Account'}
          </button>
        </form>

        <p className="auth-switch">
          Already have an account? <Link to="/login">Sign in</Link>
        </p>
      </div>
    </div>
  );
}

export default Register;
