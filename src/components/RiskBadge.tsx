import React from 'react';

export type RiskLevel = 'critical' | 'high' | 'moderate' | 'low';

interface RiskBadgeProps {
  level: RiskLevel;
  showGlow?: boolean;
  size?: 'sm' | 'md';
  className?: string;
}

export function RiskBadge({ level, size = 'sm', className = '' }: RiskBadgeProps) {
  const levelMap = {
    critical: {
      label: 'Elevated / High',
    },
    high: {
      label: 'High Priority',
    },
    moderate: {
      label: 'Standard',
    },
    low: {
      label: 'Baseline',
    },
  };

  const config = levelMap[level] || levelMap.low;
  const isSm = size === 'sm';

  return (
    <span
      className={`inline-flex items-center gap-1.5 font-semibold uppercase tracking-wider bg-white/10 text-white border border-white/20 font-mono-code ${className}`}
      style={{
        fontSize: isSm ? 13 : 14,
        padding: isSm ? '4px 10px' : '6px 14px',
        borderRadius: 8,
        letterSpacing: '0.05em',
      }}
    >
      <span className="w-1.5 h-1.5 rounded-full bg-white" />
      {config.label}
    </span>
  );
}

export default RiskBadge;
