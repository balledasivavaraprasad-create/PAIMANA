import { useSyncExternalStore } from 'react';

export type Theme = 'light' | 'dark';

function getInitialTheme(): Theme {
  if (typeof window !== 'undefined') {
    const saved = localStorage.getItem('paimana-theme') as Theme;
    if (saved === 'light' || saved === 'dark') return saved;
    if (window.matchMedia('(prefers-color-scheme: dark)').matches) return 'dark';
  }
  return 'light';
}

let currentTheme: Theme = getInitialTheme();
const listeners = new Set<() => void>();

function emitChange() {
  if (typeof window !== 'undefined') {
    document.documentElement.setAttribute('data-theme', currentTheme);
    try {
      localStorage.setItem('paimana-theme', currentTheme);
    } catch {
      // Ignore storage errors
    }
  }
  for (const listener of listeners) {
    listener();
  }
}

// Apply initial data-theme attribute to <html> root immediately
if (typeof window !== 'undefined') {
  document.documentElement.setAttribute('data-theme', currentTheme);
}

export function useTheme() {
  const theme = useSyncExternalStore(
    (callback) => {
      listeners.add(callback);
      return () => {
        listeners.delete(callback);
      };
    },
    () => currentTheme,
    () => 'light'
  );

  const setTheme = (newTheme: Theme) => {
    if (currentTheme !== newTheme) {
      currentTheme = newTheme;
      emitChange();
    }
  };

  const toggleTheme = () => {
    currentTheme = currentTheme === 'light' ? 'dark' : 'light';
    emitChange();
  };

  return { theme, setTheme, toggleTheme };
}
