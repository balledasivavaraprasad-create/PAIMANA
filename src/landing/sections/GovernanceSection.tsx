import { useInView } from '../motion';

/**
 * Governance and trust.
 *
 * The message is accountability, not compliance theatre. Automated alerting is
 * explicitly acceptable; consequential intervention is explicitly human-gated.
 */

const PRINCIPLES = [
  {
    id: 'lineage',
    title: 'Evidence lineage',
    description:
      'Every detected event, prediction, and recommendation traces back to the source records and monitoring cycle that produced it.',
    icon: (
      <>
        <circle cx="3.5" cy="13.5" r="2" />
        <circle cx="13.5" cy="3" r="2" />
        <circle cx="13.5" cy="13.5" r="2" />
        <path d="M5.2 12.8l6.6-8.4M5.4 13.5h6.2" strokeLinecap="round" />
      </>
    ),
  },
  {
    id: 'uncertainty',
    title: 'Visible uncertainty',
    description:
      'Confidence levels, conflicting evidence, and gaps in the record are stated plainly. Missing evidence is never quietly dropped.',
    icon: (
      <>
        <circle cx="8.5" cy="8.5" r="6.5" />
        <path d="M8.5 5.5v3.6" strokeLinecap="round" />
        <circle cx="8.5" cy="11.6" r="0.6" fill="currentColor" stroke="none" />
      </>
    ),
  },
  {
    id: 'approval',
    title: 'Human approval boundary',
    description:
      'Alerting and notification may be automated. Consequential intervention requires explicit authorisation from an authorised role.',
    icon: (
      <>
        <path d="M8.5 1.8l5.5 2.4v4.2c0 3.7-2.4 6.2-5.5 7.3-3.1-1.1-5.5-3.6-5.5-7.3V4.2z" strokeLinejoin="round" />
        <path d="M6 8.5l1.9 1.9 3.4-3.6" strokeLinecap="round" strokeLinejoin="round" />
      </>
    ),
  },
  {
    id: 'audit',
    title: 'Complete audit trail',
    description:
      'What was detected, investigated, recommended, approved, rejected, and executed — recorded and reviewable after the fact.',
    icon: (
      <>
        <rect x="2.6" y="2.4" width="11.8" height="12.2" rx="2" />
        <path d="M5.5 6h5M5.5 8.8h5M5.5 11.6h3" strokeLinecap="round" />
      </>
    ),
  },
  {
    id: 'durable',
    title: 'Durable automation',
    description:
      'Approved workflows execute reliably and idempotently, with delivery state tracked through retry and dead-letter handling.',
    icon: (
      <>
        <path d="M2.4 8.5a6.1 6.1 0 0111.2-2.4" strokeLinecap="round" />
        <path d="M14.6 8.5a6.1 6.1 0 01-11.2 2.4" strokeLinecap="round" />
        <path d="M13.2 2.6v3.5H9.7M3.8 14.4v-3.5h3.5" strokeLinecap="round" strokeLinejoin="round" />
      </>
    ),
  },
];

export default function GovernanceSection() {
  const { ref, isInView } = useInView<HTMLElement>();

  return (
    <section className="lp-section lp-governance" id="governance" ref={ref}>
      <div className="landing-container">
        <div className="lp-section__header">
          <span className="lp-section__eyebrow">Governance</span>
          <h2 className="lp-section__title">Intelligence without unaccountable automation.</h2>
          <p className="lp-section__description">
            Automation is welcome where it saves attention. It is not acceptable where it removes
            accountability. The system draws that line explicitly and keeps it visible.
          </p>
        </div>

        <div className="lp-governance__grid" data-visible={isInView ? 'true' : 'false'}>
          {PRINCIPLES.map((principle) => (
            <article key={principle.id} className="lp-governance__item">
              <span className="lp-governance__icon" aria-hidden="true">
                <svg width="17" height="17" viewBox="0 0 17 17" fill="none" stroke="currentColor" strokeWidth="1.3">
                  {principle.icon}
                </svg>
              </span>
              <h3 className="lp-governance__title">{principle.title}</h3>
              <p className="lp-governance__description">{principle.description}</p>
            </article>
          ))}
        </div>

        <div className="lp-governance__boundary">
          <div className="lp-governance__boundary-col">
            <span className="lp-governance__boundary-tag lp-governance__boundary-tag--ok">Automated</span>
            <ul className="lp-governance__boundary-list">
              <li>Continuous snapshot ingestion</li>
              <li>Threshold and event detection</li>
              <li>Risk scoring and projection</li>
              <li>Alert notification</li>
              <li>Status and evidence dashboards</li>
            </ul>
          </div>
          <div className="lp-governance__boundary-divider" aria-hidden="true" />
          <div className="lp-governance__boundary-col">
            <span className="lp-governance__boundary-tag lp-governance__boundary-tag--human">
              Human-gated
            </span>
            <ul className="lp-governance__boundary-list">
              <li>Approving a recommendation</li>
              <li>Authorising consequential action</li>
              <li>Changing monitoring thresholds</li>
              <li>Granting or revoking access</li>
              <li>Accepting a residual risk decision</li>
            </ul>
          </div>
        </div>

        <p className="lp-governance__footnote">
          InfraBuild-AI supports decision-makers. It does not make government decisions, and it does
          not act autonomously on consequential matters.
        </p>
      </div>
    </section>
  );
}