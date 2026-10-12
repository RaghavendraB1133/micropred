import React from 'react';
import { AlertCircle, AlertTriangle, CheckCircle } from 'lucide-react';

export default function RiskBadge({ category, score, showScore = true, size = 'md' }) {
  const cat = (category || 'LOW').toUpperCase();

  const config = {
    LOW: {
      bg: 'bg-emerald-950/60 border-emerald-500/40 text-emerald-300',
      dot: 'bg-emerald-500',
      icon: CheckCircle,
      label: 'LOW RISK'
    },
    MEDIUM: {
      bg: 'bg-amber-950/60 border-amber-500/40 text-amber-300',
      dot: 'bg-amber-500',
      icon: AlertTriangle,
      label: 'MEDIUM RISK'
    },
    HIGH: {
      bg: 'bg-rose-950/60 border-rose-500/40 text-rose-300',
      dot: 'bg-rose-500',
      icon: AlertCircle,
      label: 'HIGH RISK'
    }
  }[cat] || {
    bg: 'bg-slate-800 border-slate-700 text-slate-300',
    dot: 'bg-slate-400',
    icon: CheckCircle,
    label: cat
  };

  const Icon = config.icon;
  const padding = size === 'sm' ? 'px-2 py-0.5 text-xs' : 'px-2.5 py-1 text-xs font-semibold';

  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full border ${config.bg} ${padding} transition-all`}>
      <span className={`h-1.5 w-1.5 rounded-full ${config.dot} animate-pulse`} />
      <Icon className="h-3 w-3" />
      <span>{config.label}</span>
      {showScore && score !== undefined && score !== null && (
        <span className="opacity-75 font-mono text-[11px] ml-0.5">
          ({(score * 100).toFixed(1)}%)
        </span>
      )}
    </span>
  );
}
