import { useEffect, useState } from 'react';
import { useInView, useReducedMotion } from '../motion';

/**
 * Agentic investigation section.
 *
 * Shows the investigator adapting to evidence: which source it consults, what
 * it concluded, and where it stopped short. Deliberately restrained — no code,
 * no chat transcript, and no implication that the system has established cause.
 */

const LOOP = [
  { key: 'event', label: 'Event', detail: 'Threshold matched on DPHIS delta' },
  { key: 'evidence', label: 'Evidence needed', detail: 'Which sources could explain this' },
  { key: 'tool', label: 'Tool selected', detail: 'Query history, milestones, finance' },
  { key: 'observation', label: 'Observation', detail: 'Three milestone slips in one quarter' },
  { key: 'hypothesis', label: 'Hypothesis update', detail: 'Weighed against peer cohort' },
  { key: 'decision', label: 'Continue or conclude', detail: 'Evidence sufficient or gap remains' },
] as const;

const SOURCES = [
  { label: 'Project history', kind: 'observed' as const },
  { label: 'Milestones', kind: 'observed' as const },
  { label: 'Financial signals', kind: 'observed' as const },
  { label: 'SHAP drivers', kind: 'predicted' as const },
  { label: 'Peer cohort', kind: 'context' as const },
  { label: 'Agent memory', kind: 'context' as const },
];

export default function InvestigationSection() {
  const { ref, isInView } = useInView<HTMLElement>();
  const reducedMotion = useReducedMotion();
  const [stage, setStage] = useState(0);

  useEffect(() => {
    if (!isInView) return;
    if (reducedMotion) {
      setStage(LOOP.length);
      return;
    }
    const timers = LOOP.map((_, index) => window.setTimeout(() => setStage(index + 1), 300 + index * 540));
    return () => timers.forEach((id) => window.clearTimeout(id));
  }, [isInView, reducedMotion]);

  return (
    <section className="lp-section lp-loop" id="investigation" ref={ref}>
      <div className="landing-container">
        <div className="lp-section__header">
          <span className="lp-section__eyebrow">Investigation</span>
          <h2 className="lp-section__title">
            When the signal appears, the system investigates.
          </h2>
          <p className="lp-section__description">
            Detection alone does not help anyone act. The investigator opens a case, identifies what
            evidence would be relevant, works through the sources, and reports what it found — along
            with what it could not establish.
          </p>
        </div>

        <div className="lp-loop__layout">
          <ol className="lp-loop__steps" aria-label="Investigation sequence">
            <span className="lp-loop__rail" aria-hidden="true">
              <span
                className="lp-loop__rail-progress"
                style={{ height: `${(stage / LOOP.length) * 100}%` }}
              />
            </span>
            {LOOP.map((item, index) => (
              <li
                key={item.key}
                className={`lp-loop__step${index < stage ? ' lp-loop__step--done' : ''}${
                  index === stage ? ' lp-loop__step--active' : ''
                }`}
              >
                <span className="lp-loop__node" aria-hidden="true">
                  <span className="lp-loop__node-dot" />
                </span>
                <span className="lp-loop__body">
                  <span className="lp-loop__label">{item.label}</span>
                  <span className="lp-loop__detail">{item.detail}</span>
                </span>
              </li>
            ))}
          </ol>

          <div className="lp-loop__case">
            <header className="lp-loop__case-header">
              <span className="lp-loop__case-id">INV-2291</span>
              <span className="lp-loop__case-status">
                <span className="lp-loop__case-dot" aria-hidden="true" />
                {stage >= LOOP.length ? 'Ready for review' : 'Investigating'}
              </span>
            </header>

            <div className="lp-loop__case-body">
              <div className="lp-loop__evidence">
                <h3 className="lp-loop__case-title">Evidence consulted</h3>
                <ul className="lp-loop__sources">
                  {SOURCES.map((source, index) => (
                    <li
                      key={source.label}
                      className={`lp-loop__source lp-loop__source--${source.kind}`}
                      data-state={stage > index + 1 ? 'seen' : stage === index + 1 ? 'current' : 'pending'}
                    >
                      <span className="lp-loop__source-kind">
                        {source.kind === 'observed'
                          ? 'Observed'
                          : source.kind === 'predicted'
                            ? 'Predicted'
                            : 'Context'}
                      </span>
                      <span className="lp-loop__source-label">{source.label}</span>
                    </li>
                  ))}
                </ul>
              </div>

              <div className="lp-loop__finding">
                <h3 className="lp-loop__case-title">Finding</h3>
                <p className="lp-loop__finding-text">
                  Evidence is consistent with schedule compression following three milestone slips.
                  The peer cohort shows no comparable movement over the same window, which suggests the
                  cause is project-specific rather than sector-wide.
                </p>
                <div className="lp-loop__confidence">
                  <div className="lp-loop__confidence-row">
                    <span className="lp-loop__confidence-label">Confidence</span>
                    <span className="lp-loop__confidence-value">Moderate</span>
                  </div>
                  <div className="lp-loop__confidence-track" aria-hidden="true">
                    <span className="lp-loop__confidence-fill" style={{ width: '58%' }} />
                  </div>
                  <p className="lp-loop__confidence-note">
                    Root cause is not established. Milestone records for two dependencies are
                    unavailable.
                  </p>
                </div>
              </div>
            </div>

            <footer className="lp-loop__case-footer">
              <span className="lp-loop__case-footer-note">
                Consequential action remains human-gated.
              </span>
            </footer>
          </div>
        </div>
      </div>
    </section>
  );
}