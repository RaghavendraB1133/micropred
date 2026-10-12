import React from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts';

export default function RiskPieChart({ riskCounts = { LOW: 0, MEDIUM: 0, HIGH: 0 } }) {
  const data = [
    { name: 'Low Risk', value: riskCounts.LOW || 0, color: '#10b981' },
    { name: 'Medium Risk', value: riskCounts.MEDIUM || 0, color: '#f59e0b' },
    { name: 'High Risk', value: riskCounts.HIGH || 0, color: '#ef4444' },
  ].filter(d => d.value > 0);

  const fallbackData = data.length > 0 ? data : [
    { name: 'No Active Zones', value: 1, color: '#475569' }
  ];

  return (
    <div className="h-64 w-full flex items-center justify-center">
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={fallbackData}
            cx="50%"
            cy="50%"
            innerRadius={55}
            outerRadius={80}
            paddingAngle={4}
            dataKey="value"
          >
            {fallbackData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color} stroke="#0f172a" strokeWidth={2} />
            ))}
          </Pie>
          <Tooltip
            contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '0.5rem', color: '#f8fafc' }}
            itemStyle={{ fontSize: '12px' }}
          />
          <Legend
            verticalAlign="bottom"
            height={36}
            formatter={(value) => <span className="text-xs text-slate-300">{value}</span>}
          />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}
