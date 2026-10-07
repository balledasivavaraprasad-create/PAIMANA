/**
 * Media query helpers.
 *
 * `matchMedia` and `IntersectionObserver` are present in every browser
 * targeted by this product, but they are absent in some non-browser
 * environments (jsdom-based test runs, server rendering). Reading them through
 * these guards keeps the landing experience from throwing at mount time and
 * degrades to the documented static behaviour instead.
 */

export interface MediaQueryListLike {
  matches: boolean;
  addEventListener?: (type: 'change', listener: (event: MediaQueryListEvent) => void) => void;
  removeEventListener?: (type: 'change', listener: (event: MediaQueryListEvent) => void) => void;
  addListener?: (listener: (event: MediaQueryListEvent) => void) => void;
  removeListener?: (listener: (event: MediaQueryListEvent) => void) => void;
}

export function safeMatchMedia(query: string): MediaQueryListLike | null {
  if (typeof window === 'undefined' || typeof window.matchMedia !== 'function') {
    return null;
  }
  try {
    return window.matchMedia(query);
  } catch {
    return null;
  }
}

export function prefersReducedMotion(): boolean {
  return safeMatchMedia('(prefers-reduced-motion: reduce)')?.matches ?? false;
}

export function prefersLightScheme(): boolean {
  return safeMatchMedia('(prefers-color-scheme: light)')?.matches ?? false;
}

export function prefersWideViewport(): boolean {
  return safeMatchMedia('(min-width: 901px)')?.matches ?? false;
}

export function observeViewport(
  callback: (isIntersecting: boolean, entry?: IntersectionObserverEntry) => void,
): () => void {
  if (typeof window === 'undefined' || typeof window.IntersectionObserver !== 'function') {
    // No observer available: report visible so content renders in its final
    // state rather than staying hidden behind a scroll trigger.
    callback(true);
    return () => {};
  }

  const observer = new IntersectionObserver((entries) => {
    const entry = entries[entries.length - 1];
    callback(entry.isIntersecting, entry);
  });

  return () => observer.disconnect();
}

export function createIntersectionObserver(
  callback: IntersectionObserverCallback,
  options?: IntersectionObserverInit,
): IntersectionObserver | null {
  if (typeof window === 'undefined' || typeof window.IntersectionObserver !== 'function') {
    return null;
  }
  return new IntersectionObserver(callback, options);
}

export function supportsSelector(): (selector: string) => Element | null {
  if (typeof document === 'undefined' || typeof document.querySelector !== 'function') {
    return () => null;
  }
  return (selector: string) => document.querySelector(selector);
}