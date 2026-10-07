export type ThemeMode = 'dark' | 'light';

export interface ThemeTokens {
  mode: ThemeMode;
  bg: {
    base: string;
    subtle: string;
    panel: string;
    elevated: string;
    inset: string;
    overlay: string;
    commandBg: string;
  };
  text: {
    primary: string;
    secondary: string;
    muted: string;
    inverse: string;
    link: string;
  };
  border: {
    subtle: string;
    default: string;
    strong: string;
    focus: string;
  };
  semantic: {
    healthy: {
      bg: string;
      text: string;
      border: string;
      solid: string;
    };
    attention: {
      bg: string;
      text: string;
      border: string;
      solid: string;
    };
    highRisk: {
      bg: string;
      text: string;
      border: string;
      solid: string;
    };
    critical: {
      bg: string;
      text: string;
      border: string;
      solid: string;
    };
    intelligence: {
      bg: string;
      text: string;
      border: string;
      solid: string;
    };
    agentic: {
      bg: string;
      text: string;
      border: string;
      solid: string;
    };
    neutral: {
      bg: string;
      text: string;
      border: string;
      solid: string;
    };
  };
  chart: {
    paperBg: string;
    plotBg: string;
    textColor: string;
    gridColor: string;
    zeroLineColor: string;
    lineColors: string[];
  };
}

export const darkThemeTokens: ThemeTokens = {
  mode: 'dark',
  bg: {
    base: '#0B0F19',
    subtle: '#0F172A',
    panel: '#0E1526',
    elevated: '#16223A',
    inset: '#080C16',
    overlay: 'rgba(7, 10, 18, 0.88)',
    commandBg: '#0E1526',
  },
  text: {
    primary: '#F8FAFC',
    secondary: '#CBD5E1',
    muted: '#94A3B8',
    inverse: '#070A12',
    link: '#38BDF8',
  },
  border: {
    subtle: 'rgba(255, 255, 255, 0.09)',
    default: 'rgba(255, 255, 255, 0.16)',
    strong: 'rgba(255, 255, 255, 0.28)',
    focus: '#38BDF8',
  },
  semantic: {
    healthy: {
      bg: 'rgba(16, 185, 129, 0.16)',
      text: '#34D399',
      border: 'rgba(16, 185, 129, 0.35)',
      solid: '#10B981',
    },
    attention: {
      bg: 'rgba(245, 158, 11, 0.16)',
      text: '#FBBF24',
      border: 'rgba(245, 158, 11, 0.35)',
      solid: '#F59E0B',
    },
    highRisk: {
      bg: 'rgba(249, 115, 22, 0.18)',
      text: '#FB923C',
      border: 'rgba(249, 115, 22, 0.36)',
      solid: '#F97316',
    },
    critical: {
      bg: 'rgba(239, 68, 68, 0.18)',
      text: '#F87171',
      border: 'rgba(239, 68, 68, 0.38)',
      solid: '#EF4444',
    },
    intelligence: {
      bg: 'rgba(56, 189, 248, 0.16)',
      text: '#38BDF8',
      border: 'rgba(56, 189, 248, 0.35)',
      solid: '#0284C7',
    },
    agentic: {
      bg: 'rgba(168, 85, 247, 0.16)',
      text: '#C084FC',
      border: 'rgba(168, 85, 247, 0.35)',
      solid: '#A855F7',
    },
    neutral: {
      bg: 'rgba(148, 163, 184, 0.14)',
      text: '#CBD5E1',
      border: 'rgba(148, 163, 184, 0.25)',
      solid: '#64748B',
    },
  },
  chart: {
    paperBg: 'transparent',
    plotBg: 'transparent',
    textColor: '#CBD5E1',
    gridColor: 'rgba(255, 255, 255, 0.08)',
    zeroLineColor: 'rgba(255, 255, 255, 0.18)',
    lineColors: ['#FFFFFF', '#38BDF8', '#FBBF24', '#34D399', '#F87171', '#C084FC'],
  },
};

export const lightThemeTokens: ThemeTokens = {
  mode: 'light',
  bg: {
    base: '#F8FAFC',
    subtle: '#F1F5F9',
    panel: '#FFFFFF',
    elevated: '#FFFFFF',
    inset: '#F1F5F9',
    overlay: 'rgba(15, 23, 42, 0.4)',
    commandBg: '#FFFFFF',
  },
  text: {
    primary: '#0F172A',
    secondary: '#475569',
    muted: '#64748B',
    inverse: '#F8FAFC',
    link: '#0284C7',
  },
  border: {
    subtle: '#E2E8F0',
    default: '#CBD5E1',
    strong: '#94A3B8',
    focus: '#0284C7',
  },
  semantic: {
    healthy: {
      bg: '#DCFCE7',
      text: '#15803D',
      border: '#BBF7D0',
      solid: '#16A34A',
    },
    attention: {
      bg: '#FEF3C7',
      text: '#B45309',
      border: '#FDE68A',
      solid: '#D97706',
    },
    highRisk: {
      bg: '#FFEDD5',
      text: '#C2410C',
      border: '#FED7AA',
      solid: '#EA580C',
    },
    critical: {
      bg: '#FEE2E2',
      text: '#B91C1C',
      border: '#FECACA',
      solid: '#DC2626',
    },
    intelligence: {
      bg: '#E0F2FE',
      text: '#0369A1',
      border: '#BAE6FD',
      solid: '#0284C7',
    },
    agentic: {
      bg: '#F3E8FF',
      text: '#7E22CE',
      border: '#E9D5FF',
      solid: '#9333EA',
    },
    neutral: {
      bg: '#F1F5F9',
      text: '#475569',
      border: '#E2E8F0',
      solid: '#64748B',
    },
  },
  chart: {
    paperBg: 'transparent',
    plotBg: 'transparent',
    textColor: '#475569',
    gridColor: 'rgba(0, 0, 0, 0.06)',
    zeroLineColor: 'rgba(0, 0, 0, 0.12)',
    lineColors: ['#0284C7', '#7E22CE', '#D97706', '#16A34A', '#DC2626', '#2563EB'],
  },
};
