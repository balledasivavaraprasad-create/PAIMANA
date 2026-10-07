import React, { useState, useEffect } from 'react';

export const Navigation: React.FC<{ onOpenPlatform: () => void }> = ({ onOpenPlatform }) => {
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 30);
    };
    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const scrollToSection = (id: string) => {
    const el = document.getElementById(id);
    if (el) {
      el.scrollIntoView({ behavior: 'smooth' });
    }
  };

  const [currentMode, setCurrentMode] = useState<'dark' | 'light'>(() => {
    if (typeof document !== 'undefined') {
      const mode = document.documentElement.getAttribute('data-theme');
      if (mode === 'dark' || mode === 'light') return mode;
    }
    return 'light';
  });

  const toggleLandingTheme = () => {
    const next = currentMode === 'dark' ? 'light' : 'dark';
    setCurrentMode(next);
    document.documentElement.setAttribute('data-theme', next);
    document.documentElement.style.colorScheme = next;
    try {
      localStorage.setItem('paimana-theme', next);
      localStorage.setItem('infrabuild_theme', next);
      localStorage.setItem('infrabuild-landing.theme', next);
    } catch (e) {}
  };

  return (
    <div
      className="el-nav-container"
      style={{
        position: 'fixed',
        top: '24px',
        left: '50%',
        transform: 'translateX(-50%)',
        width: 'max-content',
        maxWidth: 'calc(100vw - 32px)',
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        zIndex: 1000,
        pointerEvents: 'none',
      }}
    >
      <nav
        className="el-nav-pill"
        style={{
          margin: '0 auto',
          pointerEvents: 'auto',
          transform: scrolled ? 'scale(0.97)' : 'scale(1)',
          boxShadow: scrolled
            ? '0 16px 40px -4px rgba(0, 0, 0, 0.45), 0 2px 6px rgba(0, 0, 0, 0.2)'
            : '0 10px 30px -4px rgba(0, 0, 0, 0.35)',
        }}
      >
        {/* Left: Product Mark */}
        <a
          href="#hero"
          onClick={(e) => {
            e.preventDefault();
            scrollToSection('hero');
          }}
          className="el-nav-logo"
        >
          <div className="el-nav-mark">▲</div>
          <span>
            <span style={{ fontWeight: 700 }}>InfraBuild</span>{' '}
            <span style={{ opacity: 0.85, fontWeight: 600, color: '#38BDF8' }}>AI</span>
          </span>
        </a>

        {/* Middle Navigation Links */}
        <ul className="el-nav-links">
          <li>
            <a
              href="#problem"
              onClick={(e) => {
                e.preventDefault();
                scrollToSection('problem');
              }}
              className="el-nav-link"
            >
              Risk Pattern
            </a>
          </li>
          <li>
            <a
              href="#monitoring"
              onClick={(e) => {
                e.preventDefault();
                scrollToSection('monitoring');
              }}
              className="el-nav-link"
            >
              Surveillance
            </a>
          </li>
          <li>
            <a
              href="#peers"
              onClick={(e) => {
                e.preventDefault();
                scrollToSection('peers');
              }}
              className="el-nav-link"
            >
              Peer Cohorts
            </a>
          </li>
          <li>
            <a
              href="#analytics"
              onClick={(e) => {
                e.preventDefault();
                scrollToSection('analytics');
              }}
              className="el-nav-link"
            >
              Workstation
            </a>
          </li>
          <li>
            <a
              href="#how-it-works"
              onClick={(e) => {
                e.preventDefault();
                scrollToSection('how-it-works');
              }}
              className="el-nav-link"
            >
              System Loop
            </a>
          </li>
        </ul>

        {/* Right CTA & Theme Toggle */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <button
            type="button"
            onClick={toggleLandingTheme}
            title={`Switch to ${currentMode === 'dark' ? 'Light' : 'Dark'} Mode`}
            aria-label="Toggle Theme"
            style={{
              width: '32px',
              height: '32px',
              borderRadius: '50%',
              backgroundColor: 'rgba(255, 255, 255, 0.10)',
              border: '1px solid rgba(255, 255, 255, 0.18)',
              color: '#FFFFFF',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              cursor: 'pointer',
              fontSize: '13px',
              transition: 'all 0.2s ease',
            }}
          >
            {currentMode === 'dark' ? '☀️' : '🌙'}
          </button>
          <button
            type="button"
            onClick={onOpenPlatform}
            className="el-nav-cta"
          >
            Sign In →
          </button>
        </div>
      </nav>
    </div>
  );
};
