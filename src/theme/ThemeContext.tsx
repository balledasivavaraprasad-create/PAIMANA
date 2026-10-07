import React, { createContext, useContext, useEffect, useState, useMemo } from 'react';
import { ThemeMode, ThemeTokens, darkThemeTokens, lightThemeTokens } from './tokens';

interface ThemeContextType {
  mode: ThemeMode;
  tokens: ThemeTokens;
  toggleTheme: () => void;
  setMode: (mode: ThemeMode) => void;
  getPlotlyLayout: (overrides?: Record<string, any>) => Record<string, any>;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export const ThemeProvider: React.FC<{ children: React.ReactNode; defaultMode?: ThemeMode }> = ({
  children,
  defaultMode = 'light',
}) => {
  const [mode, setModeState] = useState<ThemeMode>(() => {
    try {
      const stored = localStorage.getItem('infrabuild_theme');
      if (stored === 'light' || stored === 'dark') return stored;
    } catch (e) {
      // Local storage unavailable
    }
    return defaultMode;
  });

  useEffect(() => {
    try {
      localStorage.setItem('infrabuild_theme', mode);
    } catch (e) {
      // ignore
    }
    document.documentElement.setAttribute('data-theme', mode);
  }, [mode]);

  const toggleTheme = () => {
    setModeState((prev) => (prev === 'dark' ? 'light' : 'dark'));
  };

  const setMode = (newMode: ThemeMode) => {
    setModeState(newMode);
  };

  const tokens = useMemo(() => (mode === 'dark' ? darkThemeTokens : lightThemeTokens), [mode]);

  const getPlotlyLayout = (overrides?: Record<string, any>) => {
    const isDark = mode === 'dark';
    const baseMargin = { l: 60, r: 24, t: 24, b: 60, pad: 6 };
    const baseAxis = {
      automargin: true,
      zeroline: true,
      zerolinewidth: 1.5,
      zerolinecolor: isDark ? 'rgba(255, 255, 255, 0.22)' : 'rgba(0, 0, 0, 0.22)',
      gridcolor: isDark ? 'rgba(255, 255, 255, 0.07)' : 'rgba(0, 0, 0, 0.07)',
      tickfont: { color: isDark ? '#94A3B8' : '#475569', size: 10.5 },
      title: {
        font: { color: isDark ? '#E2E8F0' : '#1E293B', size: 11.5 },
        standoff: 10,
      },
    };

    const mergedMargin = {
      ...baseMargin,
      ...(overrides?.margin || {}),
    };

    const mergedXaxis = {
      ...baseAxis,
      ...(overrides?.xaxis || {}),
      title: {
        ...baseAxis.title,
        ...(typeof overrides?.xaxis?.title === 'string'
          ? { text: overrides.xaxis.title }
          : overrides?.xaxis?.title || {}),
      },
      tickfont: {
        ...baseAxis.tickfont,
        ...(overrides?.xaxis?.tickfont || {}),
      },
    };

    const mergedYaxis = {
      ...baseAxis,
      ...(overrides?.yaxis || {}),
      title: {
        ...baseAxis.title,
        ...(typeof overrides?.yaxis?.title === 'string'
          ? { text: overrides.yaxis.title }
          : overrides?.yaxis?.title || {}),
      },
      tickfont: {
        ...baseAxis.tickfont,
        ...(overrides?.yaxis?.tickfont || {}),
      },
    };

    return {
      autosize: true,
      paper_bgcolor: 'transparent',
      plot_bgcolor: 'transparent',
      font: {
        family: "-apple-system, BlinkMacSystemFont, 'Plus Jakarta Sans', 'Inter', 'Segoe UI', Roboto, sans-serif",
        color: isDark ? '#94A3B8' : '#475569',
        size: 11,
        ...(overrides?.font || {}),
      },
      legend: {
        font: { color: isDark ? '#94A3B8' : '#475569', size: 10 },
        bgcolor: 'transparent',
        ...(overrides?.legend || {}),
      },
      hoverlabel: {
        bgcolor: isDark ? '#1E293B' : '#FFFFFF',
        bordercolor: isDark ? '#334155' : '#CBD5E1',
        font: {
          family: "-apple-system, BlinkMacSystemFont, 'Plus Jakarta Sans', 'Inter', 'Segoe UI', Roboto, sans-serif",
          color: isDark ? '#F8FAFC' : '#0F172A',
          size: 11,
        },
        ...(overrides?.hoverlabel || {}),
      },
      ...overrides,
      margin: mergedMargin,
      xaxis: mergedXaxis,
      yaxis: mergedYaxis,
    };
  };

  return (
    <ThemeContext.Provider value={{ mode, tokens, toggleTheme, setMode, getPlotlyLayout }}>
      {children}
    </ThemeContext.Provider>
  );
};

export const useTheme = (): ThemeContextType => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
};
