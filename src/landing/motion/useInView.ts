import { useEffect, useRef, useState } from 'react';
import { createIntersectionObserver } from './env';

interface UseInViewOptions {
  threshold?: number;
  rootMargin?: string;
  /** Keep observing after the first intersection. Defaults to true-shot. */
  once?: boolean;
}

/**
 * Reveal-on-scroll trigger.
 *
 * Uses IntersectionObserver rather than scroll listeners so no layout
 * calculations run per frame. When the observer is unavailable the element is
 * reported as visible immediately, which keeps content from being trapped in
 * a pre-animation state.
 */
export function useInView<T extends HTMLElement = HTMLDivElement>({
  threshold = 0.15,
  rootMargin = '0px 0px -40px 0px',
  once = true,
}: UseInViewOptions = {}) {
  const ref = useRef<T>(null);
  const [isInView, setIsInView] = useState(false);

  useEffect(() => {
    const element = ref.current;
    if (!element) return;

    const observer = createIntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsInView(true);
          if (once) observer?.disconnect();
        } else if (!once) {
          setIsInView(false);
        }
      },
      { threshold, rootMargin },
    );

    if (!observer) {
      setIsInView(true);
      return;
    }

    observer.observe(element);
    return () => observer.disconnect();
  }, [threshold, rootMargin, once]);

  return { ref, isInView };
}