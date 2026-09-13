import React from 'react';
import GlassCard from './GlassCard';

interface MetricCardProps {
  label: string;
  value: string | number;
  sub?: string;
  accent?: string;
  trend?: 'up' | 'down' | 'neutral';
  icon?: React.ReactNode;
  sparkline?: number[];
  className?: string;
}

export function MetricCard({
  label,
  value,
  sub,
  accent,
  trend,
  icon,
  sparkline,
  className = '',
}: MetricCardProps) {
  return (
    <GlassCard variant="medium" padding={18} className={`flex flex-col justify-between flex-1 min-w-[180px] ${className}`}>
      <div>
        <div className="flex items-center justify-between gap-2 mb-1.5">
          <span className="text-[10px] font-semibold uppercase tracking-wider text-[var(--text-muted)]">
            {label}
          </span>
          {icon && <div className="text-[var(--text-muted)] opacity-80">{icon}</div>}
        </div>

        <div
          className="text-2xl font-bold font-display tracking-tight font-mono-data"
          style={{ color: accent || 'var(--text-primary)' }}
        >
          {value}
        </div>
      </div>

      {(sub || trend || sparkline) && (
        <div className="mt-3 pt-2 border-t border-[var(--border-hairline)] flex items-center justify-between">
          {sub && (
            <div className="text-[11px] text-[var(--text-secondary)] flex items-center gap-1">
              {trend === 'up' && <span className="text-[var(--risk-critical)] font-bold">↑</span>}
              {trend === 'down' && <span className="text-[var(--risk-low)] font-bold">↓</span>}
              <span>{sub}</span>
            </div>
          )}

          {sparkline && sparkline.length > 1 && (
            <div className="w-16 h-5">
              <svg viewBox={`0 0 ${sparkline.length - 1} 10`} className="w-full h-full">
                <polyline
                  fill="none"
                  stroke={accent || 'var(--accent)'}
                  strokeWidth="1.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  points={sparkline
                    .map((val, idx) => {
                      const min = Math.min(...sparkline);
                      const max = Math.max(...sparkline);
                      const norm = max - min > 0 ? (val - min) / (max - min) : 0.5;
                      return `${idx},${10 - norm * 9}`;
                    })
                    .join(' ')}
                />
              </svg>
            </div>
          )}
        </div>
      )}
    </GlassCard>
  );
}

export default MetricCard;
