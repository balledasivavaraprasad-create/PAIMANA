import { useInView } from '../motion';

/**
 * Closing CTA.
 *
 * Leads with the platform. Access requests and architecture exploration are
 * secondary — the primary action is opening the product.
 */

const ASSURANCES = [
  'No claim of verified causation without evidence',
  'Consequential action requires human approval',
  'Conceptual figures are labelled as such',
];

export default function FinalCTA() {
  const { ref, isInView } = useInView<HTMLElement>();

  return (
    <section className="lp-section lp-cta" id="access" ref={ref}>
      <div className="lp-cta__inner">
        <div className="lp-cta__panel" data-visible={isInView ? 'true' : 'false'}>
          <div className="lp-cta__glow" aria-hidden="true" />

          <span className="lp-section__eyebrow lp-cta__eyebrow">Continuous infrastructure intelligence</span>

          <h2 className="lp-cta__title">
            See the project before the problem becomes obvious.
          </h2>

          <p className="lp-cta__body">
            InfraBuild-AI turns monitoring into intervention intelligence — surfacing what changed,
            how unusual it is, and what an authorised decision-maker should review next.
          </p>

          <div className="lp-cta__actions">
            <a href="#signin" className="lp-button lp-button--primary">
              Open InfraBuild-AI
              <svg width="15" height="15" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" aria-hidden="true">
                <path d="M3 8h10M9 4l4 4-4 4" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </a>
            <a href="#technology" className="lp-button lp-button--secondary">
              Explore the architecture
            </a>
          </div>

          <ul className="lp-cta__assurances">
            {ASSURANCES.map((assurance) => (
              <li key={assurance} className="lp-cta__assurance">
                <span className="lp-cta__assurance-check" aria-hidden="true">
                  <svg width="10" height="10" viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth="1.7">
                    <path d="M2.5 6.2l2.4 2.3L9.5 3.9" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                </span>
                {assurance}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </section>
  );
}