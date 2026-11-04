import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  Trophy,
  Activity,
  Bookmark,
  Share2,
  GitCompare,
  ArrowLeft,
  Sparkles,
  ShieldCheck,
  TrendingUp,
  Award
} from 'lucide-react';
import { TennisAPI } from '../services/api';
import PlayerRadarChart from '../components/charts/PlayerRadarChart';

export default function PlayerDetailPage() {
  const { id } = useParams();
  const [player, setPlayer] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isFav, setIsFav] = useState(false);

  useEffect(() => {
    async function loadPlayer() {
      setLoading(true);
      const data = await TennisAPI.getPlayerDetail(id);
      setPlayer(data);
      setIsFav(data?.is_favourite || false);
      setLoading(false);
    }
    loadPlayer();
  }, [id]);

  if (loading || !player) {
    return (
      <div className="h-96 flex items-center justify-center text-textMuted font-mono text-sm">
        Loading player intelligence profile...
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* BACK BUTTON */}
      <Link
        to="/app/players"
        className="inline-flex items-center gap-1.5 text-xs text-textSecondary hover:text-white transition font-medium"
      >
        <ArrowLeft className="w-4 h-4" /> Back to Player Explorer
      </Link>

      {/* PLAYER HERO CARD */}
      <div className="glass-card p-6 sm:p-8 rounded-3xl relative overflow-hidden">
        {/* Glow accent */}
        <div className="absolute top-0 right-0 w-80 h-80 bg-tennis-green/10 rounded-full blur-[100px] pointer-events-none"></div>

        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 relative z-10">
          <div className="space-y-3">
            <div className="flex items-center gap-3">
              <span className="font-mono text-xs font-black px-3 py-1 rounded-xl bg-tennis-green text-background-main">
                OFFICIAL RANK #{player.ranking?.rank || player.rank}
              </span>
              <span className="font-mono text-xs px-2.5 py-1 rounded-lg bg-background-card border border-slateBorder text-textSecondary">
                {player.country_code} • {player.abbreviation}
              </span>
              <span className="text-xs font-semibold px-2.5 py-1 rounded-lg bg-cyanAccent/10 text-cyanAccent">
                {player.cluster_tier}
              </span>
            </div>

            <h1 className="text-3xl sm:text-5xl font-heading font-black text-white tracking-tight">
              {player.name}
            </h1>

            <p className="text-sm text-textSecondary flex items-center gap-2">
              <span>{player.country}</span>
              <span>•</span>
              <span>International Circuit Competitor</span>
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => setIsFav(!isFav)}
              className={`p-3 rounded-2xl border transition flex items-center gap-2 text-xs font-semibold ${
                isFav
                  ? 'bg-tennis-green text-background-main border-tennis-green'
                  : 'bg-background-card text-textSecondary border-slateBorder hover:text-white'
              }`}
            >
              <Bookmark className={`w-4 h-4 ${isFav ? 'fill-current' : ''}`} />
              <span>{isFav ? 'Saved in Workspace' : 'Bookmark Player'}</span>
            </button>

            <Link
              to={`/app/compare?player_a=${player.competitor_id}`}
              className="px-4 py-3 rounded-2xl bg-tennis-green/10 text-tennis-green border border-tennis-green/30 hover:bg-tennis-green hover:text-background-main text-xs font-bold transition flex items-center gap-1.5"
            >
              <GitCompare className="w-4 h-4" /> Compare Against Opponent
            </Link>
          </div>
        </div>

        {/* STATS STRIP */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-8 pt-6 border-t border-slateBorder/60">
          <div>
            <span className="text-textMuted text-[10px] uppercase font-mono block">Ranking Points</span>
            <span className="text-2xl font-heading font-bold text-white font-mono mt-1 block">
              {(player.ranking?.points || player.points)?.toLocaleString()}
            </span>
          </div>
          <div>
            <span className="text-textMuted text-[10px] uppercase font-mono block">Tournaments Played</span>
            <span className="text-2xl font-heading font-bold text-white font-mono mt-1 block">
              {player.ranking?.competitions_played || player.competitions_played}
            </span>
          </div>
          <div>
            <span className="text-textMuted text-[10px] uppercase font-mono block">Weekly Movement</span>
            <span className="text-2xl font-heading font-bold text-white font-mono mt-1 block">
              {(player.ranking?.movement || player.movement) >= 0 ? `+${player.ranking?.movement || player.movement} pos` : `${player.ranking?.movement || player.movement} pos`}
            </span>
          </div>
          <div>
            <span className="text-textMuted text-[10px] uppercase font-mono block">Avg Points / Event</span>
            <span className="text-2xl font-heading font-bold text-tennis-green font-mono mt-1 block">
              {Math.round((player.ranking?.points || player.points) / Math.max((player.ranking?.competitions_played || player.competitions_played), 1))}
            </span>
          </div>
        </div>
      </div>

      {/* TWO-COLUMN INTELLIGENCE SECTION */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* LEFT: 5-AXIS RADAR CHART */}
        <div className="glass-card p-6 rounded-3xl space-y-4">
          <div className="flex items-center justify-between border-b border-slateBorder/60 pb-3">
            <div className="flex items-center gap-2">
              <Activity className="w-4 h-4 text-tennis-green" />
              <h2 className="text-base font-bold text-white">5-Axis ML Trait Profile</h2>
            </div>
            <span className="text-xs font-mono text-textMuted">Normalized [20 - 98]</span>
          </div>

          <PlayerRadarChart traits={player.traits} playerName={player.name} />

          {/* Traits Progress Bars */}
          <div className="space-y-3 pt-2">
            {player.traits && Object.entries(player.traits).map(([key, val]) => (
              <div key={key} className="space-y-1">
                <div className="flex justify-between text-xs">
                  <span className="text-textSecondary uppercase tracking-wider text-[10px] font-mono">
                    {key.replace('_', ' ')}
                  </span>
                  <span className="font-mono text-tennis-green font-bold">{val} / 100</span>
                </div>
                <div className="w-full bg-slateBorder/50 h-2 rounded-full overflow-hidden">
                  <div className="bg-tennis-green h-full rounded-full transition-all duration-500" style={{ width: `${val}%` }}></div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* RIGHT: AI SUMMARY & SIMILAR PLAYERS */}
        <div className="space-y-6">
          {/* AI SUMMARY CARD */}
          <div className="glass-card p-6 rounded-3xl space-y-3 border-tennis-green/30">
            <div className="flex items-center gap-2 text-tennis-green">
              <Sparkles className="w-4 h-4" />
              <h2 className="text-sm font-bold uppercase tracking-wider font-mono">AI Player Intelligence Brief</h2>
            </div>
            <p className="text-sm text-textSecondary leading-relaxed bg-background-main/50 p-4 rounded-2xl border border-slateBorder/50">
              {player.ai_summary}
            </p>
          </div>

          {/* SIMILAR PLAYERS RECOMMENDATION */}
          <div className="glass-card p-6 rounded-3xl space-y-4">
            <div className="flex items-center justify-between border-b border-slateBorder/60 pb-3">
              <div className="flex items-center gap-2">
                <Award className="w-4 h-4 text-cyanAccent" />
                <h2 className="text-base font-bold text-white">Similar Circuit Competitors</h2>
              </div>
              <span className="text-xs font-mono text-textMuted">Euclidean Nearest Neighbors</span>
            </div>

            <div className="space-y-3">
              {(player.similar_players || []).map((sim) => (
                <div
                  key={sim.competitor_id}
                  className="p-3.5 rounded-xl bg-background-card hover:bg-background-cardHover border border-slateBorder/50 flex items-center justify-between transition"
                >
                  <div>
                    <Link
                      to={`/app/players/${sim.competitor_id}`}
                      className="font-bold text-sm text-white hover:text-tennis-green transition"
                    >
                      {sim.name}
                    </Link>
                    <span className="text-xs text-textMuted block">{sim.country} • Rank #{sim.rank}</span>
                  </div>
                  <div className="text-right">
                    <span className="font-mono text-xs font-bold text-tennis-green block">{sim.points?.toLocaleString()} PTS</span>
                    <Link
                      to={`/app/compare?player_a=${player.competitor_id}&player_b=${sim.competitor_id}`}
                      className="text-[11px] text-textMuted hover:text-white underline mt-0.5 block"
                    >
                      Compare
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
