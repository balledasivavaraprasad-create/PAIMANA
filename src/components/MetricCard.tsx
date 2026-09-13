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
          <span className="text-xs md:text-sm font-semibold uppercase tracking-wider text-white/70">
            {label}
          </span>
          {icon && <div className="text-white/70 opacity-80">{icon}</div>}
        </div>

        <div
          className="text-2xl md:text-3xl font-bold font-display tracking-tight font-mono-data text-white"
        >
          {value}
        </div>
      </div>

      {(sub || trend || sparkline) && (
        <div className="mt-3 pt-2.5 border-t border-white/15 flex items-center justify-between">
          {sub && (
            <div className="text-xs md:text-sm text-white/80 flex items-center gap-1.5">
              {trend === 'up' && <span className="text-white font-bold">↑</span>}
              {trend === 'down' && <span className="text-white font-bold">↓</span>}
              <span>{sub}</span>
            </div>
          )}

          {sparkline && sparkline.length > 1 && (
            <div className="w-16 h-5">
              <svg viewBox={`0 0 ${sparkline.length - 1} 10`} className="w-full h-full">
                <polyline
                  fill="none"
                  stroke="#ffffff"
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
