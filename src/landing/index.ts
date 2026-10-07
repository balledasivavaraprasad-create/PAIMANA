/**
 * Exported entry point for the public editorial landing experience.
 *
 * Intended route: `/`
 *
 * The editorial landing page is rebuilt to mirror the primary visual reference:
 * - Floating black pill navigation
 * - Large soft organic color fields (peach, lavender, mint)
 * - Spacious modern typography with tight line-heights
 * - Live interactive product mockups demonstrating DPHIS drift, peer cohorts, agentic investigations
 * - Pinned storytelling progression
 * - Subtle dark human-approval section
 * - Role-based technology matrix
 * - Clean minimal FAQ accordion
 * - Soft peach final CTA
 */

export { EditorialLandingPage as default } from './editorial/EditorialLandingPage';
export { EditorialLandingPage } from './editorial/EditorialLandingPage';
export { default as LegacyLandingPage } from './pages/LandingPage';

export { ThemeProvider, useLandingTheme, type LandingTheme } from './components/ThemeContext';
export { useInView, useReducedMotion, useScrollProgress } from './motion';