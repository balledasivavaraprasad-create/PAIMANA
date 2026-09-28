import React from 'react';

/**
 * Custom Curved Growth Arrow SVG path based on smooth curved reference geometry.
 * Curves upward to the right with an organic S-flow.
 */
export const CURVED_GROWTH_PATH =
  'M 3.22 19.14 L 2.47 19.00 L 2.04 18.37 L 2.19 17.66 L 2.71 17.08 L 3.23 16.51 L 3.78 15.95 L 4.37 15.41 L 4.98 14.91 L 5.63 14.47 L 6.31 14.11 L 7.02 13.83 L 7.76 13.62 L 8.52 13.48 L 9.30 13.39 L 10.10 13.35 L 10.91 13.34 L 11.71 13.32 L 12.47 13.22 L 13.20 13.02 L 13.90 12.73 L 14.58 12.35 L 15.18 11.89 L 15.66 11.34 L 16.14 10.87 L 16.51 10.39 L 16.70 9.83 L 16.72 9.43 L 16.43 8.96 L 15.93 8.65 L 15.42 8.07 L 15.51 7.33 L 16.11 6.82 L 16.50 6.41 L 17.17 6.06 L 17.64 5.90 L 17.87 5.70 L 18.34 5.48 L 18.65 5.23 L 19.05 5.06 L 19.52 5.00 L 20.25 4.87 L 20.86 5.12 L 21.09 5.70 L 21.35 6.25 L 21.43 6.89 L 21.56 7.62 L 21.69 8.33 L 21.84 9.07 L 22.00 9.85 L 21.70 10.53 L 20.96 10.72 L 20.31 10.26 L 20.04 9.87 L 19.43 9.89 L 19.02 10.54 L 18.60 11.20 L 18.15 11.85 L 17.66 12.46 L 17.12 13.04 L 16.53 13.56 L 15.90 14.03 L 15.24 14.43 L 14.56 14.75 L 13.84 15.00 L 13.10 15.19 L 12.32 15.31 L 11.52 15.36 L 10.70 15.37 L 9.89 15.38 L 9.08 15.43 L 8.31 15.55 L 7.58 15.76 L 6.88 16.07 L 6.23 16.48 L 5.61 16.98 L 5.03 17.55 L 4.45 18.14 L 3.87 18.71 L 3.22 19.14 Z';

/**
 * Custom Curved Decrease Arrow SVG path based on smooth curved reference geometry.
 * Curves downward to the right with an organic sweep.
 */
export const CURVED_DECREASE_PATH =
  'M 17.32 19.19 L 16.59 19.09 L 16.14 18.53 L 16.22 17.81 L 16.82 17.36 L 17.41 17.08 L 17.11 16.70 L 16.47 16.33 L 15.83 15.96 L 15.20 15.53 L 14.59 15.04 L 14.03 14.52 L 13.51 13.98 L 13.02 13.41 L 12.55 12.82 L 12.10 12.23 L 11.66 11.62 L 11.22 11.01 L 10.77 10.39 L 10.31 9.78 L 9.83 9.19 L 9.32 8.63 L 8.77 8.13 L 8.17 7.72 L 7.51 7.41 L 6.80 7.20 L 6.05 7.08 L 5.28 7.03 L 4.49 7.02 L 3.70 7.05 L 2.94 7.02 L 2.28 6.69 L 1.98 6.02 L 2.17 5.30 L 2.73 4.86 L 3.48 4.77 L 4.27 4.78 L 5.07 4.78 L 5.84 4.79 L 6.60 4.82 L 7.34 4.93 L 8.05 5.11 L 8.74 5.39 L 9.39 5.73 L 10.01 6.15 L 10.58 6.64 L 11.11 7.18 L 11.60 7.76 L 12.06 8.36 L 12.51 8.98 L 12.94 9.60 L 13.36 10.21 L 13.80 10.81 L 14.24 11.40 L 14.72 11.99 L 15.22 12.56 L 15.75 13.11 L 16.32 13.62 L 16.92 14.08 L 17.56 14.48 L 18.21 14.81 L 18.88 15.05 L 19.28 14.89 L 19.25 14.09 L 19.53 13.38 L 20.22 13.16 L 20.88 13.43 L 21.22 14.03 L 21.38 14.79 L 21.52 15.53 L 21.68 16.22 L 21.86 16.94 L 21.97 17.70 L 21.66 18.29 L 21.02 18.62 L 20.28 18.76 L 19.53 18.82 L 18.79 18.94 L 18.06 19.10 L 17.32 19.19 Z';

interface ArrowProps {
  className?: string;
  color?: string;
  style?: React.CSSProperties;
}

export function CurvedGrowthArrow({
  className = 'w-4 h-4',
  color = 'currentColor',
  style
}: ArrowProps) {
  return (
    <svg
      viewBox="0 0 24 24"
      className={`inline-block shrink-0 transition-transform ${className}`}
      style={style}
      fill={color}
      xmlns="http://www.w3.org/2000/svg"
      aria-label="Growth / Upward Trend"
    >
      <path d={CURVED_GROWTH_PATH} />
    </svg>
  );
}

export function CurvedDecreaseArrow({
  className = 'w-4 h-4',
  color = 'currentColor',
  style
}: ArrowProps) {
  return (
    <svg
      viewBox="0 0 24 24"
      className={`inline-block shrink-0 transition-transform ${className}`}
      style={style}
      fill={color}
      xmlns="http://www.w3.org/2000/svg"
      aria-label="Decrease / Downward Trend"
    >
      <path d={CURVED_DECREASE_PATH} />
    </svg>
  );
}

export interface TrendBadgeProps {
  value: string | number;
  direction?: 'up' | 'down' | 'auto';
  /**
   * 'risk': up is amber/red (higher risk), down is green (lowers risk)
   * 'progress': up is green (higher completion), down is red
   * 'neutral': up is white/slate, down is white/slate
   */
  mode?: 'risk' | 'progress' | 'neutral';
  suffix?: string;
  prefix?: string;
  className?: string;
  iconClassName?: string;
  badge?: boolean;
}

export function TrendBadge({
  value,
  direction = 'auto',
  mode = 'risk',
  suffix = '',
  prefix = '',
  className = '',
  iconClassName = 'w-3.5 h-3.5',
  badge = true
}: TrendBadgeProps) {
  const strVal = String(value);
  const numVal = typeof value === 'number' ? value : parseFloat(strVal.replace(/[^\d.-]/g, ''));

  const isUp =
    direction === 'up' ||
    (direction === 'auto' && (strVal.startsWith('+') || (!strVal.startsWith('-') && numVal > 0)));

  // Color styles depending on mode
  let textClass = 'text-white';
  let badgeClass = 'bg-white/10 border-white/20 text-white';

  if (mode === 'risk') {
    if (isUp) {
      textClass = 'text-amber-400';
      badgeClass = 'bg-amber-500/15 border-amber-500/30 text-amber-300';
    } else {
      textClass = 'text-emerald-400';
      badgeClass = 'bg-emerald-500/15 border-emerald-500/30 text-emerald-300';
    }
  } else if (mode === 'progress') {
    if (isUp) {
      textClass = 'text-emerald-400';
      badgeClass = 'bg-emerald-500/15 border-emerald-500/30 text-emerald-300';
    } else {
      textClass = 'text-rose-400';
      badgeClass = 'bg-rose-500/15 border-rose-500/30 text-rose-300';
    }
  }

  const ArrowIcon = isUp ? CurvedGrowthArrow : CurvedDecreaseArrow;

  if (!badge) {
    return (
      <span className={`inline-flex items-center gap-1 font-mono font-bold ${textClass} ${className}`}>
        <ArrowIcon className={iconClassName} />
        <span>{prefix}{strVal}{suffix}</span>
      </span>
    );
  }

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-lg border text-xs font-mono font-bold shadow-sm ${badgeClass} ${className}`}
    >
      <ArrowIcon className={iconClassName} />
      <span>{prefix}{strVal}{suffix}</span>
    </span>
  );
}
