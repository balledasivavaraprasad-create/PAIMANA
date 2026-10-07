import { useEffect, useState } from 'react';
import { useInView, useReducedMotion } from '../motion';

/**
 * Problem section — how risk actually accumulates.
 *
 * A staged progression from normal operation to critical exposure, driven by
 * real product quantities (progress, expenditure, DPHIS) so the argument is
 * concrete rather than abstract.
 */

const STAGES = [
  {
    key: 'normal',
    label: 'Normal',
    caption: 'Tracking within expected parameters',
    progress: 61,
    expenditure: 64,
    dphis: 54,
    tone: 'healthy',
  },
  {
    key: 'divergence',
    label: 'Small divergence',
    caption: 'Minor deviations begin to accumulate',
    progress: 60,
    expenditure: 66,
    dphis: 58,
    tone: 'healthy',
  },
  {
    key: 'acceleration',
    label: 'Risk acceleration',
    caption: 'Divergence compounds across dimensions',
    progress: 59,
    expenditure: 69,
    dphis: 66,
    tone: 'attention',
  },
  {
    key: 'exposure',
    label: 'Critical exposure',
    caption: 'Project is now visibly in trouble',
    progress: 59,
    expenditure: 71,
    dphis: 72,
    tone: 'critical',
  },
] as const;

export default function ProblemSection() {
  const { ref, isInView } = useInView<HTMLElement>();
  const reducedMotion = useReducedMotion();
  const [stage, setStage] = useState(0);

  useEffect(() => {
    if (!isInView) return;
    if (reducedMotion) {
      setStage(STAGES.length - 1);
      return;
    }
    const timers = STAGES.map((_, index) => window.setTimeout(() => setStage(index), 260 + index * 620));
    return () => timers.forEach((id) => window.clearTimeout(id));
  }, [isInView, reducedMotion]);

  const current = STAGES[stage];

  return (
    <section className="lp-section lp-problem" id="product" ref={ref}>
      <div className="landing-container">
        <div className="lp-section__header">
          <span className="lp-section__eyebrow">The problem</span>
          <h2 className="lp-section__title">Infrastructure risk rarely appears all at once.</h2>
          <p className="lp-section__description">
            By the time a project is reported as critical, the divergence has usually been visible in
            the underlying numbers for months — buried in separate progress, expenditure, and schedule
            reports that nobody reads together.
          </p>
        </div>

        <div className="lp-problem__board">
          {/* Progression rail */}
          <ol className="lp-problem__rail" aria-label="Risk progression stages">
            <span className="lp-problem__rail-track" aria-hidden="true">
              <span
                className="lp-problem__rail-progress"
                style={{ width: `${(stage / (STAGES.length - 1)) * 100}%` }}
              />
            </span>
            {STAGES.map((item, index) => (
              <li
                key={item.key}
                className={`lp-problem__rail-item${index === stage ? ' lp-problem__rail-item--active' : ''}${
                  index < stage ? ' lp-problem__rail-item--passed' : ''
                }`}
              >
                <span className="lp-problem__rail-dot" aria-hidden="true" />
                <span className="lp-problem__rail-label">{item.label}</span>
              </li>
            ))}
          </ol>

          {/* Live metric readout */}
          <div className="lp-problem__panel" data-tone={current.tone}>
            <div className="lp-problem__panel-header">
              <div>
                <span className="lp-problem__panel-stage">Stage {stage + 1} of {STAGES.length}</span>
                <h3 className="lp-problem__panel-title">{current.label}</h3>
                <p className="lp-problem__panel-caption">{current.caption}</p>
              </div>
              <span className="lp-problem__panel-status">
                <span className="lp-problem__panel-status-dot" aria-hidden="true" />
                {current.tone === 'healthy' ? 'Within tolerance' : current.tone === 'attention' ? 'Attention' : 'Critical'}
              </span>
            </div>

            <div className="lp-problem__metrics">
              <MetricBar
                label="Progress"
                value={current.progress}
                display={`${current.progress}%`}
                previous={stage > 0 ? STAGES[stage - 1].progress : null}
              />
              <MetricBar
                label="Expenditure"
                value={current.expenditure}
                display={`${current.expenditure}%`}
                previous={stage > 0 ? STAGES[stage - 1].expenditure : null}
                tone="attention"
              />
              <MetricBar
                label="DPHIS"
                value={current.dphis}
                display={String(current.dphis)}
                previous={stage > 0 ? STAGES[stage - 1].dphis : null}
                tone={current.tone}
              />
            </div>

            {/* Divergence gap: the quantity that is invisible in status reports */}
            <div className="lp-problem__gap">
              <span className="lp-problem__gap-label">Expenditure over progress</span>
              <span className="lp-problem__gap-value">
                +{current.expenditure - current.progress}
                <span className="lp-problem__gap-unit">pts</span>
              </span>
            </div>
          </div>
        </div>

        <p className="lp-problem__footnote">
          DPHIS — Delivery Performance and Health Index. Values are illustrative.
        </p>
      </div>
    </section>
  );
}

function MetricBar({
  label,
  value,
  display,
  previous,
  tone = 'neutral',
}: {
  label: string;
  value: number;
  display: string;
  previous: number | null;
  tone?: 'neutral' | 'attention' | 'healthy' | 'critical';
}) {
  const delta = previous === null ? null : value - previous;

  return (
    <div className="lp-metric">
      <div className="lp-metric__header">
        <span className="lp-metric__label">{label}</span>
        <span className="lp-metric__value">
          {display}
          {delta !== null && delta !== 0 && (
            <span className={`lp-metric__delta lp-metric__delta--${delta > 0 ? 'up' : 'down'}`}>
              {delta > 0 ? '+' : ''}
              {delta}
            </span>
          )}
        </span>
      </div>
      <div
        className="lp-metric__track"
        role="meter"
        aria-valuenow={value}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label={`${label}: ${display}`}
      >
        <span className={`lp-metric__fill lp-metric__fill--${tone}`} style={{ width: `${value}%` }} />
      </div>
    </div>
  );
}