import React, { useState, useEffect } from 'react';
import { Trophy, MapPin, Clock, Layers, Search, Filter } from 'lucide-react';
import { TennisAPI } from '../services/api';

export default function CompetitionExplorerPage() {
  const [competitions, setCompetitions] = useState([]);
  const [venues, setVenues] = useState([]);
  const [activeTab, setActiveTab] = useState('competitions'); // 'competitions' or 'venues'
  const [filterType, setFilterType] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      setLoading(true);
      const [compRes, venueRes] = await Promise.all([
        TennisAPI.getCompetitions(),
        TennisAPI.getVenues()
      ]);
      setCompetitions(compRes || []);
      setVenues(venueRes || []);
      setLoading(false);
    }
    loadData();
  }, []);

  const filteredCompetitions = filterType
    ? competitions.filter(c => c.category_name.toLowerCase().includes(filterType.toLowerCase()))
    : competitions;

  return (
    <div className="space-y-6">
      {/* HEADER */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-heading font-extrabold text-white tracking-tight">
            Competitions & Venue Explorer
          </h1>
          <p className="text-xs sm:text-sm text-textSecondary mt-1">
            Navigate through international tournament hierarchies, sports complexes, and individual courts.
          </p>
        </div>

        {/* TABS */}
        <div className="flex items-center gap-1.5 p-1 bg-background-card rounded-xl border border-slateBorder">
          <button
            onClick={() => setActiveTab('competitions')}
            className={`px-4 py-2 rounded-lg text-xs font-bold transition flex items-center gap-1.5 ${
              activeTab === 'competitions'
                ? 'bg-tennis-green text-background-main shadow-md'
                : 'text-textSecondary hover:text-white'
            }`}
          >
            <Trophy className="w-3.5 h-3.5" /> Competitions ({competitions.length})
          </button>
          <button
            onClick={() => setActiveTab('venues')}
            className={`px-4 py-2 rounded-lg text-xs font-bold transition flex items-center gap-1.5 ${
              activeTab === 'venues'
                ? 'bg-tennis-green text-background-main shadow-md'
                : 'text-textSecondary hover:text-white'
            }`}
          >
            <MapPin className="w-3.5 h-3.5" /> Venues & Courts ({venues.length})
          </button>
        </div>
      </div>

      {/* CONTENT BASED ON ACTIVE TAB */}
      {activeTab === 'competitions' ? (
        <div className="space-y-4">
          {/* Category Filter Pills */}
          <div className="flex items-center gap-2 overflow-x-auto pb-1 text-xs">
            <span className="text-textMuted uppercase font-mono mr-2">Filter Category:</span>
            {['', 'Grand Slam', 'ATP', 'ITF'].map((cat) => (
              <button
                key={cat}
                onClick={() => setFilterType(cat)}
                className={`px-3 py-1.5 rounded-lg border font-medium transition ${
                  filterType === cat
                    ? 'bg-tennis-green/15 text-tennis-green border-tennis-green/40'
                    : 'bg-background-card text-textSecondary border-slateBorder/60 hover:text-white'
                }`}
              >
                {cat || 'All Categories'}
              </button>
            ))}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredCompetitions.map((comp) => (
              <div key={comp.competition_id} className="glass-card glass-card-hover p-5 rounded-2xl space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-tennis-green/10 text-tennis-green font-bold">
                    {comp.category_name}
                  </span>
                  <span className="text-[10px] font-mono uppercase text-textMuted">
                    {comp.gender} • {comp.type}
                  </span>
                </div>

                <h3 className="font-heading font-bold text-lg text-white">{comp.competition_name}</h3>

                <div className="pt-2 border-t border-slateBorder/50 flex items-center justify-between text-xs text-textSecondary">
                  <span>ID: <code className="text-textMuted font-mono text-[10px]">{comp.competition_id}</code></span>
                  {comp.parent_id && (
                    <span className="text-[11px] text-cyanAccent">Sub-competition</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {venues.map((venue) => (
            <div key={venue.venue_id} className="glass-card glass-card-hover p-5 rounded-2xl space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyanAccent/10 text-cyanAccent font-bold">
                  {venue.country_code} • {venue.country_name}
                </span>
                <span className="flex items-center gap-1 text-[11px] text-textMuted font-mono">
                  <Clock className="w-3 h-3 text-tennis-green" /> {venue.timezone}
                </span>
              </div>

              <div>
                <h3 className="font-heading font-bold text-base text-white">{venue.venue_name}</h3>
                <p className="text-xs text-textSecondary flex items-center gap-1 mt-1">
                  <MapPin className="w-3 h-3 text-textMuted" /> {venue.city_name}, {venue.country_name}
                </p>
              </div>

              <div className="pt-2 border-t border-slateBorder/50 text-xs text-textMuted">
                <span>Sports Complex: </span>
                <span className="text-white font-medium">{venue.complex_name}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
