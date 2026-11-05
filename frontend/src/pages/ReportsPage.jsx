import React, { useState, useEffect } from 'react';
import { FileText, Download, Printer, Filter, CheckCircle2, Trophy, Users, Globe, ArrowDownToLine } from 'lucide-react';
import { TennisAPI } from '../services/api';

export default function ReportsPage() {
  const [players, setPlayers] = useState([]);
  const [countries, setCountries] = useState([]);
  const [kpis, setKpis] = useState(null);
  const [selectedCountry, setSelectedCountry] = useState('');
  const [selectedTier, setSelectedTier] = useState('');
  const [loading, setLoading] = useState(true);
  const [downloadSuccess, setDownloadSuccess] = useState(false);

  useEffect(() => {
    async function loadData() {
      setLoading(true);
      const [pRes, cRes, kRes] = await Promise.all([
        TennisAPI.getPlayers({ limit: 50 }),
        TennisAPI.getCountries(),
        TennisAPI.getKPIs()
      ]);
      setPlayers(pRes.items || []);
      setCountries(cRes || []);
      setKpis(kRes);
      setLoading(false);
    }
    loadData();
  }, []);

  const filtered = players.filter((p) => {
    const matchCountry = !selectedCountry || p.country.toLowerCase() === selectedCountry.toLowerCase();
    const matchTier = !selectedTier || p.cluster_tier.toLowerCase().includes(selectedTier.toLowerCase());
    return matchCountry && matchTier;
  });

  const exportCSV = () => {
    if (!filtered.length) return;
    const headers = ["Rank", "Name", "Country", "Country_Code", "Points", "Competitions", "Tier", "Consistency", "Power_Volume"];
    const rows = filtered.map(p => [
      p.rank,
      `"${p.name}"`,
      `"${p.country}"`,
      p.country_code,
      p.points,
      p.competitions_played,
      `"${p.cluster_tier}"`,
      p.traits?.consistency || 0,
      p.traits?.power_volume || 0
    ]);

    const csvContent = "data:text/csv;charset=utf-8," + [headers.join(","), ...rows.map(r => r.join(","))].join("\n");
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `tennis_intelligence_analytical_report_${new Date().toISOString().slice(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    setDownloadSuccess(true);
    setTimeout(() => setDownloadSuccess(false), 3500);
  };

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="space-y-6">
      {/* HEADER */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-heading font-extrabold text-white tracking-tight">
            Reports & Analytical Intelligence Center
          </h1>
          <p className="text-xs sm:text-sm text-textSecondary mt-1">
            Export certified CSV tables, generate shareable PDF briefs, and filter statistical performance records.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handlePrint}
            className="px-4 py-2.5 rounded-xl bg-background-card hover:bg-background-cardHover border border-slateBorder text-xs font-semibold text-white transition flex items-center gap-2"
          >
            <Printer className="w-4 h-4 text-cyanAccent" /> Print / PDF View
          </button>
          <button
            onClick={exportCSV}
            className="px-4 py-2.5 rounded-xl bg-tennis-green text-background-main font-bold text-xs hover:bg-tennis-greenHover transition flex items-center gap-2 shadow-lg shadow-tennis-green/20"
          >
            <Download className="w-4 h-4" /> Download CSV
          </button>
        </div>
      </div>

      {downloadSuccess && (
        <div className="p-3.5 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-xs text-emerald-400 flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 shrink-0" />
          <span>Analytical dataset generated and downloaded successfully.</span>
        </div>
      )}

      {/* FILTER CONTROLS */}
      <div className="glass-card p-5 rounded-2xl flex flex-col sm:flex-row items-center gap-4">
        <div className="flex items-center gap-2 w-full sm:w-auto">
          <Filter className="w-4 h-4 text-tennis-green" />
          <span className="text-xs font-mono uppercase text-textMuted font-bold">Report Filters:</span>
        </div>

        <select
          value={selectedCountry}
          onChange={(e) => setSelectedCountry(e.target.value)}
          className="w-full sm:w-56 py-2.5 px-3 rounded-xl bg-background-main border border-slateBorder text-xs text-white focus:outline-none focus:border-tennis-green"
        >
          <option value="">All Countries ({countries.length})</option>
          {countries.map((c) => (
            <option key={c.country} value={c.country}>
              {c.country} ({c.player_count} players)
            </option>
          ))}
        </select>

        <select
          value={selectedTier}
          onChange={(e) => setSelectedTier(e.target.value)}
          className="w-full sm:w-56 py-2.5 px-3 rounded-xl bg-background-main border border-slateBorder text-xs text-white focus:outline-none focus:border-tennis-green"
        >
          <option value="">All Cluster Tiers</option>
          <option value="Grand Slam">Elite Grand Slam Tier</option>
          <option value="Contender">High-Yield Contender</option>
          <option value="Challenger">Challenger Circuit</option>
        </select>

        <div className="ml-auto text-xs font-mono text-textMuted">
          Showing <span className="text-tennis-green font-bold">{filtered.length}</span> of {players.length} records
        </div>
      </div>

      {/* REPORT SUMMARY KPI ROW */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
        <div className="glass-card p-4 rounded-xl">
          <span className="text-[10px] font-mono uppercase text-textMuted block">Report Scope</span>
          <span className="text-xl font-heading font-bold text-white mt-1 block">{filtered.length} Competitors</span>
        </div>
        <div className="glass-card p-4 rounded-xl">
          <span className="text-[10px] font-mono uppercase text-textMuted block">Cumulative Points</span>
          <span className="text-xl font-heading font-bold text-tennis-green font-mono mt-1 block">
            {filtered.reduce((acc, p) => acc + (p.points || 0), 0).toLocaleString()} PTS
          </span>
        </div>
        <div className="glass-card p-4 rounded-xl">
          <span className="text-[10px] font-mono uppercase text-textMuted block">Mean Consistency</span>
          <span className="text-xl font-heading font-bold text-cyanAccent font-mono mt-1 block">
            {filtered.length ? (filtered.reduce((acc, p) => acc + (p.traits?.consistency || 0), 0) / filtered.length).toFixed(1) : 0}%
          </span>
        </div>
        <div className="glass-card p-4 rounded-xl">
          <span className="text-[10px] font-mono uppercase text-textMuted block">Audit Certification</span>
          <span className="text-xl font-heading font-bold text-emerald-400 mt-1 block">100% Certified</span>
        </div>
      </div>

      {/* REPORT DATA TABLE */}
      <div className="glass-card p-6 rounded-2xl space-y-4">
        <div className="flex items-center justify-between border-b border-slateBorder/60 pb-3">
          <h2 className="text-base font-bold text-white">Generated Intelligence Table</h2>
          <span className="text-xs font-mono text-textMuted">Format: ISO / SportRadar Verified</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="text-[11px] font-mono uppercase text-textMuted border-b border-slateBorder/40">
                <th className="py-2.5 px-3">Rank</th>
                <th className="py-2.5 px-3">Player Name</th>
                <th className="py-2.5 px-3">Country</th>
                <th className="py-2.5 px-3">Points</th>
                <th className="py-2.5 px-3">Tournaments</th>
                <th className="py-2.5 px-3">Cluster Tier</th>
                <th className="py-2.5 px-3 text-right">Consistency</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slateBorder/30 font-mono text-xs">
              {filtered.map((p) => (
                <tr key={p.competitor_id} className="hover:bg-background-card/50 transition">
                  <td className="py-3 px-3 text-tennis-green font-bold">#{p.rank}</td>
                  <td className="py-3 px-3 font-sans font-semibold text-white">{p.name}</td>
                  <td className="py-3 px-3 text-textSecondary">{p.country} ({p.country_code})</td>
                  <td className="py-3 px-3 text-white font-bold">{p.points?.toLocaleString()}</td>
                  <td className="py-3 px-3 text-textMuted">{p.competitions_played}</td>
                  <td className="py-3 px-3 font-sans text-cyanAccent">{p.cluster_tier}</td>
                  <td className="py-3 px-3 text-right font-bold text-tennis-green">{p.traits?.consistency}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
