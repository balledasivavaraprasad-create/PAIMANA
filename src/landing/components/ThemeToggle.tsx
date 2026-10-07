import { useLandingTheme, type LandingTheme } from './ThemeContext';

const LABELS: Record<LandingTheme, string> = {
  dark: 'Dark theme',
  light: 'Light theme',
};

const NEXT_LABEL: Record<LandingTheme, string> = {
  dark: 'Switch to light theme',
  light: 'Switch to dark theme',
};

export default function ThemeToggle({ className = '' }: { className?: string }) {
  const { theme, toggleTheme } = useLandingTheme();

  return (
    <button
      type="button"
      className={`lp-theme-toggle ${className}`.trim()}
      onClick={toggleTheme}
      aria-label={NEXT_LABEL[theme]}
      title={NEXT_LABEL[theme]}
      data-theme-state={theme}
    >
      <span className="lp-theme-toggle__icon" aria-hidden="true">
        {theme === 'dark' ? (
          <svg width="15" height="15" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.4">
            <circle cx="8" cy="8" r="3.2" />
            <path
              d="M8 1v1.6M8 13.4V15M15 8h-1.6M2.6 8H1M12.95 3.05l-1.13 1.13M4.18 11.82l-1.13 1.13M12.95 12.95l-1.13-1.13M4.18 4.18L3.05 3.05"
              strokeLinecap="round"
            />
          </svg>
        ) : (
          <svg width="15" height="15" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.4">
            <path d="M13.5 9.6A5.8 5.8 0 016.4 2.5a5.8 5.8 0 107.1 7.1z" strokeLinejoin="round" />
          </svg>
        )}
      </span>
      <span className="lp-sr-only">{LABELS[theme]}</span>
    </button>
  );
}