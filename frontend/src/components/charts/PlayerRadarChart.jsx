import React from 'react';
import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer
} from 'recharts';

export default function PlayerRadarChart({ traits, playerName = "Competitor", compareTraits = null, compareName = null }) {
  if (!traits) {
    return <div className="h-64 flex items-center justify-center text-textMuted text-xs">No trait metrics available</div>;
  }

  const data = [
    { trait: 'Consistency', value: traits.consistency || 50, compare: compareTraits?.consistency || 0 },
    { trait: 'Power Volume', value: traits.power_volume || 50, compare: compareTraits?.power_volume || 0 },
    { trait: 'Stamina', value: traits.tournament_stamina || 50, compare: compareTraits?.tournament_stamina || 0 },
    { trait: 'Momentum', value: traits.rank_momentum || 50, compare: compareTraits?.rank_momentum || 0 },
    { trait: 'Efficiency', value: traits.efficiency || 50, compare: compareTraits?.efficiency || 0 },
  ];

  return (
    <div className="w-full h-64 sm:h-72">
      <ResponsiveContainer width="100%" height="100%">
        <RadarChart cx="50%" cy="50%" outerRadius="70%" data={data}>
          <PolarGrid stroke="#263449" />
          <PolarAngleAxis dataKey="trait" stroke="#94A3B8" tick={{ fill: '#94A3B8', fontSize: 11 }} />
          <PolarRadiusAxis angle={30} domain={[0, 100]} stroke="#263449" tick={false} />
          
          {/* Primary Player */}
          <Radar
            name={playerName}
            dataKey="value"
            stroke="#B7F34A"
            fill="#B7F34A"
            fillOpacity={0.35}
          />

          {/* Optional Comparison Player */}
          {compareTraits && (
            <Radar
              name={compareName || "Opponent"}
              dataKey="compare"
              stroke="#43C6AC"
              fill="#43C6AC"
              fillOpacity={0.25}
            />
          )}
        </RadarChart>
      </ResponsiveContainer>
    </div>
  );
}
