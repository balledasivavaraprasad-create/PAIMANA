import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, cleanup, fireEvent } from '@testing-library/react';
import LandingPage from '../pages/LandingPage';

describe('console cleanliness', () => {
  let err: unknown[][]; let warn: unknown[][];
  beforeEach(() => {
    err = []; warn = [];
    vi.spyOn(console, 'error').mockImplementation((...a) => { err.push(a); });
    vi.spyOn(console, 'warn').mockImplementation((...a) => { warn.push(a); });
  });
  afterEach(() => { cleanup(); vi.restoreAllMocks(); });

  it('mounts with no console errors or warnings', () => {
    render(<LandingPage />);
    expect(err).toEqual([]);
    expect(warn).toEqual([]);
  });

  it('toggles theme and opens mobile nav without console noise', () => {
    const { container } = render(<LandingPage />);
    const toggle = container.querySelector('.lp-theme-toggle') as HTMLElement;
    fireEvent.click(toggle);
    fireEvent.click(container.querySelector('.lp-header__menu-btn') as HTMLElement);
    fireEvent.click(container.querySelector('.lp-header__menu-btn') as HTMLElement);
    expect(err).toEqual([]);
    expect(warn).toEqual([]);
  });
});
