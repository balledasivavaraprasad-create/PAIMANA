import React from 'react';

interface GlassCardProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  variant?: 'subtle' | 'medium' | 'hero' | 'sunken';
  className?: string;
  padding?: string | number;
  borderRadius?: number | string;
}

export function GlassCard({
  children,
  variant = 'medium',
  className = '',
  padding = 20,
  borderRadius = 12,
  style,
  ...props
}: GlassCardProps) {
  const getVariantClass = () => {
    switch (variant) {
      case 'hero':
        return 'glass-hero';
      case 'subtle':
        return 'glass-panel opacity-90';
      case 'sunken':
        return 'bg-[var(--surface-sunken)] border border-[var(--border-hairline)]';
      default:
        return 'glass-panel';
    }
  };

  return (
    <div
      className={`${getVariantClass()} ${className}`}
      style={{
        padding,
        borderRadius,
        ...style,
      }}
      {...props}
    >
      {children}
    </div>
  );
}

export default GlassCard;
