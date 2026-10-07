import { useEffect, useState } from 'react';
import { safeMatchMedia } from './env';

/**
 * Tracks `prefers-reduced-motion`.
 *
 * Returns `false` when the preference cannot be determined, so an environment
 * without `matchMedia` behaves like a motion-capable browser rather than
 * crashing. The CSS media query in `styles/landing.css` independently enforces
 * the reduced-motion presentation.
 */
export function useReducedMotion(): boolean {
  const [reduced, setReduced] = useState(false);

  useEffect(() => {
    const query = safeMatchMedia('(prefers-reduced-motion: reduce)');
    if (!query) return;

    setReduced(query.matches);

    const onChange = (event: MediaQueryListEvent) => setReduced(event.matches);

    // Safari < 14 only supports the deprecated addListener/removeListener pair.
    if (typeof query.addEventListener === 'function') {
      query.addEventListener('change', onChange);
      return () => query.removeEventListener?.('change', onChange);
    }
    if (typeof query.addListener === 'function') {
      query.addListener(onChange);
      return () => query.removeListener?.(onChange);
    }
    return;
  }, []);

  return reduced;
}