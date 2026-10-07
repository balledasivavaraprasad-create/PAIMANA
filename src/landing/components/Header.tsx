import { useCallback, useEffect, useRef, useState } from 'react';
import { NAV_LINKS } from '../data/content';
import { safeMatchMedia } from '../motion/env';
import ThemeToggle from './ThemeToggle';

/**
 * Sticky header.
 *
 * Transparent and immersive at the top of the page, then contracts into an
 * elevated, compact bar once the hero is behind the user. Height and blur
 * transition together so the change reads as one movement.
 */
export default function Header() {
  const [scrolled, setScrolled] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const mobilePanelRef = useRef<HTMLDivElement>(null);
  const toggleRef = useRef<HTMLButtonElement>(null);
  const firstLinkRef = useRef<HTMLAnchorElement>(null);

  useEffect(() => {
    let frame = 0;
    const onScroll = () => {
      if (frame) return;
      frame = requestAnimationFrame(() => {
        frame = 0;
        setScrolled(window.scrollY > 20);
      });
    };
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => {
      window.removeEventListener('scroll', onScroll);
      if (frame) cancelAnimationFrame(frame);
    };
  }, []);

  // Close the mobile menu on Escape and return focus to the trigger.
  useEffect(() => {
    if (!mobileOpen) return;
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setMobileOpen(false);
        toggleRef.current?.focus();
      }
    };
    document.addEventListener('keydown', onKeyDown);
    return () => document.removeEventListener('keydown', onKeyDown);
  }, [mobileOpen]);

  // Move focus into the panel when it opens so keyboard users are not stranded.
  useEffect(() => {
    if (mobileOpen) {
      firstLinkRef.current?.focus();
    }
  }, [mobileOpen]);

  // A resize past the breakpoint should not leave an orphaned open panel.
  useEffect(() => {
    const mq = safeMatchMedia('(min-width: 901px)');
    if (!mq) return;

    const onChange = (event: MediaQueryListEvent) => {
      if (event.matches) setMobileOpen(false);
    };

    if (typeof mq.addEventListener === 'function') {
      mq.addEventListener('change', onChange);
      return () => mq.removeEventListener?.('change', onChange);
    }
    mq.addListener?.(onChange);
    return () => mq.removeListener?.(onChange);
  }, []);

  const closeMenu = useCallback(() => setMobileOpen(false), []);

  return (
    <header className={`lp-header${scrolled ? ' lp-header--scrolled' : ''}`}>
      <div className="lp-header__inner">
        <a href="/" className="lp-header__logo" aria-label="InfraBuild-AI — home">
          <span className="lp-header__logo-icon" aria-hidden="true">
            <svg width="15" height="15" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5">
              <path d="M2 12.5V5.5L8 2l6 3.5v7" strokeLinejoin="round" />
              <path d="M5.5 12.5v-4h5v4" strokeLinejoin="round" />
            </svg>
          </span>
          <span className="lp-header__wordmark">
            InfraBuild <span className="lp-header__wordmark-accent">AI</span>
          </span>
        </a>

        <nav className="lp-header__nav" aria-label="Primary">
          {NAV_LINKS.map((link) => (
            <a key={link.label} href={link.href} className="lp-header__nav-link">
              {link.label}
            </a>
          ))}
        </nav>

        <div className="lp-header__actions">
          <ThemeToggle className="lp-header__theme" />
          <a href="#signin" className="lp-header__signin">
            Sign in
          </a>
          <a href="#access" className="lp-header__cta">
            Request access
          </a>
          <button
            ref={toggleRef}
            type="button"
            className="lp-header__menu-btn"
            onClick={() => setMobileOpen((open) => !open)}
            aria-expanded={mobileOpen}
            aria-controls="lp-mobile-nav"
          >
            <span className="lp-sr-only">{mobileOpen ? 'Close navigation' : 'Open navigation'}</span>
            <svg width="18" height="18" viewBox="0 0 18 18" fill="none" stroke="currentColor" strokeWidth="1.5" aria-hidden="true">
              {mobileOpen ? (
                <path d="M4.5 4.5l9 9M13.5 4.5l-9 9" strokeLinecap="round" />
              ) : (
                <path d="M3 5.5h12M3 9h12M3 12.5h12" strokeLinecap="round" />
              )}
            </svg>
          </button>
        </div>
      </div>

      <div
        id="lp-mobile-nav"
        ref={mobilePanelRef}
        className={`lp-header__mobile-menu${mobileOpen ? ' lp-header__mobile-menu--open' : ''}`}
        hidden={!mobileOpen}
      >
        {NAV_LINKS.map((link, index) => (
          <a
            key={link.label}
            ref={index === 0 ? firstLinkRef : undefined}
            href={link.href}
            className="lp-header__mobile-link"
            onClick={closeMenu}
            tabIndex={mobileOpen ? 0 : -1}
          >
            {link.label}
          </a>
        ))}
        <div className="lp-header__mobile-divider" aria-hidden="true" />
        <a
          href="#signin"
          className="lp-header__mobile-link"
          onClick={closeMenu}
          tabIndex={mobileOpen ? 0 : -1}
        >
          Sign in
        </a>
        <a
          href="#access"
          className="lp-header__mobile-link lp-header__mobile-link--cta"
          onClick={closeMenu}
          tabIndex={mobileOpen ? 0 : -1}
        >
          Request access
        </a>
      </div>
    </header>
  );
}