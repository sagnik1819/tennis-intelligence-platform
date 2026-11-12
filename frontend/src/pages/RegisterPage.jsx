import React, { useState, useEffect } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import {
  Lock,
  Mail,
  User,
  Phone,
  ArrowRight,
  AlertCircle,
  CheckCircle2,
  ShieldCheck,
  RefreshCw,
  ArrowLeft,
  Info,
} from 'lucide-react';
import { TennisAPI } from '../services/api';
import GoogleSignInButton from '../components/auth/GoogleSignInButton';

export default function RegisterPage() {
  const navigate = useNavigate();
  const location = useLocation();

  // Step: 'form' | 'verify-otp'
  const [step, setStep] = useState(location.state?.verifyEmail ? 'verify-otp' : 'form');
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState(location.state?.verifyEmail || '');
  const [phoneNumber, setPhoneNumber] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [otp, setOtp] = useState('');
  const [cooldown, setCooldown] = useState(0);
  const [statusMessage, setStatusMessage] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [providers, setProviders] = useState({ gmail_otp_enabled: true, google_enabled: false });

  useEffect(() => {
    TennisAPI.getAuthProviders().then(setProviders);
  }, []);

  useEffect(() => {
    if (cooldown <= 0) return;
    const timer = setTimeout(() => setCooldown((c) => c - 1), 1000);
    return () => clearTimeout(timer);
  }, [cooldown]);

  const handleRegister = async (e) => {
    e.preventDefault();
    setError('');
    setStatusMessage('');

    if (password !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }

    if (phoneNumber.trim() && !/^\+[1-9]\d{6,14}$/.test(phoneNumber.trim())) {
      setError('Phone number must be in international E.164 format (e.g. +919876543210).');
      return;
    }

    setLoading(true);
    try {
      const res = await TennisAPI.registerWithEmail({
        full_name: fullName,
        email,
        password,
        phone_number: phoneNumber,
      });
      if (res.requires_verification) {
        setStatusMessage(res.message || `6-digit OTP sent to ${email}`);
        setStep('verify-otp');
        setCooldown(30);
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Registration failed. Please verify your details.');
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyOTP = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await TennisAPI.verifyEmailOTP(email, otp.trim());
      navigate('/app');
    } catch (err) {
      setError(err.response?.data?.detail || 'Invalid or expired OTP code.');
    } finally {
      setLoading(false);
    }
  };

  const handleResendOTP = async () => {
    if (cooldown > 0 || loading) return;
    setError('');
    setStatusMessage('');
    setLoading(true);
    try {
      const res = await TennisAPI.resendEmailOTP(email);
      setStatusMessage(res.message || `A new OTP was sent to ${email}.`);
      setCooldown(30);
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not resend OTP right now.');
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
          <h1 className="text-xl font-heading font-bold text-white">
            {step === 'form' ? 'Create Analyst Account' : 'Verify Your Gmail OTP'}
          </h1>
          <p className="text-xs text-textSecondary">
            {step === 'form'
              ? 'Register with Google or verify a real Gmail address with 6-digit OTP.'
              : `Enter the 6-digit verification code sent to ${email}`}
          </p>
        </div>

        {error && (
          <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-xs text-rose-400 flex items-start gap-2">
            <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        )}

        {statusMessage && (
          <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-xs text-emerald-400 flex items-start gap-2">
            <CheckCircle2 className="w-4 h-4 shrink-0 mt-0.5" />
            <span>{statusMessage}</span>
          </div>
        )}

        {step === 'form' ? (
          <>
            <GoogleSignInButton
              mode="signup"
              onSuccess={() => navigate('/app')}
              onError={(msg) => setError(msg)}
            />

            <div className="relative flex items-center py-1">
              <div className="flex-grow border-t border-slateBorder/70"></div>
              <span className="px-3 text-[10px] font-mono uppercase tracking-wider text-textMuted">
                Or register with Gmail OTP
              </span>
              <div className="flex-grow border-t border-slateBorder/70"></div>
            </div>

            {!providers.gmail_otp_enabled && (
              <div className="p-3 rounded-xl bg-sky-500/10 border border-sky-500/25 text-[11px] text-sky-300 flex items-start gap-2">
                <Info className="w-4 h-4 shrink-0 mt-0.5" />
                <span>
                  To send live Gmail OTPs, add <code className="text-white">SMTP_EMAIL</code> &amp;{' '}
                  <code className="text-white">SMTP_APP_PASSWORD</code> in <code className="text-white">.env</code>.
                </span>
              </div>
            )}

            <form onSubmit={handleRegister} className="space-y-3.5">
              <div className="space-y-1">
                <label className="text-xs font-mono uppercase text-textMuted block">Full Name</label>
                <div className="relative">
                  <User className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-textMuted" />
                  <input
                    type="text"
                    placeholder="Sagnik Das"
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    required
                    className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-background-main border border-slateBorder text-sm text-white focus:outline-none focus:border-tennis-green"
                  />
                </div>
              </div>

              <div className="space-y-1">
                <label className="text-xs font-mono uppercase text-textMuted block">Gmail / Email Address</label>
                <div className="relative">
                  <Mail className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-textMuted" />
                  <input
                    type="email"
                    placeholder="yourname@gmail.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-background-main border border-slateBorder text-sm text-white focus:outline-none focus:border-tennis-green"
                  />
                </div>
              </div>

              <div className="space-y-1">
                <label className="text-xs font-mono uppercase text-textMuted block">
                  Phone Number <span className="text-textMuted/60">(Optional, E.164 e.g. +919876543210)</span>
                </label>
                <div className="relative">
                  <Phone className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-textMuted" />
                  <input
                    type="tel"
                    placeholder="+919876543210"
                    value={phoneNumber}
                    onChange={(e) => setPhoneNumber(e.target.value)}
                    className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-background-main border border-slateBorder text-sm text-white focus:outline-none focus:border-tennis-green"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div className="space-y-1">
                  <label className="text-xs font-mono uppercase text-textMuted block">Password</label>
                  <div className="relative">
                    <Lock className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-textMuted" />
                    <input
                      type="password"
                      placeholder="••••••"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      required
                      minLength={6}
                      className="w-full pl-10 pr-3 py-2.5 rounded-xl bg-background-main border border-slateBorder text-sm text-white focus:outline-none focus:border-tennis-green"
                    />
                  </div>
                </div>

                <div className="space-y-1">
                  <label className="text-xs font-mono uppercase text-textMuted block">Confirm</label>
                  <div className="relative">
                    <Lock className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-textMuted" />
                    <input
                      type="password"
                      placeholder="••••••"
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      required
                      minLength={6}
                      className="w-full pl-10 pr-3 py-2.5 rounded-xl bg-background-main border border-slateBorder text-sm text-white focus:outline-none focus:border-tennis-green"
                    />
                  </div>
                </div>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full py-3 rounded-xl bg-tennis-green text-background-main font-bold text-sm hover:bg-tennis-greenHover transition shadow-lg shadow-tennis-green/20 flex items-center justify-center gap-2"
              >
                {loading ? 'Sending Gmail OTP...' : 'Send Verification OTP'} <ArrowRight className="w-4 h-4" />
              </button>
            </form>
          </>
        ) : (
          <form onSubmit={handleVerifyOTP} className="space-y-4">
            <div className="p-4 rounded-2xl bg-background-main border border-slateBorder text-center space-y-2">
              <ShieldCheck className="w-8 h-8 text-tennis-green mx-auto" />
              <p className="text-xs text-textSecondary">
                Check your Gmail inbox (and Spam folder) for a 6-digit code valid for 10 minutes.
              </p>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-mono uppercase text-textMuted block text-center">
                Enter 6-Digit OTP Code
              </label>
              <input
                type="text"
                inputMode="numeric"
                maxLength={6}
                placeholder="000000"
                value={otp}
                onChange={(e) => setOtp(e.target.value.replace(/\D/g, '').slice(0, 6))}
                required
                className="w-full py-3 rounded-xl bg-background-main border border-slateBorder text-center font-mono text-2xl tracking-[0.45em] text-tennis-green focus:outline-none focus:border-tennis-green"
              />
            </div>

            <button
              type="submit"
              disabled={loading || otp.length !== 6}
              className="w-full py-3 rounded-xl bg-tennis-green text-background-main font-bold text-sm hover:bg-tennis-greenHover disabled:opacity-50 transition shadow-lg shadow-tennis-green/20 flex items-center justify-center gap-2"
            >
              {loading ? 'Verifying OTP...' : 'Verify & Activate Account'} <ArrowRight className="w-4 h-4" />
            </button>

            <div className="flex items-center justify-between pt-1 text-xs">
              <button
                type="button"
                onClick={() => {
                  setStep('form');
                  setError('');
                  setStatusMessage('');
                }}
                className="text-textMuted hover:text-white inline-flex items-center gap-1"
              >
                <ArrowLeft className="w-3.5 h-3.5" /> Change Email
              </button>

              <button
                type="button"
                onClick={handleResendOTP}
                disabled={cooldown > 0 || loading}
                className="text-tennis-green hover:underline disabled:text-textMuted disabled:no-underline inline-flex items-center gap-1 font-semibold"
              >
                <RefreshCw className="w-3.5 h-3.5" />
                {cooldown > 0 ? `Resend in ${cooldown}s` : 'Resend OTP'}
              </button>
            </div>
          </form>
        )}

        <div className="pt-2 text-center text-xs text-textSecondary">
          Already have an account?{' '}
          <Link to="/login" className="text-tennis-green font-semibold hover:underline">
            Sign In
          </Link>
        </div>
      </div>
    </div>
  );
}
