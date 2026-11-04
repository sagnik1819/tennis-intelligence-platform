import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { GitCompare, Sparkles, AlertCircle, Trophy, ArrowRight, ShieldAlert } from 'lucide-react';
import { TennisAPI } from '../services/api';
import PlayerRadarChart from '../components/charts/PlayerRadarChart';

export default function ComparisonPage() {
  const [searchParams] = useSearchParams();
  const [allPlayers, setAllPlayers] = useState([]);
  const [playerAId, setPlayerAId] = useState('');
  const [playerBId, setPlayerBId] = useState('');
  const [comparison, setComparison] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    async function loadAll() {
      const res = await TennisAPI.getPlayers({ limit: 50 });
      const items = res.items || [];
      setAllPlayers(items);

      const initA = searchParams.get('player_a') || (items[0] ? items[0].competitor_id : '');
      const initB = searchParams.get('player_b') || (items[1] ? items[1].competitor_id : '');
      setPlayerAId(initA);
      setPlayerBId(initB);
    }
    loadAll();
  }, [searchParams]);

  useEffect(() => {
    async function runComparison() {
      if (!playerAId || !playerBId || playerAId === playerBId) return;
      setLoading(true);
      const data = await TennisAPI.comparePlayers(playerAId, playerBId);
      setComparison(data);
      setLoading(false);
    }
    runComparison();
  }, [playerAId, playerBId]);

  return (
    <div className="space-y-6">
      {/* HEADER */}
      <div>
        <h1 className="text-2xl sm:text-3xl font-heading font-extrabold text-white tracking-tight">
          Smart Head-to-Head Player Comparison
        </h1>
        <p className="text-xs sm:text-sm text-textSecondary mt-1">
          Select any two competitors for statistical disparity metrics, dual radar overlays, and AI analysis.
        </p>
      </div>

      {/* SELECTOR BAR */}
      <div className="glass-card p-6 rounded-2xl grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="text-xs font-mono uppercase text-tennis-green block mb-1.5 font-bold">
            Select Competitor A (Green)
          </label>
          <select
            value={playerAId}
            onChange={(e) => setPlayerAId(e.target.value)}
            className="w-full py-2.5 px-3 rounded-xl bg-background-main border border-slateBorder text-sm text-white focus:outline-none focus:border-tennis-green"
          >
            {allPlayers.map((p) => (
              <option key={p.competitor_id} value={p.competitor_id}>
                #{p.rank} {p.name} ({p.country}) - {p.points?.toLocaleString()} pts
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="text-xs font-mono uppercase text-cyanAccent block mb-1.5 font-bold">
            Select Competitor B (Cyan)
          </label>
          <select
            value={playerBId}
            onChange={(e) => setPlayerBId(e.target.value)}
            className="w-full py-2.5 px-3 rounded-xl bg-background-main border border-slateBorder text-sm text-white focus:outline-none focus:border-cyanAccent"
          >
            {allPlayers.map((p) => (
              <option key={p.competitor_id} value={p.competitor_id}>
                #{p.rank} {p.name} ({p.country}) - {p.points?.toLocaleString()} pts
              </option>
            ))}
          </select>
        </div>
      </div>

      {loading ? (
        <div className="glass-card p-12 rounded-2xl text-center text-textMuted font-mono text-sm animate-pulse">
          Computing comparison vectors and AI breakdown...
        </div>
      ) : comparison ? (
        <div className="space-y-6">
          {/* SIDE-BY-SIDE HEADERS */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="glass-card p-6 rounded-2xl border-l-4 border-l-tennis-green space-y-2">
              <span className="text-xs font-mono text-tennis-green font-bold">COMPETITOR A</span>
              <h2 className="text-2xl font-heading font-extrabold text-white">{comparison.player_a?.name}</h2>
              <p className="text-xs text-textSecondary">{comparison.player_a?.country} • World Rank #{comparison.player_a?.rank}</p>
              <div className="pt-2">
                <span className="text-xl font-mono font-bold text-white">{comparison.player_a?.points?.toLocaleString()} <span className="text-xs text-textMuted">PTS</span></span>
              </div>
            </div>

            <div className="glass-card p-6 rounded-2xl border-l-4 border-l-cyanAccent space-y-2">
              <span className="text-xs font-mono text-cyanAccent font-bold">COMPETITOR B</span>
              <h2 className="text-2xl font-heading font-extrabold text-white">{comparison.player_b?.name}</h2>
              <p className="text-xs text-textSecondary">{comparison.player_b?.country} • World Rank #{comparison.player_b?.rank}</p>
              <div className="pt-2">
                <span className="text-xl font-mono font-bold text-white">{comparison.player_b?.points?.toLocaleString()} <span className="text-xs text-textMuted">PTS</span></span>
              </div>
            </div>
          </div>

          {/* DUAL RADAR OVERLAY & AI BREAKDOWN */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* RADAR OVERLAY */}
            <div className="glass-card p-6 rounded-2xl space-y-3">
              <div className="flex items-center justify-between border-b border-slateBorder/60 pb-3">
                <h3 className="text-sm font-bold text-white">5-Axis Trait Overlay</h3>
                <div className="flex items-center gap-4 text-xs font-mono">
                  <span className="flex items-center gap-1.5 text-tennis-green">
                    <span className="w-2.5 h-2.5 rounded-full bg-tennis-green"></span> {comparison.player_a?.name?.split(',')[0]}
                  </span>
                  <span className="flex items-center gap-1.5 text-cyanAccent">
                    <span className="w-2.5 h-2.5 rounded-full bg-cyanAccent"></span> {comparison.player_b?.name?.split(',')[0]}
                  </span>
                </div>
              </div>

              <PlayerRadarChart
                traits={comparison.player_a?.traits}
                playerName={comparison.player_a?.name}
                compareTraits={comparison.player_b?.traits}
                compareName={comparison.player_b?.name}
              />
            </div>

            {/* AI COMPARISON ANALYSIS */}
            <div className="glass-card p-6 rounded-2xl flex flex-col justify-between space-y-4">
              <div className="space-y-3">
                <div className="flex items-center gap-2 text-tennis-green">
                  <Sparkles className="w-4 h-4" />
                  <h3 className="text-sm font-bold uppercase tracking-wider font-mono">AI Comparative Sports Analysis</h3>
                </div>

                <p className="text-sm text-textSecondary leading-relaxed bg-background-main/60 p-4 rounded-xl border border-slateBorder/60">
                  {comparison.ai_comparison_analysis}
                </p>
              </div>

              {/* Data Warning Alert */}
              {comparison.missing_data_warnings && (
                <div className="flex items-start gap-2.5 p-3 rounded-xl bg-amber-500/10 border border-amber-500/20 text-xs text-amber-300">
                  <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
                  <span>{comparison.missing_data_warnings[0]}</span>
                </div>
              )}
            </div>
          </div>

          {/* METRIC DIFFERENCE TABLE */}
          <div className="glass-card p-6 rounded-2xl space-y-4">
            <h3 className="text-base font-bold text-white border-b border-slateBorder/60 pb-3">
              Detailed Metric Head-to-Head
            </h3>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="text-[11px] font-mono uppercase text-textMuted border-b border-slateBorder/40">
                    <th className="py-2.5 px-3">Metric Category</th>
                    <th className="py-2.5 px-3 text-tennis-green">{comparison.player_a?.name}</th>
                    <th className="py-2.5 px-3 text-cyanAccent">{comparison.player_b?.name}</th>
                    <th className="py-2.5 px-3">Difference</th>
                    <th className="py-2.5 px-3 text-right">Statistical Edge</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slateBorder/30 font-mono text-xs">
                  {comparison.metrics_table?.map((row, idx) => (
                    <tr key={idx} className="hover:bg-background-card/50 transition">
                      <td className="py-3 px-3 font-sans font-medium text-white">{row.metric}</td>
                      <td className="py-3 px-3 text-white font-bold">{row.player_a_value}</td>
                      <td className="py-3 px-3 text-white font-bold">{row.player_b_value}</td>
                      <td className="py-3 px-3 text-textSecondary">{row.difference}</td>
                      <td className="py-3 px-3 text-right">
                        {row.advantage === 'player_a' ? (
                          <span className="px-2 py-0.5 rounded bg-tennis-green/10 text-tennis-green font-bold">
                            Advantage {comparison.player_a?.name?.split(',')[0]}
                          </span>
                        ) : row.advantage === 'player_b' ? (
                          <span className="px-2 py-0.5 rounded bg-cyanAccent/10 text-cyanAccent font-bold">
                            Advantage {comparison.player_b?.name?.split(',')[0]}
                          </span>
                        ) : (
                          <span className="px-2 py-0.5 rounded bg-slate-500/10 text-textMuted">
                            Tied / Equal
                          </span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
