import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, Bot, ShieldCheck, Zap, Activity, Globe, Trophy, Sparkles } from 'lucide-react';

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-background-main text-textPrimary flex flex-col font-sans selection:bg-tennis-green selection:text-background-main">
      {/* HEADER */}
      <header className="h-20 border-b border-slateBorder/50 px-6 sm:px-12 flex items-center justify-between bg-background-main/80 backdrop-blur-md sticky top-0 z-50">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-tennis-green flex items-center justify-center text-background-main font-black text-xl shadow-lg shadow-tennis-green/20">
            🎾
          </div>
          <span className="font-heading font-extrabold text-xl tracking-tight text-white">
            TENNIS<span className="text-tennis-green">INTEL</span>
          </span>
        </div>

        <div className="flex items-center gap-4">
          <Link
            to="/login"
            className="text-sm font-medium text-textSecondary hover:text-white px-3 py-2 transition"
          >
            Sign In
          </Link>
          <Link
            to="/app"
            className="px-5 py-2.5 rounded-xl bg-tennis-green text-background-main text-sm font-bold hover:bg-tennis-greenHover transition shadow-lg shadow-tennis-green/20 flex items-center gap-2"
          >
            Launch Platform <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </header>

      {/* HERO SECTION */}
      <section className="relative pt-20 pb-24 px-6 sm:px-12 overflow-hidden flex-1 flex flex-col justify-center">
        {/* Subtle Ambient Light Gradients */}
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[650px] h-[350px] bg-tennis-green/10 rounded-full blur-[140px] pointer-events-none"></div>
        <div className="absolute top-1/3 right-10 w-[450px] h-[300px] bg-cyanAccent/10 rounded-full blur-[120px] pointer-events-none"></div>

        <div className="max-w-5xl mx-auto text-center space-y-8 relative z-10">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-background-card border border-tennis-green/30 text-xs font-mono text-tennis-green">
            <Sparkles className="w-3.5 h-3.5" />
            <span>AI-POWERED TENNIS SPORTS INTELLIGENCE & ANALYTICS</span>
          </div>

          <h1 className="text-4xl sm:text-6xl lg:text-7xl font-heading font-extrabold tracking-tight leading-[1.1]">
            See Beyond The <span className="tennis-gradient-text">Rankings.</span>
          </h1>

          <p className="max-w-2xl mx-auto text-base sm:text-xl text-textSecondary leading-relaxed">
            Unify official SportRadar tennis feeds, 5-axis ML player trait profiling, automated smart comparisons, and data-grounded AI sports analytics in one high-performance SaaS platform.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-4">
            <Link
              to="/app"
              className="w-full sm:w-auto px-8 py-3.5 rounded-xl bg-tennis-green text-background-main font-bold text-base hover:bg-tennis-greenHover transition shadow-xl shadow-tennis-green/25 flex items-center justify-center gap-2.5"
            >
              Explore Intelligence Dashboard <ArrowRight className="w-5 h-5" />
            </Link>
            <Link
              to="/app/assistant"
              className="w-full sm:w-auto px-8 py-3.5 rounded-xl bg-background-card border border-slateBorder hover:border-tennis-green/40 text-white font-medium text-base transition flex items-center justify-center gap-2"
            >
              <Bot className="w-5 h-5 text-tennis-green" /> Ask AI Analyst
            </Link>
          </div>

          {/* Interactive Metric Preview Ticker */}
          <div className="pt-12 grid grid-cols-2 md:grid-cols-4 gap-4 max-w-4xl mx-auto text-left">
            <div className="glass-card p-5 rounded-2xl">
              <span className="text-xs text-textMuted uppercase font-mono block">Top Seed Points</span>
              <span className="text-2xl sm:text-3xl font-heading font-bold text-white mt-1 block">7,510 <span className="text-xs text-tennis-green font-mono">PTS</span></span>
              <span className="text-xs text-textSecondary mt-1 block">Mate Pavic (Croatia)</span>
            </div>
            <div className="glass-card p-5 rounded-2xl">
              <span className="text-xs text-textMuted uppercase font-mono block">Data Reliability</span>
              <span className="text-2xl sm:text-3xl font-heading font-bold text-tennis-green mt-1 block">100%</span>
              <span className="text-xs text-textSecondary mt-1 block">Zero Missing Key Metrics</span>
            </div>
            <div className="glass-card p-5 rounded-2xl">
              <span className="text-xs text-textMuted uppercase font-mono block">ML Trait Radar</span>
              <span className="text-2xl sm:text-3xl font-heading font-bold text-cyanAccent mt-1 block">5-Axis</span>
              <span className="text-xs text-textSecondary mt-1 block">Consistency & Momentum</span>
            </div>
            <div className="glass-card p-5 rounded-2xl">
              <span className="text-xs text-textMuted uppercase font-mono block">AI Grounding</span>
              <span className="text-2xl sm:text-3xl font-heading font-bold text-white mt-1 block">Grounded</span>
              <span className="text-xs text-textSecondary mt-1 block">Zero Hallucinations</span>
            </div>
          </div>
        </div>
      </section>

      {/* CORE CAPABILITIES GRID */}
      <section className="py-20 px-6 sm:px-12 bg-background-secondary/50 border-t border-slateBorder/60">
        <div className="max-w-6xl mx-auto space-y-12">
          <div className="text-center space-y-3">
            <span className="text-xs font-mono uppercase text-tennis-green tracking-wider">Engineered For Performance</span>
            <h2 className="text-3xl sm:text-4xl font-heading font-bold text-white">6 Distinct Intelligence Capabilities</h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="glass-card p-6 rounded-2xl space-y-3">
              <div className="w-10 h-10 rounded-xl bg-tennis-green/10 border border-tennis-green/30 flex items-center justify-center text-tennis-green">
                <Activity className="w-5 h-5" />
              </div>
              <h3 className="text-lg font-bold text-white">1. Player Intelligence Profile</h3>
              <p className="text-sm text-textSecondary leading-relaxed">
                Complete player dossiers with 5-axis ML radar traits (Consistency, Power Volume, Stamina, Momentum, Efficiency).
              </p>
            </div>

            <div className="glass-card p-6 rounded-2xl space-y-3">
              <div className="w-10 h-10 rounded-xl bg-cyanAccent/10 border border-cyanAccent/30 flex items-center justify-center text-cyanAccent">
                <Zap className="w-5 h-5" />
              </div>
              <h3 className="text-lg font-bold text-white">2. Smart Head-to-Head Comparison</h3>
              <p className="text-sm text-textSecondary leading-relaxed">
                Side-by-side metric tables, advantage indicators, dual radar overlays, and AI comparative breakdowns.
              </p>
            </div>

            <div className="glass-card p-6 rounded-2xl space-y-3">
              <div className="w-10 h-10 rounded-xl bg-tennis-green/10 border border-tennis-green/30 flex items-center justify-center text-tennis-green">
                <Bot className="w-5 h-5" />
              </div>
              <h3 className="text-lg font-bold text-white">3. Data-Grounded AI Assistant</h3>
              <p className="text-sm text-textSecondary leading-relaxed">
                Chat with an intelligent analyst querying parameterized database tools. Citations provided for every stat.
              </p>
            </div>

            <div className="glass-card p-6 rounded-2xl space-y-3">
              <div className="w-10 h-10 rounded-xl bg-cyanAccent/10 border border-cyanAccent/30 flex items-center justify-center text-cyanAccent">
                <Globe className="w-5 h-5" />
              </div>
              <h3 className="text-lg font-bold text-white">4. Global Tennis Intelligence</h3>
              <p className="text-sm text-textSecondary leading-relaxed">
                Geographic player distribution, national strength index, and country-level tournament analytics.
              </p>
            </div>

            <div className="glass-card p-6 rounded-2xl space-y-3">
              <div className="w-10 h-10 rounded-xl bg-tennis-green/10 border border-tennis-green/30 flex items-center justify-center text-tennis-green">
                <ShieldCheck className="w-5 h-5" />
              </div>
              <h3 className="text-lg font-bold text-white">5. Data Freshness & Quality Center</h3>
              <p className="text-sm text-textSecondary leading-relaxed">
                Real-time sync telemetry, duplicate detection counters, and column completeness monitoring.
              </p>
            </div>

            <div className="glass-card p-6 rounded-2xl space-y-3">
              <div className="w-10 h-10 rounded-xl bg-cyanAccent/10 border border-cyanAccent/30 flex items-center justify-center text-cyanAccent">
                <Trophy className="w-5 h-5" />
              </div>
              <h3 className="text-lg font-bold text-white">6. Personalized Analyst Workspace</h3>
              <p className="text-sm text-textSecondary leading-relaxed">
                Bookmark competitors, save comparative sets, and export formatted CSV reports on demand.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* FOOTER */}
      <footer className="border-t border-slateBorder/60 py-8 px-6 sm:px-12 bg-background-main flex flex-col sm:flex-row items-center justify-between text-xs text-textMuted gap-4">
        <div>
          © 2026 Tennis Intelligence Platform. Built with FastAPI, PostgreSQL, Scikit-Learn & React.
        </div>
        <div className="flex gap-6 font-mono">
          <Link to="/app" className="hover:text-tennis-green">Launch Dashboard</Link>
          <Link to="/app/data-quality" className="hover:text-tennis-green">Sync Health</Link>
          <a href="http://localhost:8000/docs" target="_blank" rel="noreferrer" className="hover:text-tennis-green">Swagger API</a>
        </div>
      </footer>
    </div>
  );
}
