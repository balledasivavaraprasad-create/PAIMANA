/**
 * Reduced-motion behaviour.
 *
 * `23_MOTION_SYSTEM.md` requires a static equivalent rather than simply
 * disabling animation. These tests assert that content still reaches its
 * final, complete state when motion is suppressed.
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { render, cleanup } from '@testing-library/react';
import LandingPage from '../pages/LandingPage';

/** Installs a matchMedia stub reporting the given query as matching. */
function stubMatchMedia(matching: (query: string) => boolean) {
  const original = window.matchMedia;

  Object.defineProperty(window, 'matchMedia', {
    configurable: true,
    writable: true,
    value: (query: string) => ({
      matches: matching(query),
      media: query,
      onchange: null,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      addListener: vi.fn(),
      removeListener: vi.fn(),
      dispatchEvent: vi.fn(),
    }),
  });

  return () => {
    Object.defineProperty(window, 'matchMedia', {
      configurable: true,
      writable: true,
      value: original,
    });
  };
}

describe('reduced motion', () => {
  let restore: () => void;

  beforeEach(() => {
    window.localStorage.clear();
    document.documentElement.removeAttribute('data-theme');
    restore = stubMatchMedia((query) => query.includes('prefers-reduced-motion'));
  });

  afterEach(() => {
    cleanup();
    restore();
    vi.useRealTimers();
  });

  it('still renders every section with its full content', () => {
    const { container } = render(<LandingPage />);

    // The story must be complete even when nothing animates.
    expect(container.querySelectorAll('section[id]').length).toBeGreaterThanOrEqual(11);

    // Peer section resolves to its final cohort rather than an empty field.
    const peers = container.querySelectorAll('.lp-cohort__peer[data-state="visible"]');
    expect(peers.length).toBeGreaterThanOrEqual(6);

    // Investigation resolves to a concluded state.
    expect(container.textContent).toMatch(/ready for review/i);

    // Governance still states the approval boundary.
    expect(container.textContent?.toLowerCase()).toMatch(/human-gated/);
  });

  it('does not leave content hidden behind scroll triggers', () => {
    const { container } = render(<LandingPage />);

    // Elements that animate in on scroll must not be permanently invisible.
    const animated = Array.from(
      container.querySelectorAll('.lp-pillar, .lp-governance__item, .lp-tech__layer, .lp-cta__panel'),
    );

    expect(animated.length).toBeGreaterThan(0);

    animated.forEach((element) => {
      const style = (element as HTMLElement).style;
      const inlineHidden = style.opacity === '0';
      const inlineCollapsed =
        style.transform !== '' && style.transform !== 'none' && style.transform.includes('translateY');
      expect(inlineHidden || inlineCollapsed).toBe(false);
    });
  });

  it('paints a settled hero field rather than an empty canvas', () => {
    const { container } = render(<LandingPage />);

    const canvas = container.querySelector('.lp-hero__canvas') as HTMLCanvasElement;
    expect(canvas).toBeTruthy();
    expect(canvas.getAttribute('aria-label')).toBeTruthy();

    // The visual carries an explicit conceptual label regardless of motion.
    expect(container.textContent?.toLowerCase()).toMatch(/conceptual visualisation/);
  });

  it('keeps the walkthrough readable and fully populated', () => {
    const { container } = render(<LandingPage />);

    const titles = Array.from(container.querySelectorAll('.lp-walkthrough__step-title')).map(
      (node) => node.textContent,
    );

    expect(titles).toEqual(['Monitor', 'Detect', 'Investigate', 'Decide', 'Learn']);
  });
});