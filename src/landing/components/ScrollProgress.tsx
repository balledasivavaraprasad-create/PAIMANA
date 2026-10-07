import { useScrollProgress } from '../motion';

/**
 * Thin scroll-progress rail pinned to the top of the page.
 *
 * Communicates reading position without occupying layout space. Decorative:
 * progress is already conveyed structurally, so it is hidden from assistive
 * technology to avoid redundant announcements.
 */
export default function ScrollProgress() {
  const progress = useScrollProgress();

  return (
    <div className="lp-scroll-progress" aria-hidden="true">
      <div
        className="lp-scroll-progress__bar"
        style={{ transform: `scaleX(${progress})` }}
      />
    </div>
  );
}