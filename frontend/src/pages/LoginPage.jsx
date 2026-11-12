import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Lock, Mail, ArrowRight, AlertCircle, ShieldCheck } from 'lucide-react';
import { TennisAPI } from '../services/api';
import GoogleSignInButton from '../components/auth/GoogleSignInButton';

export default function LoginPage() {
  const [email, setEmail] = useState('analyst@tennisintel.com');
  const [password, setPassword] = useState('Analyst@123');
  const [error, setError] = useState('');
  const [needsVerification, setNeedsVerification] = useState(false);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setNeedsVerification(false);
    try {
      await TennisAPI.login(email, password);
      navigate('/app');
    } catch (err) {
      const detail = err.response?.data?.detail;
      if (err.response?.status === 403 && detail === 'EMAIL_NOT_VERIFIED') {
        setNeedsVerification(true);
        setError('Your email is not verified yet. Please verify with your 6-digit Gmail OTP.');
      } else {
        setError(detail || 'Invalid email or password. Please verify credentials.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleGoVerifyOTP = async () => {
    setLoading(true);
    setError('');
    try {
      await TennisAPI.resendEmailOTP(email);
      navigate('/register', { state: { verifyEmail: email } });
    } catch (err) {
      const status = err.response?.status;
      if (status === 429) {
        // Already sent recently; take them right to the OTP box
        navigate('/register', { state: { verifyEmail: email } });
      } else {
        setError(err.response?.data?.detail || 'Could not send OTP to this Gmail.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background-main flex items-center justify-center p-6 relative overflow-hidden font-sans">
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-tennis-green/10 rounded-full blur-[120px] pointer-events-none"></div>

      <div className="glass-card max-w-md w-full p-8 rounded-3xl space-y-6 relative z-10 border border-slateBorder/80">
        <div className="text-center space-y-2">
          <Link to="/" className="inline-flex items-center gap-2 mb-2">
            <span className="text-2xl">🎾</span>
            <span className="font-heading font-black text-2xl text-white">
              TENNIS<span className="text-tennis-green">INTEL</span>
            </span>
          </Link>
          <h1 className="text-xl font-heading font-bold text-white">Sign In to Platform</h1>
          <p className="text-xs text-textSecondary">Sign in with Google, your verified Gmail, or demo credentials.</p>
        </div>

        {error && (
          <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-xs text-rose-400 space-y-2">
            <div className="flex items-start gap-2">
              <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
            {needsVerification && (
              <button
                type="button"
                onClick={handleGoVerifyOTP}
                disabled={loading}
                className="w-full py-2 px-3 rounded-lg bg-tennis-green text-background-main font-bold text-xs flex items-center justify-center gap-1.5 hover:bg-tennis-greenHover transition"
              >
                <ShieldCheck className="w-4 h-4" /> Send OTP &amp; Verify Gmail Now
              </button>
            )}
          </div>
        )}

        <GoogleSignInButton
          mode="signin"
          onSuccess={() => navigate('/app')}
          onError={(msg) => setError(msg)}
        />

        <div className="relative flex items-center py-0.5">
          <div className="flex-grow border-t border-slateBorder/70"></div>
          <span className="px-3 text-[10px] font-mono uppercase tracking-wider text-textMuted">
            Or sign in with email
          </span>
          <div className="flex-grow border-t border-slateBorder/70"></div>
        </div>

        <form onSubmit={handleLogin} className="space-y-4">
          <div className="space-y-1.5">
            <label className="text-xs font-mono uppercase text-textMuted block">Email Address</label>
            <div className="relative">
              <Mail className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-textMuted" />
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-background-main border border-slateBorder text-sm text-white focus:outline-none focus:border-tennis-green"
              />
            </div>
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-mono uppercase text-textMuted block">Password</label>
            <div className="relative">
              <Lock className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-textMuted" />
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-background-main border border-slateBorder text-sm text-white focus:outline-none focus:border-tennis-green"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 rounded-xl bg-tennis-green text-background-main font-bold text-sm hover:bg-tennis-greenHover transition shadow-lg shadow-tennis-green/20 flex items-center justify-center gap-2"
          >
            {loading ? 'Authenticating...' : 'Sign In'} <ArrowRight className="w-4 h-4" />
          </button>
        </form>

        <div className="pt-1 space-y-2 text-center text-xs">
          <div className="text-textSecondary">
            New to TennisIntel?{' '}
            <Link to="/register" className="text-tennis-green font-semibold hover:underline">
              Create Verified Account
            </Link>
          </div>
          <div className="text-textMuted">
            <span>Demo Credentials: </span>
            <code className="text-tennis-green">analyst@tennisintel.com</code> / <code className="text-tennis-green">Analyst@123</code>
          </div>
        </div>
      </div>
    </div>
  );
}
