/**
 * Copy and claims audit.
 *
 * Encodes the language rules from `32_COPY_GUIDELINES.md` and the trust
 * principles in `01_PRODUCT_VISION.md` as executable assertions, so the
 * constraints cannot drift as copy is edited.
 */

import { describe, it, expect } from 'vitest';
import { render, cleanup } from '@testing-library/react';
import { afterEach } from 'vitest';
import LandingPage from '../pages/LandingPage';

/** Phrases the product specification explicitly prohibits. */
const PROHIBITED = [
  'revolutionary',
  'revolutionise',
  'revolutionize',
  'magical',
  'game-changer',
  'cutting-edge',
  '100% accurate',
  'guaranteed',
  'seamless',
  'best-in-class',
  'world-class',
  'unparalleled',
];

/** Claims that would require substantiation the product cannot supply. */
const UNSUPPORTED_CLAIMS = [
  /real[- ]time (live )?monitoring/i,
  /live paimana/i,
  /guaranteed savings/i,
  /savings of (₹|\$|rs\.?)/i,
  /trusted by/i,
  /used by \d/i,
  /\d+ (ministries|departments|agencies)/i,
  /(?!not\b)(?<!does not )(?<!cannot )explains? the (cause|root cause)/i,
  /the contractor caused/i,
  /we (have )?(found|discovered) the (cause|root cause)/i,
];

/**
 * Disclaimer phrasings that legitimately mention causation in order to deny
 * it. Matching these separately keeps the claim check above strict without
 * flagging the copy that upholds the trust principles.
 */
const CAUSAL_DISCLAIMERS = [
  'the cause is not established',
  'root cause is not established',
  'does not claim to have identified the cause',
  'not evidence of causation',
  'not presented as proof of cause',
];

/** Domain vocabulary the specification asks us to prefer. */
const REQUIRED_VOCABULARY = [
  'observed',
  'detected',
  'predicted',
  'evidence',
  'uncertainty',
  'peer cohort',
];

describe('landing copy compliance', () => {
  afterEach(() => cleanup());

  function landingText(): string {
    const { container } = render(<LandingPage />);
    return (container.textContent ?? '').toLowerCase();
  }

  it('contains no prohibited marketing language', () => {
    const text = landingText();
    PROHIBITED.forEach((phrase) => {
      expect(text).not.toContain(phrase);
    });
  });

  it('makes no unsupported factual or causal claims', () => {
    const text = landingText();
    UNSUPPORTED_CLAIMS.forEach((pattern) => {
      expect(text).not.toMatch(pattern);
    });
  });

  it('uses the preferred evidence-aware vocabulary', () => {
    const text = landingText();
    REQUIRED_VOCABULARY.forEach((term) => {
      expect(text).toContain(term);
    });
  });

  it('distinguishes observed facts from predictions and hypotheses', () => {
    const text = landingText();
    // The classification legend must survive in the rendered output.
    expect(text).toContain('observed');
    expect(text).toContain('predicted');
    expect(text).toContain('peer context');
    expect(text).toContain('detected event');
  });

  it('states that consequential action stays human-gated', () => {
    const text = landingText();
    expect(text).toMatch(/consequential/);
    expect(text).toMatch(/human approval|human-gated/);
  });

  it('does not claim autonomous government decision-making', () => {
    const text = landingText();

    // Word order is not fixed, so match both arrangements.
    expect(text).not.toMatch(/autonomous(ly)?\s+(make|makes|making|take|takes)\b/i);
    expect(text).not.toMatch(/\b(make|makes|making|take|takes)\b[^.]{0,40}\bautonomous(ly)?\b/i);
    expect(text).not.toMatch(/replaces? (the )?(decision|judgement|judgment|officials?)/i);
    expect(text).not.toMatch(/acts? (on its own|without human approval)/i);
  });

  it('labels conceptual figures rather than presenting them as live', () => {
    const text = landingText();
    expect(text).toMatch(/conceptual|illustrative/);
  });

  it('acknowledges that peer comparison is not causation', () => {
    const text = landingText();
    CAUSAL_DISCLAIMERS.forEach((disclaimer) => {
      expect(text).toContain(disclaimer);
    });
  });
});