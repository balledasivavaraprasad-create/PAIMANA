import React from 'react';

export type RiskLevel = 'critical' | 'high' | 'moderate' | 'low';

interface RiskBadgeProps {
  level: RiskLevel;
  showGlow?: boolean;
  size?: 'sm' | 'md';
  className?: string;
}

export function RiskBadge({ level, showGlow = false, size = 'sm', className = '' }: RiskBadgeProps) {
  const levelMap = {
    critical: {
      color: 'var(--risk-critical)',
      bg: 'var(--risk-critical-bg)',
      border: 'var(--risk-critical-border)',
      label: 'Critical',
    },
    high: {
      color: 'var(--risk-high)',
      bg: 'var(--risk-high-bg)',
      border: 'var(--risk-high-border)',
      label: 'High Risk',
    },
    moderate: {
      color: 'var(--risk-moderate)',
      bg: 'var(--risk-moderate-bg)',
      border: 'var(--risk-moderate-border)',
      label: 'Moderate',
    },
    low: {
      color: 'var(--risk-low)',
      bg: 'var(--risk-low-bg)',
      border: 'var(--risk-low-border)',
      label: 'Low Risk',
    },
  };

  const config = levelMap[level] || levelMap.low;
  const isSm = size === 'sm';

  return (
    <span
      className={`inline-flex items-center gap-1.5 font-semibold uppercase tracking-wider ${className}`}
      style={{
        background: config.bg,
        color: config.color,
        border: `1px solid ${config.border}`,
        fontSize: isSm ? 10 : 11,
        padding: isSm ? '2px 8px' : '4px 10px',
        borderRadius: 6,
        letterSpacing: '0.05em',
        boxShadow: showGlow ? `0 0 12px ${config.bg}` : 'none',
      }}
    >
      <span
        style={{
          width: 5,
          height: 5,
          borderRadius: '50%',
          background: config.color,
          boxShadow: showGlow ? `0 0 6px ${config.color}` : 'none',
        }}
      />
      {config.label}
    </span>
  );
}

export default RiskBadge;
