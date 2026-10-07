/**
 * Anchor integrity.
 *
 * Every in-page link must resolve to a real element id. A dangling fragment
 * silently does nothing, which reads as a broken page rather than a known gap.
 */

import { describe, it, expect, afterEach } from 'vitest';
import { render, cleanup } from '@testing-library/react';
import LandingPage from '../pages/LandingPage';

describe('in-page links', () => {
  afterEach(() => cleanup());

  it('resolves every hash link to an existing element', () => {
    const { container } = render(<LandingPage />);

    const links = Array.from(container.querySelectorAll('a[href^="#"]'));
    expect(links.length).toBeGreaterThan(10);

    // These fragments are intentional integration placeholders for real auth
    // routes and are documented as such. They are not expected to resolve to
    // an element on the public page.
    const INTEGRATION_PLACEHOLDERS = new Set(['#signin', '#access']);

    const unresolved: string[] = [];

    links.forEach((link) => {
      const href = link.getAttribute('href') ?? '';
      if (href === '#' || INTEGRATION_PLACEHOLDERS.has(href)) return;

      const id = href.slice(1);
      if (!id) {
        unresolved.push(href);
        return;
      }

      if (!document.getElementById(id) && !container.querySelector(`#${CSS.escape(id)}`)) {
        unresolved.push(href);
      }
    });

    expect(unresolved).toEqual([]);
  });

  it('routes auth-intent CTAs through the documented placeholder fragments', () => {
    const { container } = render(<LandingPage />);

    // These two are intentional placeholders for the integrator to map onto
    // real authentication routes. They are asserted here so a future change is
    // a deliberate decision rather than an accident.
    const signin = Array.from(container.querySelectorAll('a[href="#signin"]'));
    const access = Array.from(container.querySelectorAll('a[href="#access"]'));

    expect(signin.length).toBeGreaterThan(0);
    expect(access.length).toBeGreaterThan(0);
  });

  it('gives every link a discernible name', () => {
    const { container } = render(<LandingPage />);

    const links = Array.from(container.querySelectorAll('a'));
    const unnamed = links.filter((link) => {
      const text = (link.textContent ?? '').trim();
      const label = link.getAttribute('aria-label');
      const title = link.getAttribute('title');
      const image = link.querySelector('img[alt]:not([alt=""])');
      return text.length === 0 && !label && !title && !image;
    });

    expect(unnamed).toEqual([]);
  });
});