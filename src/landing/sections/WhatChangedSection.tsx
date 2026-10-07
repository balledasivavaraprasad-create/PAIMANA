import { useEffect, useState } from 'react';
import { useInView, useReducedMotion } from '../motion';

/**
 * "What changed?" — the product's core value proposition.
 *
 * Sequence: previous snapshot → new snapshot → detected events → peer context.
 *
 * The contrast between Observed / Predicted / Peer Context / Detected is
 * carried by label text, position, and an explicit legend — never by colour
 * alone (22_ACCESSIBILITY.md).
 */

type Stage = 'previous' | 'current' | 'detected' | 'peer';

const STAGE_SEQUENCE: Stage[] = ['previous', 'current', 'detected', 'peer'];

const SNAPSHOTS = {
  previous: {
    label: 'Previous snapshot',
    timestamp: 'Cycle 114 · 3 days prior',
    progress: 61,
    expenditure: 64,
    dphis: 54,
  },
  current: {
    label: 'New snapshot',
    timestamp: 'Cycle 115 · current',
    progress: 59,
    expenditure: 71,
    dphis: 72,
  },
} as const;

const DETECTED_EVENTS = [
  { title: 'Cost / progress mismatch', detail: 'Expenditure rose 7 pts while progress fell 2 pts.' },
  { title: 'Risk accelerating', detail: 'DPHIS moved +18 in one cycle against a 6-pt cohort norm.' },
];

const PEER_CONTEXT = [
  { label: 'Peer median DPHIS', value: '46', tone: 'neutral' as const },
  { label: 'Target DPHIS', value: '72', tone: 'target' as const },
  { label: 'Peer deviation', value: '+26', tone: 'risk' as const },
];

const LEGEND = [
  { key: 'observed', label: 'Observed', description: 'Measured from project records' },
  { key: 'predicted', label: 'Predicted', description: 'Model estimate, not a fact' },
  { key: 'peer', label: 'Peer context', description: 'Cohort comparison, not causation' },
  { key: 'detected', label: 'Detected event', description: 'Threshold rule matched' },
];

export default function WhatChangedSection() {
  const { ref, isInView } = useInView<HTMLElement>();
  const reducedMotion = useReducedMotion();
  const [step, setStep] = useState(0);

  // Advance the sequence once when the section enters view. Under reduced
  // motion the sequence resolves immediately to its final state.
  useEffect(() => {
    if (!isInView) return;
    if (reducedMotion) {
      setStep(STAGE_SEQUENCE.length);
      return;
    }
    const timers = STAGE_SEQUENCE.map((_, index) =>
      window.setTimeout(() => setStep(index + 1), 420 + index * 620),
    );
    return () => timers.forEach((id) => window.clearTimeout(id));
  }, [isInView, reducedMotion]);

  const settled = step >= STAGE_SEQUENCE.length;

  return (
    <section className="lp-section lp-changed" id="what-changed" ref={ref}>
      <div className="landing-container">
        <div className="lp-section__header">
          <span className="lp-section__eyebrow">What changed?</span>
          <h2 className="lp-section__title">
            Most monitoring shows you the present. This shows you the delta.
          </h2>
          <p className="lp-section__description">
            Each monitoring cycle compares the current snapshot against the previous one. When the
            change is large enough to matter, an event is raised — with peer context attached, so a
            project-specific problem is not confused with a cohort-wide one.
          </p>
        </div>

        <p className="lp-conceptual-note" role="note">
          <span className="lp-conceptual-note-tag">Illustrative example</span>
          The project, peer cohort, and figures below are conceptual. Peer evidence is contextual and
          is not presented as proof of cause.
        </p>

        <div className="lp-changed__board">
          <ol className="lp-changed__legend" aria-label="Data classification legend">
            {LEGEND.map((item) => (
              <li key={item.key} className={`lp-legend__item lp-legend__item--${item.key}`}>
                <span className="lp-legend__marker" aria-hidden="true" />
                <span className="lp-legend__text">
                  <span className="lp-legend__label">{item.label}</span>
                  <span className="lp-legend__desc">{item.description}</span>
                </span>
              </li>
            ))}
          </ol>

          <div className="lp-changed__panels">
            <SnapshotPanel
              variant="previous"
              data={SNAPSHOTS.previous}
              state={step >= 1 ? 'dimmed' : 'active'}
            />

            <span className="lp-changed__connector" aria-hidden="true">
              <span className="lp-changed__connector-line" />
              <span className="lp-changed__connector-arrow">→</span>
            </span>

            <SnapshotPanel variant="current" data={SNAPSHOTS.current} state={step >= 2 ? 'active' : 'pending'} />
          </div>

          <div className="lp-changed__detected" data-state={step >= 3 ? 'active' : 'pending'}>
            <div className="lp-changed__detected-header">
              <span className="lp-legend__marker lp-legend__marker--detected" aria-hidden="true" />
              <h3 className="lp-changed__detected-title">Detected</h3>
              <span className="lp-changed__detected-count">
                {DETECTED_EVENTS.length} events
              </span>
            </div>
            <ul className="lp-changed__event-list">
              {DETECTED_EVENTS.map((event, index) => (
                <li key={event.title} className="lp-changed__event">
                  <span className="lp-changed__event-index">{String(index + 1).padStart(2, '0')}</span>
                  <span className="lp-changed__event-body">
                    <span className="lp-changed__event-title">{event.title}</span>
                    <span className="lp-changed__event-detail">{event.detail}</span>
                  </span>
                </li>
              ))}
            </ul>
          </div>

          <div className="lp-changed__peer" data-state={step >= 4 ? 'active' : 'pending'}>
            <span className="lp-legend__marker lp-legend__marker--peer" aria-hidden="true" />
            <h3 className="lp-changed__peer-title">Peer context</h3>
            <dl className="lp-changed__peer-grid">
              {PEER_CONTEXT.map((item) => (
                <div key={item.label} className={`lp-changed__peer-item lp-changed__peer-item--${item.tone}`}>
                  <dt className="lp-changed__peer-label">{item.label}</dt>
                  <dd className="lp-changed__peer-value">{item.value}</dd>
                </div>
              ))}
            </dl>
            <p className="lp-changed__peer-note">
              Comparable projects show a peer median of 46. The current evidence suggests this
              project is under greater delivery pressure than its cohort — the cause is not
              established.
            </p>
          </div>

          {/* Textual equivalent of the whole comparison. */}
          <p className="lp-sr-only">
            Previous snapshot: progress 61 percent, expenditure 64 percent, DPHIS 54. New snapshot:
            progress 59 percent, expenditure 71 percent, DPHIS 72. Two events detected: cost over
            progress mismatch, and risk accelerating. Peer median DPHIS is 46, target DPHIS is 72,
            a peer deviation of plus 26.
          </p>

          {settled && (
            <div className="lp-changed__timeline" aria-hidden="true">
              {STAGE_SEQUENCE.map((item, index) => (
                <span key={item} className="lp-changed__tick" style={{ animationDelay: `${index * 120}ms` }} />
              ))}
            </div>
          )}
        </div>
      </div>
    </section>
  );
}

function SnapshotPanel({
  variant,
  data,
  state,
}: {
  variant: 'previous' | 'current';
  data: typeof SNAPSHOTS.previous | typeof SNAPSHOTS.current;
  state: 'active' | 'dimmed' | 'pending';
}) {
  const metrics = [
    { key: 'progress', label: 'Progress', value: `${data.progress}%`, delta: variant === 'current' ? -2 : null },
    { key: 'expenditure', label: 'Expenditure', value: `${data.expenditure}%`, delta: variant === 'current' ? 7 : null },
    { key: 'dphis', label: 'DPHIS', value: String(data.dphis), delta: variant === 'current' ? 18 : null },
  ];

  return (
    <div className={`lp-snapshot lp-snapshot--${variant}`} data-state={state}>
      <header className="lp-snapshot__header">
        <span className="lp-snapshot__label">{data.label}</span>
        <span className="lp-snapshot__timestamp">{data.timestamp}</span>
      </header>
      <dl className="lp-snapshot__metrics">
        {metrics.map((metric) => (
          <div key={metric.key} className="lp-snapshot__metric">
            <dt className="lp-snapshot__metric-label">{metric.label}</dt>
            <dd className="lp-snapshot__metric-value">
              {metric.value}
              {metric.delta !== null && (
                <span
                  className={`lp-snapshot__delta lp-snapshot__delta--${metric.delta > 0 ? 'up' : 'down'}`}
                >
                  {metric.delta > 0 ? '+' : ''}
                  {metric.delta}
                </span>
              )}
            </dd>
          </div>
        ))}
      </dl>
    </div>
  );
}