import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react';

import { prefersLightScheme } from '../motion/env';

export type LandingTheme = 'dark' | 'light';

export const THEME_STORAGE_KEY = 'infrabuild-landing.theme';

interface ThemeContextValue {
  theme: LandingTheme;
  setTheme: (theme: LandingTheme) => void;
  toggleTheme: () => void;
}

const ThemeContext = createContext<ThemeContextValue | null>(null);

interface ThemeProviderProps {
  children: ReactNode;
  /** Class applied to the scoped theme root. */
  className?: string;
}

/**
 * Owns theme state for the public landing experience only.
 *
 * Deliberately does NOT touch `document.documentElement` or any global token
 * layer: the authenticated application shell owns document-level theming.
 * Theme is applied to this subtree only so the two experiences cannot clobber
 * each other when they are mounted in the same document.
 */
export function ThemeProvider({ children, className }: ThemeProviderProps) {
  const [theme, setThemeState] = useState<LandingTheme>('dark');

  useEffect(() => {
    let initial: LandingTheme;
    try {
      const stored = window.localStorage.getItem(THEME_STORAGE_KEY);
      initial =
        stored === 'dark' || stored === 'light' ? stored : prefersLightScheme() ? 'light' : 'dark';
    } catch {
      // Private browsing / storage disabled — fall back to the OS preference.
      initial = prefersLightScheme() ? 'light' : 'dark';
    }
    setThemeState(initial);
  }, []);

  const setTheme = useCallback((next: LandingTheme) => {
    setThemeState(next);
    try {
      window.localStorage.setItem(THEME_STORAGE_KEY, next);
    } catch {
      // Persistence is best-effort; the session still works without it.
    }
  }, []);

  const toggleTheme = useCallback(() => {
    setThemeState((current) => {
      const next = current === 'dark' ? 'light' : 'dark';
      try {
        window.localStorage.setItem(THEME_STORAGE_KEY, next);
      } catch {
        /* ignore */
      }
      return next;
    });
  }, []);

  const value = useMemo<ThemeContextValue>(
    () => ({ theme, setTheme, toggleTheme }),
    [theme, setTheme, toggleTheme],
  );

  return (
    <ThemeContext.Provider value={value}>
      <div className={className} data-theme={theme}>
        {children}
      </div>
    </ThemeContext.Provider>
  );
}

export function useLandingTheme(): ThemeContextValue {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useLandingTheme must be used within a ThemeProvider');
  }
  return context;
}