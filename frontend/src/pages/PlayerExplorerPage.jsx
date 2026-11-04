import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Search, Filter, Trophy, ArrowRight, GitCompare, Activity } from 'lucide-react';
import { TennisAPI } from '../services/api';

export default function PlayerExplorerPage() {
  const [players, setPlayers] = useState([]);
  const [search, setSearch] = useState('');
  const [selectedCountry, setSelectedCountry] = useState('');
  const [countries, setCountries] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchPlayers() {
      setLoading(true);
      const res = await TennisAPI.getPlayers({ search, country: selectedCountry, limit: 50 });
      setPlayers(res.items || []);
      setLoading(false);
    }
    fetchPlayers();
  }, [search, selectedCountry]);

  useEffect(() => {
    async function fetchCountries() {
      const res = await TennisAPI.getCountries();
      setCountries(res || []);
    }
    fetchCountries();
  }, []);

  return (
    <div className="space-y-6">
      {/* HEADER */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-heading font-extrabold text-white tracking-tight">
            Player Intelligence Explorer
          </h1>
          <p className="text-xs sm:text-sm text-textSecondary mt-1">
            Discover verified competitor dossiers, 5-axis ML traits, and international doubles standings.
          </p>
        </div>
        <div className="font-mono text-xs text-textMuted bg-background-card px-3 py-1.5 rounded-xl border border-slateBorder">
          Total Found: <span className="text-tennis-green font-bold">{players.length}</span>
        </div>
      </div>

      {/* FILTER BAR */}
      <div className="glass-card p-4 rounded-2xl flex flex-col sm:flex-row items-center gap-4">
        <div className="relative flex-1 w-full">
          <Search className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-textMuted" />
          <input
            type="text"
            placeholder="Search competitor name, country or code..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-background-main border border-slateBorder/80 text-sm text-white placeholder-textMuted focus:outline-none focus:border-tennis-green"
          />
        </div>

        <div className="flex items-center gap-2 w-full sm:w-auto">
          <Filter className="w-4 h-4 text-textMuted" />
          <select
            value={selectedCountry}
            onChange={(e) => setSelectedCountry(e.target.value)}
            className="w-full sm:w-48 py-2.5 px-3 rounded-xl bg-background-main border border-slateBorder/80 text-sm text-white focus:outline-none focus:border-tennis-green"
          >
            <option value="">All Countries</option>
            {countries.map((c) => (
              <option key={c.country} value={c.country}>
                {c.country} ({c.player_count})
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* PLAYERS GRID */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {[1, 2, 3, 4, 5, 6].map((n) => (
            <div key={n} className="glass-card p-6 rounded-2xl h-60 animate-pulse bg-background-card/50"></div>
          ))}
        </div>
      ) : players.length === 0 ? (
        <div className="glass-card p-12 rounded-2xl text-center space-y-3">
          <p className="text-base font-bold text-white">No tennis competitors found matching your criteria.</p>
          <p className="text-xs text-textMuted">Try clearing the search query or selecting a different country filter.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {players.map((player) => (
            <div
              key={player.competitor_id}
              className="glass-card glass-card-hover p-6 rounded-2xl flex flex-col justify-between space-y-4"
            >
              <div>
                <div className="flex items-center justify-between">
                  <span className="font-mono text-xs font-bold px-2.5 py-1 rounded-lg bg-tennis-green/10 text-tennis-green border border-tennis-green/30">
                    WORLD RANK #{player.rank}
                  </span>
                  <span className="text-xs font-mono px-2 py-0.5 rounded bg-background-card text-textMuted border border-slateBorder/50">
                    {player.country_code}
                  </span>
                </div>

                <div className="mt-3">
                  <h3 className="font-heading font-extrabold text-lg text-white hover:text-tennis-green transition">
                    <Link to={`/app/players/${player.competitor_id}`}>{player.name}</Link>
                  </h3>
                  <p className="text-xs text-textSecondary">{player.country}</p>
                </div>

                <div className="mt-2 inline-block">
                  <span className="text-[11px] font-medium px-2 py-0.5 rounded bg-cyanAccent/10 text-cyanAccent">
                    {player.cluster_tier}
                  </span>
                </div>

                {/* Key Metrics Grid */}
                <div className="grid grid-cols-2 gap-3 mt-4 pt-3 border-t border-slateBorder/50 text-xs">
                  <div>
                    <span className="text-textMuted block text-[10px] uppercase font-mono">Points Volume</span>
                    <span className="font-mono font-bold text-sm text-white">{player.points?.toLocaleString()} PTS</span>
                  </div>
                  <div>
                    <span className="text-textMuted block text-[10px] uppercase font-mono">Tournaments</span>
                    <span className="font-mono font-bold text-sm text-white">{player.competitions_played}</span>
                  </div>
                </div>

                {/* Radar Traits Mini-Summary */}
                {player.traits && (
                  <div className="mt-3 space-y-1.5">
                    <div className="flex justify-between text-[11px]">
                      <span className="text-textMuted">Consistency Index</span>
                      <span className="font-mono text-tennis-green font-bold">{player.traits.consistency}%</span>
                    </div>
                    <div className="w-full bg-slateBorder/50 h-1.5 rounded-full overflow-hidden">
                      <div className="bg-tennis-green h-full rounded-full" style={{ width: `${player.traits.consistency}%` }}></div>
                    </div>
                  </div>
                )}
              </div>

              {/* Action Buttons */}
              <div className="pt-3 border-t border-slateBorder/40 flex items-center justify-between gap-2">
                <Link
                  to={`/app/compare?player_a=${player.competitor_id}`}
                  className="px-3 py-1.5 rounded-lg bg-background-card hover:bg-background-cardHover text-textSecondary hover:text-white border border-slateBorder/60 text-xs font-medium flex items-center gap-1"
                >
                  <GitCompare className="w-3.5 h-3.5 text-tennis-green" /> Compare
                </Link>
                <Link
                  to={`/app/players/${player.competitor_id}`}
                  className="px-3.5 py-1.5 rounded-lg bg-tennis-green text-background-main font-bold text-xs hover:bg-tennis-greenHover transition flex items-center gap-1"
                >
                  Profile <ArrowRight className="w-3.5 h-3.5" />
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
