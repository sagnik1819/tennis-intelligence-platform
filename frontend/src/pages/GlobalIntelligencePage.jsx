import React, { useState, useEffect } from 'react';
import { Globe, Trophy, Users, TrendingUp, BarChart3 } from 'lucide-react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip } from 'recharts';
import { TennisAPI } from '../services/api';

export default function GlobalIntelligencePage() {
  const [countries, setCountries] = useState([]);
  const [venues, setVenues] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      setLoading(true);
      const [cRes, vRes] = await Promise.all([
        TennisAPI.getCountries(),
        TennisAPI.getVenues()
      ]);
      setCountries(cRes || []);
      setVenues(vRes || []);
      setLoading(false);
    }
    loadData();
  }, []);

  return (
    <div className="space-y-6">
      {/* HEADER */}
      <div>
        <h1 className="text-2xl sm:text-3xl font-heading font-extrabold text-white tracking-tight">
          Global Tennis Geographic Intelligence
        </h1>
        <p className="text-xs sm:text-sm text-textSecondary mt-1">
          Explore player density by nation, international points volume, and complex venue distributions.
        </p>
      </div>

      {/* TOP SUMMARY CARDS */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="glass-card p-5 rounded-2xl">
          <span className="text-xs font-mono uppercase text-textMuted block">Active Countries</span>
          <span className="text-3xl font-heading font-black text-white mt-2 block">{countries.length}</span>
          <span className="text-xs text-textSecondary mt-1 block">Federations Represented</span>
        </div>
        <div className="glass-card p-5 rounded-2xl">
          <span className="text-xs font-mono uppercase text-textMuted block">Total International Venues</span>
          <span className="text-3xl font-heading font-black text-tennis-green mt-2 block">{venues.length}</span>
          <span className="text-xs text-textSecondary mt-1 block">Sanctioned Tennis Courts</span>
        </div>
        <div className="glass-card p-5 rounded-2xl">
          <span className="text-xs font-mono uppercase text-textMuted block">Top Country by Points</span>
          <span className="text-3xl font-heading font-black text-cyanAccent mt-2 block">
            {countries[0] ? countries[0].country : '--'}
          </span>
          <span className="text-xs text-textSecondary mt-1 block">
            {countries[0] ? `${countries[0].total_points.toLocaleString()} Points` : ''}
          </span>
        </div>
      </div>

      {/* CHART & TABLE SECTION */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* CHART: TOTAL POINTS BY COUNTRY */}
        <div className="glass-card p-6 rounded-2xl space-y-4">
          <div className="flex items-center justify-between border-b border-slateBorder/60 pb-3">
            <h3 className="text-sm font-bold text-white">Ranking Points by Federation</h3>
            <span className="text-xs font-mono text-tennis-green">Total Cumulative Points</span>
          </div>

          <div className="w-full h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={countries} layout="vertical">
                <XAxis type="number" stroke="#64748B" tick={{ fill: '#94A3B8', fontSize: 11 }} />
                <YAxis dataKey="country" type="category" stroke="#64748B" tick={{ fill: '#94A3B8', fontSize: 11 }} width={100} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#172338', borderColor: '#263449', borderRadius: '12px', color: '#fff' }}
                />
                <Bar dataKey="total_points" name="Total Points" fill="#43C6AC" radius={[0, 6, 6, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* COUNTRY METRICS TABLE */}
        <div className="glass-card p-6 rounded-2xl space-y-4">
          <h3 className="text-sm font-bold text-white border-b border-slateBorder/60 pb-3">
            National Performance Index
          </h3>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="text-[11px] font-mono uppercase text-textMuted border-b border-slateBorder/40">
                  <th className="py-2.5 px-3">Country</th>
                  <th className="py-2.5 px-3">Code</th>
                  <th className="py-2.5 px-3">Competitors</th>
                  <th className="py-2.5 px-3">Points</th>
                  <th className="py-2.5 px-3 text-right">Avg / Player</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slateBorder/30 font-mono text-xs">
                {countries.map((c) => (
                  <tr key={c.country} className="hover:bg-background-card/50 transition">
                    <td className="py-3 px-3 font-sans font-semibold text-white">{c.country}</td>
                    <td className="py-3 px-3 text-textMuted">{c.country_code}</td>
                    <td className="py-3 px-3 text-tennis-green font-bold">{c.player_count}</td>
                    <td className="py-3 px-3 text-white">{c.total_points.toLocaleString()}</td>
                    <td className="py-3 px-3 text-right text-textSecondary">{c.avg_points.toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
