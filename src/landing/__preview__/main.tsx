/**
 * Standalone preview harness for the public landing page.
 *
 * Development scaffolding only — not part of the delivered page. It mounts
 * `LandingPage` without the authenticated app shell so the public experience
 * can be reviewed on its own. The real integration path is documented in
 * `../LANDING_INTEGRATION.md`.
 */
import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import LandingPage from '../pages/LandingPage';

const container = document.getElementById('root');
if (!container) throw new Error('Preview root element missing');

createRoot(container).render(
  <StrictMode>
    <LandingPage />
  </StrictMode>,
);