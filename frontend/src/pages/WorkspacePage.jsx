import React, { useState, useEffect } from 'react';
import {
  Bookmark,
  Download,
  ArrowRight,
  CheckCircle2,
  Phone,
  ShieldCheck,
  Mail,
  AlertCircle,
  Send,
} from 'lucide-react';
import { Link } from 'react-router-dom';
import { TennisAPI } from '../services/api';

export default function WorkspacePage() {
  const [players, setPlayers] = useState([]);
  const [exportNotice, setExportNotice] = useState(false);

  // User profile & phone OTP verification state
  const [user, setUser] = useState(() => TennisAPI.getCurrentUser());
  const [providers, setProviders] = useState(null);
  const [phoneInput, setPhoneInput] = useState(() => TennisAPI.getCurrentUser()?.phone_number || '');
  const [phoneOtpSent, setPhoneOtpSent] = useState(false);
  const [phoneOtpCode, setPhoneOtpCode] = useState('');
  const [phoneLoading, setPhoneLoading] = useState(false);
  const [phoneMessage, setPhoneMessage] = useState('');
  const [phoneError, setPhoneError] = useState('');

  useEffect(() => {
    async function loadData() {
      const res = await TennisAPI.getPlayers({ limit: 4 });
      setPlayers(res.items || []);

      const prov = await TennisAPI.getAuthProviders();
      setProviders(prov);

      if (localStorage.getItem('tip_token')) {
        try {
          const profile = await TennisAPI.getProfile();
          setUser(profile);
          if (profile.phone_number && !phoneInput) {
            setPhoneInput(profile.phone_number);
          }
        } catch {
          // Keep cached user if offline or token expired
        }
      }
    }
    loadData();
  }, []);

  const handleSendPhoneOTP = async (e) => {
    e.preventDefault();
    setPhoneError('');
    setPhoneMessage('');
    if (!/^\+[1-9]\d{6,14}$/.test(phoneInput.trim())) {
      setPhoneError('Enter phone number in international E.164 format (e.g. +919876543210 or +14155552671).');
      return;
    }

    setPhoneLoading(true);
    try {
      const res = await TennisAPI.sendPhoneOTP(phoneInput.trim());
      setPhoneOtpSent(true);
      setPhoneMessage(res.message || `SMS OTP sent via ${res.provider}.`);
    } catch (err) {
      setPhoneError(err.response?.data?.detail || 'Could not dispatch SMS OTP.');
    } finally {
      setPhoneLoading(false);
    }
  };

  const handleVerifyPhoneOTP = async (e) => {
    e.preventDefault();
    setPhoneError('');
    setPhoneMessage('');
    setPhoneLoading(true);
    try {
      const updatedUser = await TennisAPI.verifyPhoneOTP(phoneInput.trim(), phoneOtpCode.trim());
      setUser(updatedUser);
      setPhoneOtpSent(false);
      setPhoneOtpCode('');
      setPhoneMessage('Phone number verified and linked to your profile!');
    } catch (err) {
      setPhoneError(err.response?.data?.detail || 'Invalid or expired SMS OTP code.');
    } finally {
      setPhoneLoading(false);
    }
  };

  const handleDownloadCSV = () => {
    if (!players.length) return;
    const headers = ["Rank", "Name", "Country", "Country_Code", "Points", "Competitions_Played", "Tier"];
    const rows = players.map(p => [
      p.rank,
      `"${p.name}"`,
      `"${p.country}"`,
      p.country_code,
      p.points,
      p.competitions_played,
      `"${p.cluster_tier}"`
    ]);

    const csvContent = "data:text/csv;charset=utf-8," + [headers.join(","), ...rows.map(r => r.join(","))].join("\n");
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `tennis_intelligence_report_${new Date().toISOString().slice(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    setExportNotice(true);
    setTimeout(() => setExportNotice(false), 3000);
  };

  return (
    <div className="space-y-6">
      {/* HEADER */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-heading font-extrabold text-white tracking-tight">
            Personalized Tennis Analyst Workspace
          </h1>
          <p className="text-xs sm:text-sm text-textSecondary mt-1">
            Manage your verified identity, bookmarked players, and structured CSV exports.
          </p>
        </div>

        <button
          onClick={handleDownloadCSV}
          className="px-4 py-2.5 rounded-xl bg-tennis-green text-background-main font-bold text-xs hover:bg-tennis-greenHover transition flex items-center gap-2 shadow-lg shadow-tennis-green/20"
        >
          <Download className="w-4 h-4" /> Export CSV Report
        </button>
      </div>

      {exportNotice && (
        <div className="p-3.5 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-xs text-emerald-400 flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4" />
          <span>Analytical CSV dataset successfully generated and downloaded to your machine!</span>
        </div>
      )}

      {/* IDENTITY & PHONE VERIFICATION CARD */}
      <div className="glass-card p-6 rounded-2xl space-y-5 border border-slateBorder/70">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slateBorder/60 pb-4">
          <div className="flex items-center gap-3">
            {user?.avatar_url ? (
              <img
                src={user.avatar_url}
                alt={user.full_name || 'User'}
                className="w-11 h-11 rounded-full border border-tennis-green/50 object-cover"
              />
            ) : (
              <div className="w-11 h-11 rounded-full bg-tennis-green/15 border border-tennis-green/40 flex items-center justify-center text-tennis-green font-bold">
                {(user?.full_name || user?.email || 'TA').slice(0, 2).toUpperCase()}
              </div>
            )}
            <div>
              <h2 className="text-base font-bold text-white flex items-center gap-2">
                {user?.full_name || 'Guest Analyst'}
                {user?.auth_provider === 'google' && (
                  <span className="px-2 py-0.5 rounded-full text-[10px] font-mono bg-sky-500/15 text-sky-300 border border-sky-500/30">
                    Google Linked
                  </span>
                )}
              </h2>
              <p className="text-xs text-textMuted flex items-center gap-1.5">
                <Mail className="w-3.5 h-3.5" />
                <span>{user?.email || 'Not signed in — sign in to verify phone & sync favourites'}</span>
              </p>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            {user?.is_email_verified ? (
              <span className="px-2.5 py-1 rounded-lg bg-emerald-500/15 border border-emerald-500/30 text-emerald-300 text-xs font-medium inline-flex items-center gap-1.5">
                <ShieldCheck className="w-3.5 h-3.5" /> Email Verified
              </span>
            ) : (
              <Link
                to="/login"
                className="px-3 py-1.5 rounded-lg bg-tennis-green/15 border border-tennis-green/40 text-tennis-green text-xs font-semibold hover:bg-tennis-green/25 transition"
              >
                Sign In to Verify Account
              </Link>
            )}

            {user?.is_phone_verified && (
              <span className="px-2.5 py-1 rounded-lg bg-emerald-500/15 border border-emerald-500/30 text-emerald-300 text-xs font-medium inline-flex items-center gap-1.5">
                <Phone className="w-3.5 h-3.5" /> Phone Verified ({user.phone_number})
              </span>
            )}
          </div>
        </div>

        {/* Free SMS Phone Verification Form */}
        {user && localStorage.getItem('tip_token') && (
          <div className="space-y-3">
            <div className="flex items-center justify-between flex-wrap gap-2">
              <div className="flex items-center gap-2 text-xs font-semibold text-white">
                <Phone className="w-4 h-4 text-tennis-green" />
                <span>
                  {user.is_phone_verified ? 'Update Verified Phone Number' : 'Optional Free Phone Number Verification (SMS OTP)'}
                </span>
              </div>
              <span className="text-[11px] font-mono text-textMuted">
                Active Free Gateway: <span className="text-tennis-green uppercase">{providers?.sms_provider || 'textbelt'}</span>
              </span>
            </div>

            {phoneError && (
              <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-xs text-rose-400 flex items-start gap-2">
                <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
                <span>{phoneError}</span>
              </div>
            )}

            {phoneMessage && (
              <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-xs text-emerald-400 flex items-start gap-2">
                <CheckCircle2 className="w-4 h-4 shrink-0 mt-0.5" />
                <span>{phoneMessage}</span>
              </div>
            )}

            <form onSubmit={handleSendPhoneOTP} className="flex flex-col sm:flex-row gap-3">
              <input
                type="tel"
                placeholder="+919876543210 (International E.164 format)"
                value={phoneInput}
                onChange={(e) => setPhoneInput(e.target.value)}
                required
                className="flex-1 px-4 py-2.5 rounded-xl bg-background-main border border-slateBorder text-sm text-white focus:outline-none focus:border-tennis-green"
              />
              <button
                type="submit"
                disabled={phoneLoading}
                className="px-5 py-2.5 rounded-xl bg-white/10 hover:bg-white/15 border border-slateBorder text-white font-semibold text-xs transition inline-flex items-center justify-center gap-2"
              >
                <Send className="w-3.5 h-3.5 text-tennis-green" />
                {phoneLoading ? 'Sending...' : phoneOtpSent ? 'Resend SMS OTP' : 'Send Free SMS OTP'}
              </button>
            </form>

            {phoneOtpSent && (
              <form onSubmit={handleVerifyPhoneOTP} className="flex flex-col sm:flex-row gap-3 pt-1">
                <input
                  type="text"
                  inputMode="numeric"
                  maxLength={6}
                  placeholder="Enter 6-digit SMS OTP"
                  value={phoneOtpCode}
                  onChange={(e) => setPhoneOtpCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                  required
                  className="sm:w-56 px-4 py-2.5 rounded-xl bg-background-main border border-tennis-green/50 font-mono text-center tracking-widest text-sm text-tennis-green focus:outline-none focus:border-tennis-green"
                />
                <button
                  type="submit"
                  disabled={phoneLoading || phoneOtpCode.length !== 6}
                  className="px-5 py-2.5 rounded-xl bg-tennis-green text-background-main font-bold text-xs hover:bg-tennis-greenHover disabled:opacity-50 transition inline-flex items-center justify-center gap-2"
                >
                  <ShieldCheck className="w-4 h-4" /> Verify Phone Number
                </button>
              </form>
            )}

            <p className="text-[11px] text-textMuted leading-relaxed">
              Free SMS options supported: <strong>Textbelt</strong> (1 free SMS/day per IP built in),{' '}
              <strong>Textbee</strong> (300 free SMS/month via your Android phone SIM), or <strong>Twilio Trial</strong> via <code>.env</code>.
            </p>
          </div>
        )}
      </div>

      {/* SAVED PLAYERS SECTION */}
      <div className="glass-card p-6 rounded-2xl space-y-4">
        <div className="flex items-center justify-between border-b border-slateBorder/60 pb-3">
          <div className="flex items-center gap-2">
            <Bookmark className="w-4 h-4 text-tennis-green" />
            <h2 className="text-base font-bold text-white">Active Watchlist & Bookmarked Competitors</h2>
          </div>
          <span className="text-xs font-mono text-textMuted">{players.length} Competitors Saved</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {players.map((p) => (
            <div
              key={p.competitor_id}
              className="p-4 rounded-xl bg-background-card hover:bg-background-cardHover border border-slateBorder/60 flex items-center justify-between transition"
            >
              <div>
                <span className="font-mono text-xs font-bold text-tennis-green block">RANK #{p.rank}</span>
                <Link
                  to={`/app/players/${p.competitor_id}`}
                  className="font-bold text-base text-white hover:text-tennis-green transition"
                >
                  {p.name}
                </Link>
                <p className="text-xs text-textMuted">{p.country} • {p.points?.toLocaleString()} PTS</p>
              </div>

              <div className="flex items-center gap-2">
                <Link
                  to={`/app/players/${p.competitor_id}`}
                  className="p-2 rounded-lg bg-background-main text-textSecondary hover:text-white border border-slateBorder"
                  title="View Profile"
                >
                  <ArrowRight className="w-4 h-4" />
                </Link>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
