import { useEffect, useRef, useState } from 'react';
import { useReducedMotion } from '../motion';
import { createIntersectionObserver, prefersReducedMotion } from '../motion/env';
import { WALKTHROUGH_STEPS } from '../data/content';

/**
 * Scroll-linked product walkthrough.
 *
 * A tall sticky rail drives a central visual. Which step is "active" is
 * derived from scroll position, so the narrative advances as the user reads
 * rather than requiring clicks. Clicking a step scrolls to it, keeping the
 * two input methods consistent in both directions.
 */
export default function WalkthroughSection() {
  const [activeIndex, setActiveIndex] = useState(0);
  const sectionRef = useRef<HTMLElement>(null);
  const stepRefs = useRef<(HTMLLIElement | null)[]>([]);
  const reducedMotion = useReducedMotion();

  useEffect(() => {
    const section = sectionRef.current;
    if (!section) return;

    // A single observer covering the whole section: the step nearest the
    // reading line (upper third of the viewport) becomes active.
    const observer = createIntersectionObserver(
      (entries) => {
        let bestIndex = -1;
        let bestRatio = 0;

        entries.forEach((entry) => {
          const index = Number((entry.target as HTMLElement).dataset.stepIndex);
          if (Number.isNaN(index) || !entry.isIntersecting) return;
          if (entry.intersectionRatio > bestRatio) {
            bestRatio = entry.intersectionRatio;
            bestIndex = index;
          }
        });

        if (bestIndex >= 0 && bestRatio > 0) {
          setActiveIndex(bestIndex);
        }
      },
      {
        // Bias the trigger line towards the upper-middle of the viewport.
        rootMargin: '-30% 0px -45% 0px',
        threshold: [0, 0.25, 0.5, 0.75, 1],
      },
    );

    if (!observer) return;

    stepRefs.current.forEach((el) => el && observer.observe(el));
    return () => observer.disconnect();
  }, []);

  const progress = (activeIndex / (WALKTHROUGH_STEPS.length - 1)) * 100;

  const scrollToStep = (index: number) => {
    const target = stepRefs.current[index];
    if (!target) return;
    const reduce = prefersReducedMotion();
    target.scrollIntoView({ behavior: reduce ? 'auto' : 'smooth', block: 'center' });
    setActiveIndex(index);
  };

  return (
    <section className="lp-section lp-walkthrough" id="how-it-works" ref={sectionRef}>
      <div className="landing-container">
        <div className="lp-section__header">
          <span className="lp-section__eyebrow">How it works</span>
          <h2 className="lp-section__title">One loop, continuously repeated.</h2>
          <p className="lp-section__description">
            Monitoring does not end at a report. Each cycle produces evidence that improves the next
            cycle, so the system compounds its understanding of the portfolio over time.
          </p>
        </div>

        <div className="lp-walkthrough__layout">
          {/* Narrative rail — the scroll driver. */}
          <ol className="lp-walkthrough__rail">
            <span className="lp-walkthrough__rail-track" aria-hidden="true">
              <span
                className="lp-walkthrough__rail-progress"
                style={{ height: `${progress}%` }}
              />
            </span>

            {WALKTHROUGH_STEPS.map((step, index) => (
              <li
                key={step.id}
                ref={(el) => {
                  stepRefs.current[index] = el;
                }}
                data-step-index={index}
                className={`lp-walkthrough__step${index === activeIndex ? ' lp-walkthrough__step--active' : ''}`}
              >
                <button
                  type="button"
                  className="lp-walkthrough__step-btn"
                  onClick={() => scrollToStep(index)}
                  aria-current={index === activeIndex ? 'step' : undefined}
                >
                  <span className="lp-walkthrough__step-marker" aria-hidden="true">
                    <span className="lp-walkthrough__step-index">
                      {String(index + 1).padStart(2, '0')}
                    </span>
                  </span>
                  <span className="lp-walkthrough__step-body">
                    <span className="lp-walkthrough__step-title">{step.title}</span>
                    <span className="lp-walkthrough__step-desc">{step.description}</span>
                  </span>
                </button>
              </li>
            ))}
          </ol>

          {/* Central visual — changes with the active step. */}
          <div className="lp-walkthrough__stage">
            <div className="lp-walkthrough__stage-inner">
              <WalkthroughVisual index={activeIndex} reducedMotion={reducedMotion} />
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

const STAGE_COPY: Record<string, { label: string; detail: string }> = {
  monitor: { label: 'Project field', detail: 'Snapshots, progress, expenditure, milestones' },
  detect: { label: 'Change engine', detail: 'Meaningful state and risk deltas' },
  investigate: { label: 'Evidence board', detail: 'Hypotheses ranked by supporting evidence' },
  decide: { label: 'Approval gate', detail: 'Validated recommendation, human authorised' },
  learn: { label: 'Memory', detail: 'Measured outcome feeds the next cycle' },
};

function WalkthroughVisual({ index, reducedMotion }: { index: number; reducedMotion: boolean }) {
  const step = WALKTHROUGH_STEPS[index];
  const copy = STAGE_COPY[step.id];

  return (
    <div className="lp-walkthrough__visual" key={step.id}>
      <span className="lp-walkthrough__visual-eyebrow">{copy.label}</span>
      <h3 className="lp-walkthrough__visual-title">{step.title}</h3>
      <p className="lp-walkthrough__visual-detail">{copy.detail}</p>
      <StageDiagram stepId={step.id} reducedMotion={reducedMotion} />
      <div className="lp-walkthrough__visual-footer">
        <span className="lp-walkthrough__visual-step">
          Step {String(index + 1).padStart(2, '0')} / {String(WALKTHROUGH_STEPS.length).padStart(2, '0')}
        </span>
        <span className="lp-walkthrough__visual-status">
          {index === WALKTHROUGH_STEPS.length - 1 ? 'Loop restarts' : 'In progress'}
        </span>
      </div>
    </div>
  );
}

function StageDiagram({ stepId, reducedMotion }: { stepId: string; reducedMotion: boolean }) {
  switch (stepId) {
    case 'monitor':
      return <MonitorDiagram />;
    case 'detect':
      return <DetectDiagram />;
    case 'investigate':
      return <InvestigateDiagram reducedMotion={reducedMotion} />;
    case 'decide':
      return <DecideDiagram />;
    case 'learn':
      return <LearnDiagram reducedMotion={reducedMotion} />;
    default:
      return null;
  }
}

function MonitorDiagram() {
  // A small sequence of snapshots accumulating over time.
  return (
    <svg className="lp-stage-svg" viewBox="0 0 320 150" role="img" aria-label="Four project snapshots arriving over successive monitoring cycles">
      <line x1="24" y1="118" x2="296" y2="118" stroke="var(--lp-border-strong)" strokeWidth="1" />
      {[0, 1, 2, 3].map((i) => {
        const x = 40 + i * 76;
        const height = 26 + i * 13;
        return (
          <g key={i}>
            <rect
              x={x}
              y={118 - height}
              width="18"
              height={height}
              rx="2"
              fill="var(--lp-accent)"
              opacity={0.25 + i * 0.2}
            />
            <text x={x + 9} y="134" textAnchor="middle" className="lp-stage-tick">
              T{i}
            </text>
          </g>
        );
      })}
      <text x="40" y="20" className="lp-stage-caption">
        Continuous snapshots
      </text>
    </svg>
  );
}

function DetectDiagram() {
  return (
    <svg className="lp-stage-svg" viewBox="0 0 320 150" role="img" aria-label="Snapshot comparison producing a cost over progress mismatch event">
      <text x="30" y="36" className="lp-stage-caption">
        Previous
      </text>
      <text x="30" y="76" className="lp-stage-caption">
        Current
      </text>
      <rect x="86" y="24" width="86" height="16" rx="3" fill="var(--lp-accent)" opacity="0.35" />
      <rect x="86" y="64" width="120" height="16" rx="3" fill="var(--lp-high-risk)" opacity="0.6" />
      <path d="M180 40 C 214 40, 214 72, 240 72" stroke="var(--lp-high-risk)" strokeWidth="1.5" fill="none" />
      <circle cx="248" cy="72" r="4" fill="var(--lp-high-risk)" />
      <text x="248" y="98" textAnchor="middle" className="lp-stage-caption lp-stage-caption--risk">
        Mismatch
      </text>
      <text x="212" y="130" textAnchor="middle" className="lp-stage-caption">
        Risk accelerating
      </text>
    </svg>
  );
}

function InvestigateDiagram({ reducedMotion }: { reducedMotion: boolean }) {
  const rows = [
    { label: 'Project history', weight: 0.85 },
    { label: 'Milestones', weight: 0.7 },
    { label: 'Financial signals', weight: 0.55 },
    { label: 'SHAP drivers', weight: 0.45 },
    { label: 'Peer context', weight: 0.3 },
  ];
  return (
    <div className="lp-stage-weights">
      {rows.map((row, i) => (
        <div key={row.label} className="lp-stage-weight">
          <span className="lp-stage-weight-label">{row.label}</span>
          <span className="lp-stage-weight-track">
            <span
              className="lp-stage-weight-fill"
              style={{
                width: `${row.weight * 100}%`,
                transitionDelay: reducedMotion ? '0ms' : `${i * 70}ms`,
              }}
            />
          </span>
        </div>
      ))}
      <p className="lp-stage-note">Evidence is consistent with — not verified cause.</p>
    </div>
  );
}

function DecideDiagram() {
  return (
    <div className="lp-stage-gate">
      <span className="lp-stage-gate-node lp-stage-gate-node--candidate">Candidate</span>
      <span className="lp-stage-gate-arrow" aria-hidden="true">→</span>
      <span className="lp-stage-gate-node lp-stage-gate-node--validated">Validated</span>
      <span className="lp-stage-gate-arrow" aria-hidden="true">→</span>
      <span className="lp-stage-gate-node lp-stage-gate-node--human">
        <span className="lp-stage-gate-node-label">Human</span>
        <span className="lp-stage-gate-node-value">Approval</span>
      </span>
    </div>
  );
}

function LearnDiagram({ reducedMotion }: { reducedMotion: boolean }) {
  return (
    <svg className="lp-stage-svg" viewBox="0 0 320 150" role="img" aria-label="Observed outcome feeding project and peer memory, then returning to monitoring">
      <circle cx="160" cy="75" r="46" fill="none" stroke="var(--lp-border-strong)" strokeWidth="1" />
      <path
        d="M160 29 A46 46 0 1 1 116 55"
        fill="none"
        stroke="var(--lp-healthy)"
        strokeWidth="2"
        strokeLinecap="round"
        style={reducedMotion ? undefined : { animation: 'lp-rotate 6s linear infinite' }}
      />
      {[
        { x: 160, y: 29, label: 'Monitor' },
        { x: 206, y: 75, label: 'Detect' },
        { x: 160, y: 121, label: 'Investigate' },
        { x: 114, y: 75, label: 'Learn' },
      ].map((point) => (
        <g key={point.label}>
          <circle cx={point.x} cy={point.y} r="3" fill="var(--lp-accent)" />
          <text x={point.x} y={point.y - 10} textAnchor="middle" className="lp-stage-caption">
            {point.label}
          </text>
        </g>
      ))}
      <text x="160" y="79" textAnchor="middle" className="lp-stage-caption">
        Observed outcome
      </text>
    </svg>
  );
}