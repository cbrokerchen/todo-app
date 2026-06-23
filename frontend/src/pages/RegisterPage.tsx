import { useState } from 'react';
import type { FormEvent } from 'react';
import { Link, useNavigate, Navigate } from 'react-router-dom';
import { useAuth } from '../AuthContext';

export default function RegisterPage() {
  const { register, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);

    if (password !== confirmPassword) {
      setError('兩次輸入的密碼不一致');
      return;
    }
    if (password.length < 6) {
      setError('密碼長度至少需要 6 個字元');
      return;
    }

    setSubmitting(true);
    try {
      await register(username, password);
      navigate('/dashboard', { replace: true });
    } catch (err: unknown) {
      const message =
        extractErrorMessage(err) ?? '註冊失敗，請再試一次';
      setError(message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="auth-container">
      <div className="auth-card">
        <h1>建立新帳號</h1>
        <p className="auth-subtitle">註冊後即可開始管理待辦事項</p>
        <form onSubmit={handleSubmit} className="auth-form">
          <label>
            <span>帳號</span>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              minLength={3}
              maxLength={64}
              autoComplete="username"
              autoFocus
            />
          </label>
          <label>
            <span>密碼</span>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={6}
              autoComplete="new-password"
            />
          </label>
          <label>
            <span>確認密碼</span>
            <input
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
              minLength={6}
              autoComplete="new-password"
            />
          </label>
          {error && <div className="error-banner">{error}</div>}
          <button type="submit" disabled={submitting} className="btn-primary">
            {submitting ? '註冊中…' : '註冊'}
          </button>
        </form>
        <p className="auth-footer">
          已經有帳號了？<Link to="/login">登入</Link>
        </p>
      </div>
    </div>
  );
}

function extractErrorMessage(err: unknown): string | null {
  if (typeof err === 'object' && err !== null && 'response' in err) {
    const response = (err as { response?: { data?: { detail?: string } } }).response;
    if (response?.data?.detail) return response.data.detail;
  }
  return null;
}
