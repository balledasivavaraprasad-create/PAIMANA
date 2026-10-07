/**
 * Document title and meta description for the public landing experience.
 *
 * Set once on mount and reverted on unmount so the authenticated application
 * is not left carrying marketing metadata. Uses the dedicated hook instead of
 * direct document writes scattered through components.
 */

const TITLE = 'InfraBuild-AI — Continuous Infrastructure Project Intelligence';
const DESCRIPTION =
  'InfraBuild-AI continuously observes infrastructure project state, detects meaningful change, predicts emerging risk, compares projects with relevant peers, investigates possible causes, and supports evidence-backed intervention.';

let appliedCount = 0;

/**
 * Sets the landing document title and meta description while the public
 * experience is mounted, then restores whatever the host application had.
 */
export function useLandingMeta(): () => void {
  if (typeof document === 'undefined') return () => {};

  appliedCount += 1;

  if (appliedCount > 1) {
    return () => {
      appliedCount -= 1;
    };
  }

  const previousTitle = document.title;

  const meta = document.createElement('meta');
  meta.name = 'description';
  meta.content = DESCRIPTION;
  document.head.appendChild(meta);

  document.title = TITLE;

  return () => {
    if (--appliedCount === 0) {
      document.title = previousTitle;
      meta.remove();
    }
  };
}