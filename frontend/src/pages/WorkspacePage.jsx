import React, { useState, useEffect } from 'react';
import { Bookmark, Download, Trash2, ArrowRight, FileText, CheckCircle2 } from 'lucide-react';
import { Link } from 'react-router-dom';
import { TennisAPI } from '../services/api';

export default function WorkspacePage() {
  const [players, setPlayers] = useState([]);
  const [exportNotice, setExportNotice] = useState(false);

  useEffect(() => {
    async function loadData() {
      const res = await TennisAPI.getPlayers({ limit: 4 });
      setPlayers(res.items || []);
    }
    loadData();
  }, []);

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
            Manage your bookmarked players, customize analytics views, and download structured CSV reports.
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
