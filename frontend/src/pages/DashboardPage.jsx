import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  Users,
  Trophy,
  Globe,
  Activity,
  ArrowUpRight,
  Sparkles,
  Bot,
  GitCompare,
  TrendingUp,
  RefreshCw
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer
} from 'recharts';
import { TennisAPI } from '../services/api';
import PlayerRadarChart from '../components/charts/PlayerRadarChart';

export default function DashboardPage() {
  const [kpis, setKpis] = useState(null);
  const [topPlayers, setTopPlayers] = useState([]);
  const [countryData, setCountryData] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      setLoading(true);
      const [kpiRes, playerRes, countryRes] = await Promise.all([
        TennisAPI.getKPIs(),
        TennisAPI.getPlayers({ limit: 5 }),
        TennisAPI.getCountries()
      ]);
      setKpis(kpiRes);
      setTopPlayers(playerRes.items || []);
      setCountryData(countryRes || []);
      setLoading(false);
    }
    loadData();
  }, []);

  const topPlayer = topPlayers[0] || null;

  return (
    <div className="space-y-6">
      {/* PAGE HEADER */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-heading font-extrabold text-white tracking-tight">
            Executive Sports Intelligence Dashboard
          </h1>
          <p className="text-xs sm:text-sm text-textSecondary mt-1">
            Real-time ATP doubles rankings, ML player trait distributions & global tournament data.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Link
            to="/app/compare"
            className="px-3.5 py-2 rounded-xl bg-background-card hover:bg-background-cardHover border border-slateBorder text-xs font-semibold text-white transition flex items-center gap-1.5"
          >
            <GitCompare className="w-3.5 h-3.5 text-tennis-green" /> Compare Players
          </Link>
          <Link
            to="/app/assistant"
            className="px-4 py-2 rounded-xl bg-tennis-green hover:bg-tennis-greenHover text-background-main text-xs font-bold transition flex items-center gap-1.5 shadow-md shadow-tennis-green/20"
          >
            <Bot className="w-4 h-4" /> Ask AI Analyst
          </Link>
        </div>
      </div>

      {/* 4 TOP KPI CARDS */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="glass-card p-5 rounded-2xl relative overflow-hidden">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono uppercase text-textMuted">Total Competitors</span>
            <div className="w-8 h-8 rounded-lg bg-tennis-green/10 flex items-center justify-center text-tennis-green">
              <Users className="w-4 h-4" />
            </div>
          </div>
          <p className="text-3xl font-heading font-extrabold text-white mt-3">
            {kpis ? kpis.total_players : '--'}
          </p>
          <div className="flex items-center gap-1 mt-2 text-xs text-tennis-green">
            <TrendingUp className="w-3.5 h-3.5" />
            <span>100% Verified Profiles</span>
          </div>
        </div>

        <div className="glass-card p-5 rounded-2xl relative overflow-hidden">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono uppercase text-textMuted">Tournaments & Venues</span>
            <div className="w-8 h-8 rounded-lg bg-cyanAccent/10 flex items-center justify-center text-cyanAccent">
              <Trophy className="w-4 h-4" />
            </div>
          </div>
          <p className="text-3xl font-heading font-extrabold text-white mt-3">
            {kpis ? `${kpis.total_competitions} / ${kpis.total_venues}` : '--'}
          </p>
          <div className="flex items-center gap-1 mt-2 text-xs text-textSecondary">
            <span>ATP, Grand Slam & Complexes</span>
          </div>
        </div>

        <div className="glass-card p-5 rounded-2xl relative overflow-hidden">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono uppercase text-textMuted">Countries Represented</span>
            <div className="w-8 h-8 rounded-lg bg-tennis-green/10 flex items-center justify-center text-tennis-green">
              <Globe className="w-4 h-4" />
            </div>
          </div>
          <p className="text-3xl font-heading font-extrabold text-white mt-3">
            {kpis ? kpis.countries_represented : '--'}
          </p>
          <div className="flex items-center gap-1 mt-2 text-xs text-textSecondary">
            <span>Global Coverage</span>
          </div>
        </div>

        <div className="glass-card p-5 rounded-2xl relative overflow-hidden">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono uppercase text-textMuted">Leader Points Volume</span>
            <div className="w-8 h-8 rounded-lg bg-tennis-green/10 flex items-center justify-center text-tennis-green">
              <Sparkles className="w-4 h-4" />
            </div>
          </div>
          <p className="text-3xl font-heading font-extrabold text-tennis-green mt-3 font-mono">
            {kpis ? `${kpis.highest_points.toLocaleString()} PTS` : '--'}
          </p>
          <div className="flex items-center gap-1 mt-2 text-xs text-textSecondary truncate">
            <span>Leader: {kpis ? kpis.highest_points_player : '--'}</span>
          </div>
        </div>
      </div>

      {/* MAIN TWO-COLUMN SECTION */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* LEFT: LEADERBOARD TABLE (2 Columns) */}
        <div className="lg:col-span-2 glass-card p-6 rounded-2xl space-y-4">
          <div className="flex items-center justify-between border-b border-slateBorder/60 pb-3">
            <div className="flex items-center gap-2">
              <Trophy className="w-4 h-4 text-tennis-green" />
              <h2 className="text-base font-bold text-white">Top Official Circuit Competitors</h2>
            </div>
            <Link
              to="/app/players"
              className="text-xs font-semibold text-tennis-green hover:underline flex items-center gap-1"
            >
              View All Players <ArrowUpRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="text-[11px] font-mono uppercase text-textMuted border-b border-slateBorder/40">
                  <th className="py-2.5 px-3">Rank</th>
                  <th className="py-2.5 px-3">Competitor</th>
                  <th className="py-2.5 px-3">Country</th>
                  <th className="py-2.5 px-3">Points</th>
                  <th className="py-2.5 px-3">Movement</th>
                  <th className="py-2.5 px-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slateBorder/30">
                {topPlayers.map((player) => (
                  <tr key={player.competitor_id} className="hover:bg-background-card/50 transition">
                    <td className="py-3 px-3">
                      <span className="font-mono font-bold text-sm text-tennis-green">#{player.rank}</span>
                    </td>
                    <td className="py-3 px-3">
                      <Link
                        to={`/app/players/${player.competitor_id}`}
                        className="font-semibold text-white hover:text-tennis-green transition"
                      >
                        {player.name}
                      </Link>
                      <span className="text-[11px] text-textMuted block">{player.cluster_tier}</span>
                    </td>
                    <td className="py-3 px-3 text-textSecondary">
                      {player.country} <span className="text-xs font-mono text-textMuted">({player.country_code})</span>
                    </td>
                    <td className="py-3 px-3 font-mono font-bold text-white">
                      {player.points.toLocaleString()}
                    </td>
                    <td className="py-3 px-3">
                      {player.movement > 0 ? (
                        <span className="text-xs font-mono px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 font-bold">
                          +{player.movement} ▲
                        </span>
                      ) : player.movement < 0 ? (
                        <span className="text-xs font-mono px-2 py-0.5 rounded bg-rose-500/10 text-rose-400 font-bold">
                          {player.movement} ▼
                        </span>
                      ) : (
                        <span className="text-xs font-mono px-2 py-0.5 rounded bg-slate-500/10 text-slate-400">
                          0 ●
                        </span>
                      )}
                    </td>
                    <td className="py-3 px-3 text-right">
                      <Link
                        to={`/app/players/${player.competitor_id}`}
                        className="text-xs px-2.5 py-1 rounded-lg bg-background-card hover:bg-background-cardHover text-textSecondary hover:text-white border border-slateBorder/60 font-medium transition"
                      >
                        Profile
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* RIGHT: SPOTLIGHT RADAR TRAIT CARD (1 Column) */}
        <div className="glass-card p-6 rounded-2xl flex flex-col justify-between space-y-4">
          <div className="border-b border-slateBorder/60 pb-3 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Activity className="w-4 h-4 text-tennis-green" />
              <h2 className="text-base font-bold text-white">Top Seed ML Trait Radar</h2>
            </div>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-tennis-green/10 text-tennis-green">
              K-Means 5-Axis
            </span>
          </div>

          {topPlayer ? (
            <div className="space-y-4">
              <div className="text-center">
                <h3 className="font-heading font-extrabold text-lg text-white">{topPlayer.name}</h3>
                <p className="text-xs text-textSecondary">{topPlayer.country} • World Rank #{topPlayer.rank}</p>
              </div>

              {/* Radar Chart */}
              <PlayerRadarChart traits={topPlayer.traits} playerName={topPlayer.name} />

              <div className="p-3 rounded-xl bg-background-card/80 border border-slateBorder/50 text-xs text-textSecondary leading-relaxed">
                <span className="font-bold text-tennis-green">AI Trait Insight: </span>
                Demonstrates high baseline consistency ({topPlayer.traits?.consistency}/100) and power volume ({topPlayer.traits?.power_volume}/100).
              </div>
            </div>
          ) : (
            <div className="h-64 flex items-center justify-center text-textMuted text-xs">
              Loading radar metrics...
            </div>
          )}
        </div>
      </div>

      {/* COUNTRY DISTRIBUTION BAR CHART */}
      <div className="glass-card p-6 rounded-2xl space-y-4">
        <div className="flex items-center justify-between border-b border-slateBorder/60 pb-3">
          <div className="flex items-center gap-2">
            <Globe className="w-4 h-4 text-cyanAccent" />
            <h2 className="text-base font-bold text-white">National Player Count & Points Concentration</h2>
          </div>
          <span className="text-xs text-textMuted font-mono">Aggregated via SQL Analytics</span>
        </div>

        <div className="w-full h-64">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={countryData}>
              <XAxis dataKey="country" stroke="#64748B" tick={{ fill: '#94A3B8', fontSize: 11 }} />
              <YAxis stroke="#64748B" tick={{ fill: '#94A3B8', fontSize: 11 }} />
              <Tooltip
                contentStyle={{ backgroundColor: '#172338', borderColor: '#263449', borderRadius: '12px', color: '#fff' }}
              />
              <Bar dataKey="player_count" name="Players" fill="#B7F34A" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
