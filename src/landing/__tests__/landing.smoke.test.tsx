/**
 * Landing page smoke tests.
 *
 * Verifies the public experience mounts, that its accessible structure is
 * intact, and — importantly — that it does not write to document-level theme
 * state owned by the authenticated application shell.
 */

import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { render, screen, cleanup } from '@testing-library/react';
import LandingPage from '../pages/LandingPage';

describe('LandingPage', () => {
  beforeEach(() => {
    window.localStorage.clear();
    document.documentElement.removeAttribute('data-theme');
  });

  afterEach(() => {
    cleanup();
  });

  it('renders the hero headline and both primary CTAs', () => {
    render(<LandingPage />);

    const heading = screen.getByRole('heading', { level: 1 });
    expect(heading.textContent).toMatch(/know what changed/i);

    // "Open InfraBuild-AI" appears in both the hero and the closing CTA.
    const openLinks = screen.getAllByRole('link', { name: /open infrabuild-ai/i });
    expect(openLinks.length).toBeGreaterThanOrEqual(2);

    expect(screen.getByRole('link', { name: /explore the intelligence loop/i })).toBeTruthy();
  });

  it('does not set data-theme on the document element', () => {
    const { container } = render(<LandingPage />);

    // The authenticated app owns document-level theming. The landing page
    // must scope its theme to its own subtree instead.
    expect(document.documentElement.hasAttribute('data-theme')).toBe(false);

    const root = container.querySelector('.landing-root');
    expect(root).toBeTruthy();
    expect(['dark', 'light']).toContain(root?.getAttribute('data-theme'));
  });

  it('renders every landing section in specification order', () => {
    const { container } = render(<LandingPage />);

    const expectedOrder = [
      'hero',
      'product',
      'intelligence',
      'what-changed',
      'peer-intelligence',
      'investigation',
      'analytics',
      'governance',
      'how-it-works',
      'technology',
      'access',
    ];

    const ids = Array.from(container.querySelectorAll('section[id]')).map(
      (section) => section.id,
    );

    expectedOrder.forEach((id) => {
      expect(ids).toContain(id);
    });

    const positions = expectedOrder.map((id) => ids.indexOf(id));
    expect(positions).toEqual([...positions].sort((a, b) => a - b));
  });

  it('exposes a skip link pointing at the main landmark', () => {
    render(<LandingPage />);

    const skip = screen.getByRole('link', { name: /skip to main content/i });
    expect(skip.getAttribute('href')).toBe('#main');
    expect(document.querySelector('main#main')).toBeTruthy();
  });

  it('labels illustrative visual content as conceptual', () => {
    const { container } = render(<LandingPage />);

    const notes = container.querySelectorAll('.lp-conceptual-note');
    expect(notes.length).toBeGreaterThanOrEqual(2);

    const tag = notes[0].querySelector('.lp-conceptual-note-tag');
    expect(tag?.textContent?.toLowerCase()).toMatch(/conceptual|illustrative/);
  });

  it('gives every analytics panel an accessible name and description', () => {
    const { container } = render(<LandingPage />);

    const figures = Array.from(container.querySelectorAll('.lp-chart'));
    expect(figures.length).toBeGreaterThanOrEqual(8);

    figures.forEach((figure) => {
      // Every panel carries a visible title and a textual caption, so the
      // information is available without relying on colour or hover.
      expect(figure.querySelector('.lp-chart__title')?.textContent?.trim()).toBeTruthy();
      expect(figure.querySelector('.lp-chart__caption')?.textContent?.trim()).toBeTruthy();
    });

    // SVG-based charts additionally expose an accessible graphic name.
    const svgCharts = Array.from(container.querySelectorAll('.lp-chart__svg'));
    expect(svgCharts.length).toBeGreaterThanOrEqual(4);

    svgCharts.forEach((chart) => {
      expect(chart.getAttribute('role')).toBe('img');
      expect((chart.getAttribute('aria-label') ?? '').length).toBeGreaterThan(10);
    });
  });

  it('exposes a working theme toggle', async () => {
    const { container } = render(<LandingPage />);

    const before = container.querySelector('.landing-root')?.getAttribute('data-theme');
    const toggle = screen.getByRole('button', { name: /switch to (light|dark) theme/i });

    toggle.click();
    await Promise.resolve();

    const after = container.querySelector('.landing-root')?.getAttribute('data-theme');
    expect(after).not.toBe(before);
    expect(['dark', 'light']).toContain(after);
  });

  it('renders the mobile nav trigger with correct ARIA wiring', () => {
    const { container } = render(<LandingPage />);

    const trigger = container.querySelector('.lp-header__menu-btn');
    expect(trigger).toBeTruthy();
    expect(trigger?.getAttribute('aria-expanded')).toBe('false');
    expect(trigger?.getAttribute('aria-controls')).toBe('lp-mobile-nav');

    const panel = container.querySelector('#lp-mobile-nav');
    expect(panel?.hasAttribute('hidden')).toBe(true);
  });

  it('marks pending legal pages instead of linking to placeholders', () => {
    const { container } = render(<LandingPage />);

    const pending = container.querySelectorAll('.lp-footer__legal-pending');
    expect(pending.length).toBeGreaterThanOrEqual(3);

    pending.forEach((item) => {
      expect(item.getAttribute('aria-disabled')).toBe('true');
    });
  });

  it('states that consequential action is human-gated', () => {
    const { container } = render(<LandingPage />);

    const text = (container.textContent ?? '').toLowerCase();
    expect(text).toMatch(/human-gated|human approval/);
    expect(text).toMatch(/consequential/);
  });

  it('does not fabricate customer, savings, or accuracy claims', () => {
    const { container } = render(<LandingPage />);

    const text = (container.textContent ?? '').toLowerCase();

    expect(text).not.toMatch(/guaranteed/);
    expect(text).not.toMatch(/revolutionary/);
    expect(text).not.toMatch(/100% accurate/);
    expect(text).not.toMatch(/\bsavings of\b/);
    expect(text).not.toMatch(/trusted by (ministries|departments)/);
  });
});