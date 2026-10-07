import { NAV_LINKS } from '../data/content';

/**
 * Site footer.
 *
 * Grouped by intent rather than by internal org chart. Links that do not yet
 * have a destination are rendered as disabled text with an explicit note,
 * rather than as links to "#" which would be misleading.
 */

const COLUMNS = [
  {
    title: 'Product',
    links: NAV_LINKS.filter((link) => ['Product', 'Intelligence', 'Analytics'].includes(link.label)),
  },
  {
    title: 'Architecture',
    links: [
      { label: 'How it works', href: '#how-it-works' },
      { label: 'Governance', href: '#governance' },
      { label: 'Peer intelligence', href: '#peer-intelligence' },
    ],
  },
  {
    title: 'Technology',
    links: [{ label: 'Stack and roles', href: '#technology' }],
  },
] as const;

export default function Footer() {
  const year = new Date().getFullYear();

  return (
    <footer className="lp-footer">
      <div className="lp-footer__inner">
        <div className="lp-footer__top">
          <div className="lp-footer__brand">
            <div className="lp-footer__logo">
              <span className="lp-footer__logo-icon" aria-hidden="true">
                <svg width="13" height="13" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5">
                  <path d="M2 12.5V5.5L8 2l6 3.5v7" strokeLinejoin="round" />
                  <path d="M5.5 12.5v-4h5v4" strokeLinejoin="round" />
                </svg>
              </span>
              <span>InfraBuild-AI</span>
            </div>
            <p className="lp-footer__tagline">
              Continuous infrastructure project intelligence. Observe, detect, predict, explain,
              compare, investigate, recommend, and measure — with evidence attached to every step.
            </p>
          </div>

          <nav className="lp-footer__nav" aria-label="Footer">
            {COLUMNS.map((column) => (
              <div key={column.title} className="lp-footer__column">
                <h2 className="lp-footer__column-title">{column.title}</h2>
                <ul className="lp-footer__list">
                  {column.links.map((link) => (
                    <li key={link.label}>
                      <a href={link.href} className="lp-footer__link">
                        {link.label}
                      </a>
                    </li>
                  ))}
                </ul>
              </div>
            ))}

            <div className="lp-footer__column">
              <h2 className="lp-footer__column-title">Access</h2>
              <ul className="lp-footer__list">
                <li>
                  <a href="#signin" className="lp-footer__link">
                    Sign in
                  </a>
                </li>
                <li>
                  <a href="#access" className="lp-footer__link">
                    Request access
                  </a>
                </li>
              </ul>
            </div>
          </nav>
        </div>

        <div className="lp-footer__bottom">
          <p className="lp-footer__copyright">
            &copy; {year} InfraBuild-AI. Figures and visualisations on this page are illustrative.
          </p>

          <ul className="lp-footer__legal">
            <li>
              <span className="lp-footer__legal-pending" aria-disabled="true">
                Privacy
              </span>
            </li>
            <li>
              <span className="lp-footer__legal-pending" aria-disabled="true">
                Terms
              </span>
            </li>
            <li>
              <span className="lp-footer__legal-pending" aria-disabled="true">
                Documentation
              </span>
            </li>
          </ul>
        </div>

        <p className="lp-footer__note">
          Privacy, Terms, and Documentation pages are not yet published. They are marked as pending
          rather than linked to a placeholder destination.
        </p>
      </div>
    </footer>
  );
}