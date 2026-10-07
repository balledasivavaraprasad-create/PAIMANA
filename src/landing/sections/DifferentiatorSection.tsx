import { useInView } from '../motion';

/**
 * Product differentiator — four pillars presented as one analytical system.
 *
 * Deliberately not four independent cards: the pillars share a continuous
 * connector rail so the sequence reads as a single pipeline rather than a set
 * of disconnected features.
 */

const PILLARS = [
  {
    id: 'predict',
    title: 'Predict',
    role: 'Forward estimate',
    description:
      'Cost, schedule, and implementation risk are estimated before they materialise, with the driving factors exposed rather than hidden behind a score.',
    items: [
      { label: 'Cost risk', note: 'Expenditure against progress' },
      { label: 'Schedule risk', note: 'Milestone slippage' },
      { label: 'Implementation risk', note: 'Composite DPHIS' },
    ],
  },
  {
    id: 'contextualize',
    title: 'Contextualize',
    role: 'Cohort comparison',
    description:
      'Every project is placed against comparable projects. A number means more when you know whether the cohort moved with it.',
    items: [
      { label: 'Peer cohort', note: 'Explicit similarity match' },
      { label: 'Benchmarks', note: 'Cohort medians' },
      { label: 'Trajectory', note: 'Direction over cycles' },
    ],
  },
  {
    id: 'investigate',
    title: 'Investigate',
    role: 'Evidence gathering',
    description:
      'A stateful agent examines history, milestones, financial signals, and drivers — forming and revising hypotheses as evidence arrives.',
    items: [
      { label: 'Evidence', note: 'Sourced and timestamped' },
      { label: 'Hypotheses', note: 'Ranked, revisable' },
      { label: 'Stateful agent', note: 'Knows what it already checked' },
    ],
  },
  {
    id: 'act',
    title: 'Act',
    role: 'Gated intervention',
    description:
      'Validated recommendations reach a human approval boundary. Consequential execution happens only after authorisation.',
    items: [
      { label: 'Validated recommendation', note: 'Evidence attached' },
      { label: 'Human approval', note: 'Explicit authorisation' },
      { label: 'Automation', note: 'Durable, tracked delivery' },
    ],
  },
] as const;

const ICONS: Record<string, React.ReactNode> = {
  predict: (
    <>
      <path d="M2.5 12.5L6.5 8l3 2.5 4-5.5" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M11 5h2.5v2.5" strokeLinecap="round" strokeLinejoin="round" />
    </>
  ),
  contextualize: (
    <>
      <circle cx="5.5" cy="8" r="2.5" />
      <circle cx="11.5" cy="4.5" r="2" />
      <circle cx="11.5" cy="11.5" r="2" />
      <path d="M7.6 7L9.7 5.3M7.6 9l2.1 1.7" strokeLinecap="round" />
    </>
  ),
  investigate: (
    <>
      <circle cx="7" cy="7" r="4.5" />
      <path d="M10.4 10.4L13.5 13.5" strokeLinecap="round" />
      <path d="M5.2 7h3.6" strokeLinecap="round" />
    </>
  ),
  act: (
    <>
      <path d="M2.5 4.5h11v7h-11z" strokeLinejoin="round" />
      <path d="M6 8.5l1.8 1.8L11 6.8" strokeLinecap="round" strokeLinejoin="round" />
    </>
  ),
};

export default function DifferentiatorSection() {
  const { ref, isInView } = useInView<HTMLElement>();

  return (
    <section className="lp-section lp-pillars" id="intelligence" ref={ref}>
      <div className="landing-container">
        <div className="lp-section__header">
          <span className="lp-section__eyebrow">The difference</span>
          <h2 className="lp-section__title">From project status to project intelligence.</h2>
          <p className="lp-section__description">
            A status report tells you where a project is. These four steps turn that into something a
            decision-maker can actually act on — each one feeding the next.
          </p>
        </div>

        <ol className="lp-pillars__system" data-visible={isInView ? 'true' : 'false'}>
          <span className="lp-pillars__rail" aria-hidden="true" />
          {PILLARS.map((pillar, index) => (
            <li key={pillar.id} className="lp-pillar" style={{ ['--pillar-index' as string]: index }}>
              <div className="lp-pillar__head">
                <span className="lp-pillar__icon" aria-hidden="true">
                  <svg
                    width="16"
                    height="16"
                    viewBox="0 0 16 16"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="1.3"
                  >
                    {ICONS[pillar.id]}
                  </svg>
                </span>
                <div className="lp-pillar__heading">
                  <h3 className="lp-pillar__title">{pillar.title}</h3>
                  <span className="lp-pillar__role">{pillar.role}</span>
                </div>
                <span className="lp-pillar__index" aria-hidden="true">
                  {String(index + 1).padStart(2, '0')}
                </span>
              </div>

              <p className="lp-pillar__description">{pillar.description}</p>

              <ul className="lp-pillar__items">
                {pillar.items.map((item) => (
                  <li key={item.label} className="lp-pillar__item">
                    <span className="lp-pillar__item-label">{item.label}</span>
                    <span className="lp-pillar__item-note">{item.note}</span>
                  </li>
                ))}
              </ul>
            </li>
          ))}
        </ol>
      </div>
    </section>
  );
}