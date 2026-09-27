export type RiskLevel = 'critical' | 'high' | 'moderate' | 'low';

export interface RiskCategory {
  level: RiskLevel;
  label: string;       // Plain language: "ON TRACK", "NEEDS ATTENTION", "HIGH RISK", "CRITICAL"
  badgeText: string;   // "On Track", "Needs Attention", "High Risk", "Critical"
  colorClass: string;
  bgClass: string;
  borderClass: string;
  badgeBg: string;     // Color badge style
  description: string;
}

/**
 * Single global source of truth for Risk Classification
 * 0  - 44: Low / ON TRACK
 * 45 - 64: Moderate / NEEDS ATTENTION
 * 65 - 79: High / HIGH RISK
 * 80 - 100: Critical / CRITICAL
 */
export function getRiskCategory(scoreOrLevel: number | string | undefined | null): RiskCategory {
  let score = 50;
  if (typeof scoreOrLevel === 'number') {
    score = scoreOrLevel;
  } else if (typeof scoreOrLevel === 'string') {
    const sLower = scoreOrLevel.toLowerCase().trim();
    if (sLower === 'critical') score = 85;
    else if (sLower === 'high') score = 72;
    else if (sLower === 'moderate' || sLower === 'medium') score = 55;
    else if (sLower === 'low') score = 25;
    else {
      const parsed = parseFloat(sLower);
      if (!isNaN(parsed)) score = parsed;
    }
  }

  if (score >= 80) {
    return {
      level: 'critical',
      label: 'CRITICAL',
      badgeText: 'Critical Risk',
      colorClass: 'text-red-500',
      bgClass: 'bg-red-500/15',
      borderClass: 'border-red-500/30',
      badgeBg: 'bg-red-500/20 text-red-400 border-red-500/40',
      description: 'Severe schedule or expenditure divergence requiring immediate action.'
    };
  }
  if (score >= 65) {
    return {
      level: 'high',
      label: 'HIGH RISK',
      badgeText: 'High Risk',
      colorClass: 'text-orange-500',
      bgClass: 'bg-orange-500/15',
      borderClass: 'border-orange-500/30',
      badgeBg: 'bg-orange-500/20 text-orange-400 border-orange-500/40',
      description: 'Progress is significantly behind planned milestones.'
    };
  }
  if (score >= 45) {
    return {
      level: 'moderate',
      label: 'NEEDS ATTENTION',
      badgeText: 'Needs Attention',
      colorClass: 'text-amber-500',
      bgClass: 'bg-amber-500/15',
      borderClass: 'border-amber-500/30',
      badgeBg: 'bg-amber-500/20 text-amber-400 border-amber-500/40',
      description: 'Milestones slipping or spending ahead of physical progress.'
    };
  }
  return {
    level: 'low',
    label: 'ON TRACK',
    badgeText: 'On Track',
    colorClass: 'text-emerald-500',
    bgClass: 'bg-emerald-500/15',
    borderClass: 'border-emerald-500/30',
    badgeBg: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/40',
    description: 'Work and disbursements progressing according to plan.'
  };
}
