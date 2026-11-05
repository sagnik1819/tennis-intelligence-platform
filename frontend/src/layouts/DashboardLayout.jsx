import React, { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard,
  Users,
  GitCompare,
  Globe2,
  Trophy,
  Bot,
  Bookmark,
  FileText,
  ShieldCheck,
  Menu,
  X,
  Search,
  Bell,
  LogOut,
  LogIn,
  Activity
} from 'lucide-react';
import { TennisAPI } from '../services/api';

const NAV_ITEMS = [
  { name: 'Dashboard', path: '/app', icon: LayoutDashboard },
  { name: 'Player Explorer', path: '/app/players', icon: Users },
  { name: 'Player Comparison', path: '/app/compare', icon: GitCompare },
  { name: 'Global Map & Intel', path: '/app/global', icon: Globe2 },
  { name: 'Competitions & Venues', path: '/app/competitions', icon: Trophy },
  { name: 'AI Tennis Assistant', path: '/app/assistant', icon: Bot },
  { name: 'User Workspace', path: '/app/workspace', icon: Bookmark },
  { name: 'Reports & Analytics', path: '/app/reports', icon: FileText },
  { name: 'Data Quality & Admin', path: '/app/data-quality', icon: ShieldCheck },
];

export default function DashboardLayout({ children }) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();
  const user = TennisAPI.getCurrentUser();

  const handleLogout = () => {
    TennisAPI.logout();
    navigate('/');
  };

  return (
    <div className="flex h-screen bg-background-main text-textPrimary overflow-hidden font-sans">
      {/* SIDEBAR (Desktop) */}
      <aside className="hidden md:flex flex-col w-64 bg-background-secondary border-r border-slateBorder/60 z-20">
        {/* Brand */}
        <div className="h-16 flex items-center px-6 border-b border-slateBorder/60 gap-3">
          <div className="w-8 h-8 rounded-lg bg-tennis-green flex items-center justify-center text-background-main font-extrabold text-lg shadow-lg shadow-tennis-green/20">
            🎾
          </div>
          <div>
            <span className="font-heading font-extrabold text-base tracking-tight text-white block">TENNIS<span className="text-tennis-green">INTEL</span></span>
            <span className="text-[10px] text-textMuted uppercase tracking-wider block font-medium">Sports Intelligence</span>
          </div>
        </div>

        {/* Navigation Links */}
        <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path || (item.path !== '/app' && location.pathname.startsWith(item.path));
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-150 ${
                  isActive
                    ? 'bg-tennis-green/15 text-tennis-green border border-tennis-green/30 font-semibold shadow-sm'
                    : 'text-textSecondary hover:text-white hover:bg-background-card'
                }`}
              >
                <Icon className={`w-4 h-4 ${isActive ? 'text-tennis-green' : 'text-textMuted'}`} />
                {item.name}
              </Link>
            );
          })}
        </nav>

        {/* Sync Telemetry Badge & User Card */}
        <div className="p-4 border-t border-slateBorder/60 space-y-3">
          <div className="px-3 py-2 rounded-lg bg-background-card/80 border border-slateBorder/50 flex items-center justify-between text-xs">
            <span className="flex items-center gap-1.5 text-textSecondary">
              <span className="w-2 h-2 rounded-full bg-tennis-green animate-pulse"></span>
              SportRadar Sync
            </span>
            <span className="font-mono text-tennis-green font-medium">LIVE</span>
          </div>

          <div className="flex items-center justify-between pt-1">
            <div className="flex items-center gap-2.5 overflow-hidden">
              <div className="w-8 h-8 rounded-full bg-slateBorder flex items-center justify-center font-bold text-xs text-white uppercase">
                {user ? user.full_name?.charAt(0) : 'G'}
              </div>
              <div className="overflow-hidden">
                <p className="text-xs font-semibold truncate text-white">{user ? user.full_name : 'Guest Analyst'}</p>
                <p className="text-[10px] text-textMuted truncate">{user ? user.role : 'Read-Only'}</p>
              </div>
            </div>
            {user ? (
              <button
                onClick={handleLogout}
                title="Log out"
                className="p-1.5 text-textMuted hover:text-red-400 transition"
              >
                <LogOut className="w-4 h-4" />
              </button>
            ) : (
              <Link
                to="/login"
                title="Log in"
                className="p-1.5 text-tennis-green hover:text-white transition"
              >
                <LogIn className="w-4 h-4" />
              </Link>
            )}
          </div>
        </div>
      </aside>

      {/* MOBILE DRAWER */}
      {mobileMenuOpen && (
        <div className="fixed inset-0 z-50 md:hidden bg-background-main/90 backdrop-blur-md flex flex-col">
          <div className="h-16 flex items-center justify-between px-6 border-b border-slateBorder">
            <span className="font-heading font-bold text-lg text-white">TENNIS<span className="text-tennis-green">INTEL</span></span>
            <button onClick={() => setMobileMenuOpen(false)} className="p-2 text-textSecondary">
              <X className="w-6 h-6" />
            </button>
          </div>
          <nav className="p-4 space-y-2 flex-1">
            {NAV_ITEMS.map((item) => (
              <Link
                key={item.path}
                to={item.path}
                onClick={() => setMobileMenuOpen(false)}
                className="flex items-center gap-3 px-4 py-3 rounded-xl text-base font-medium text-textSecondary hover:text-white hover:bg-background-card"
              >
                <item.icon className="w-5 h-5 text-tennis-green" />
                {item.name}
              </Link>
            ))}
          </nav>
        </div>
      )}

      {/* MAIN CONTENT AREA */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* TOP NAVBAR */}
        <header className="h-16 bg-background-secondary/80 backdrop-blur-md border-b border-slateBorder/60 px-6 flex items-center justify-between gap-4 z-10">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setMobileMenuOpen(true)}
              className="md:hidden p-2 text-textSecondary hover:text-white"
            >
              <Menu className="w-5 h-5" />
            </button>
            <div className="hidden sm:flex items-center gap-2 text-xs font-mono text-textMuted bg-background-card px-3 py-1.5 rounded-lg border border-slateBorder/50">
              <Activity className="w-3.5 h-3.5 text-tennis-green" />
              <span>ATP & DOUBLES RANKINGS v3.2</span>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <Link
              to="/app/assistant"
              className="flex items-center gap-2 px-3.5 py-1.5 rounded-xl bg-tennis-green/10 text-tennis-green border border-tennis-green/30 text-xs font-semibold hover:bg-tennis-green hover:text-background-main transition shadow-sm"
            >
              <Bot className="w-3.5 h-3.5" />
              <span>Ask AI Analyst</span>
            </Link>
            <Link
              to="/"
              className="text-xs text-textSecondary hover:text-white font-medium px-2 py-1"
            >
              Marketing Site
            </Link>
          </div>
        </header>

        {/* BODY VIEWPORT */}
        <main className="flex-1 overflow-y-auto p-4 sm:p-6 lg:p-8">
          <div className="max-w-7xl mx-auto space-y-6">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
