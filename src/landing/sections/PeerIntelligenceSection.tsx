import { useEffect, useState } from 'react';
import { useInView, useReducedMotion } from '../motion';

/**
 * Peer intelligence section.
 *
 * Visualises cohort formation, the median, and the target's deviation, then
 * contrasts the two interpretations that matter: a project-specific anomaly
 * versus cohort-wide deterioration.
 *
 * Peer evidence is explicitly framed as context, never causation.
 */

const PEERS = [
  { id: 'p1', x: 18, y: 30, label: 'A', dphis: 44 },
  { id: 'p2', x: 78, y: 24, label: 'B', dphis: 48 },
  { id: 'p3', x: 14, y: 66, label: 'C', dphis: 42 },
  { id: 'p4', x: 74, y: 68, label: 'D', dphis: 50 },
  { id: 'p5', x: 30, y: 82, label: 'E', dphis: 46 },
  { id: 'p6', x: 86, y: 46, label: 'F', dphis: 45 },
];

const MEDIAN = 46;
const TARGET_DPHIS = 72;
const SIMILARITY_CRITERIA = ['Sector', 'Scale band', 'Terrain', 'Contract type', 'Age band'];

export default function PeerIntelligenceSection() {
  const { ref, isInView } = useInView<HTMLElement>();
  const reducedMotion = useReducedMotion();
  const [formed, setFormed] = useState(0);

  useEffect(() => {
    if (!isInView) return;
    if (reducedMotion) {
      setFormed(PEERS.length);
      return;
    }
    const timers = PEERS.map((_, index) => window.setTimeout(() => setFormed(index + 1), 260 + index * 190));
    return () => timers.forEach((id) => window.clearTimeout(id));
  }, [isInView, reducedMotion]);

  return (
    <section className="lp-section lp-peers" id="peer-intelligence" ref={ref}>
      <div className="landing-container">
        <div className="lp-section__header">
          <span className="lp-section__eyebrow">Peer intelligence</span>
          <h2 className="lp-section__title">A project is not understood in isolation.</h2>
          <p className="lp-section__description">
            A DPHIS of 72 means one thing on its own and something different entirely next to a cohort
            sitting at 46. Cohort matching makes the difference visible — and shows whether a project
            is genuinely an outlier or simply part of a sector-wide trend.
          </p>
        </div>

        <p className="lp-conceptual-note" role="note">
          <span className="lp-conceptual-note-tag">Illustrative example</span>
          Cohort members, medians, and deviations below are conceptual. Peer comparison is
          contextual evidence and is not evidence of causation.
        </p>

        <div className="lp-peers__layout">
          <div className="lp-peers__visual">
            <CohortDiagram formed={formed} />

            <div className="lp-peers__stats">
              <div className="lp-peers__stat">
                <span className="lp-peers__stat-label">Peer median DPHIS</span>
                <span className="lp-peers__stat-value">{MEDIAN}</span>
              </div>
              <div className="lp-peers__stat lp-peers__stat--target">
                <span className="lp-peers__stat-label">Target DPHIS</span>
                <span className="lp-peers__stat-value">{TARGET_DPHIS}</span>
              </div>
              <div className="lp-peers__stat lp-peers__stat--deviation">
                <span className="lp-peers__stat-label">Peer deviation</span>
                <span className="lp-peers__stat-value">+{TARGET_DPHIS - MEDIAN}</span>
              </div>
            </div>
          </div>

          <aside className="lp-peers__criteria">
            <h3 className="lp-peers__criteria-title">Cohort match criteria</h3>
            <ul className="lp-peers__criteria-list">
              {SIMILARITY_CRITERIA.map((criterion) => (
                <li key={criterion} className="lp-peers__criteria-item">
                  <span className="lp-peers__criteria-check" aria-hidden="true">
                    <svg width="11" height="11" viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth="1.6">
                      <path d="M2.5 6.2l2.4 2.3L9.5 3.9" strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                  </span>
                  {criterion}
                </li>
              ))}
            </ul>
            <p className="lp-peers__criteria-note">
              Cohort matching is explicit and inspectable. Where too few comparable projects exist,
              the product reports an insufficient cohort rather than widening the match.
            </p>
          </aside>
        </div>

        <div className="lp-peers__outcomes">
          <article className="lp-peers__outcome lp-peers__outcome--anomaly">
            <header className="lp-peers__outcome-header">
              <span className="lp-peers__outcome-tag">Interpretation A</span>
              <h3 className="lp-peers__outcome-title">Project-specific anomaly</h3>
            </header>
            <p className="lp-peers__outcome-body">
              The cohort is stable while this project alone deteriorates. The investigation should
              focus on project-level evidence — its own milestones, expenditure pattern, and contract
              history.
            </p>
          </article>

          <article className="lp-peers__outcome lp-peers__outcome--deterioration">
            <header className="lp-peers__outcome-header">
              <span className="lp-peers__outcome-tag">Interpretation B</span>
              <h3 className="lp-peers__outcome-title">Cohort-wide deterioration</h3>
            </header>
            <p className="lp-peers__outcome-body">
              Similar projects are moving together, which points at a shared external factor. Here the
              useful question is not which project failed but what changed across the sector.
            </p>
          </article>
        </div>

        <p className="lp-peers__disclaimer">
          The system distinguishes these two patterns. It does not claim to have identified the cause
          of either.
        </p>
      </div>
    </section>
  );
}

function CohortDiagram({ formed }: { formed: number }) {
  const cx = 400;
  const cy = 190;

  return (
    <svg
      className="lp-cohort"
      viewBox="0 0 800 380"
      role="img"
      aria-label="Target project at the centre of a peer cohort of six comparable projects, with a peer median of 46 and a target DPHIS of 72, a deviation of plus 26."
    >
      {/* Cohort boundary */}
      <ellipse
        cx={cx}
        cy={cy}
        rx={300}
        ry={150}
        className="lp-cohort__boundary"
        data-state={formed >= PEERS.length ? 'complete' : 'forming'}
      />
      <text x={cx} y={28} textAnchor="middle" className="lp-cohort__caption">
        PEER COHORT · {formed} / {PEERS.length} matched
      </text>

      {/* Similarity links */}
      {PEERS.slice(0, formed).map((peer) => {
        const px = (peer.x / 100) * 800;
        const py = (peer.y / 100) * 380;
        return (
          <line
            key={peer.id}
            x1={cx}
            y1={cy}
            x2={px}
            y2={py}
            className="lp-cohort__link"
          />
        );
      })}

      {/* Peer nodes with their DPHIS */}
      {PEERS.map((peer, index) => {
        const visible = index < formed;
        const px = (peer.x / 100) * 800;
        const py = (peer.y / 100) * 380;
        return (
          <g key={peer.id} className="lp-cohort__peer" data-state={visible ? 'visible' : 'hidden'}>
            <circle cx={px} cy={py} r="17" className="lp-cohort__peer-ring" />
            <text x={px} y={py + 4} textAnchor="middle" className="lp-cohort__peer-label">
              {peer.label}
            </text>
            <text x={px} y={py + 32} textAnchor="middle" className="lp-cohort__peer-value">
              {peer.dphis}
            </text>
          </g>
        );
      })}

      {/* Deviation vector from median to target */}
      {formed >= PEERS.length && (
        <g className="lp-cohort__deviation">
          <line x1={cx + 118} y1={cy - 84} x2={cx} y2={cy} className="lp-cohort__deviation-line" />
          <text x={cx + 126} y={cy - 88} className="lp-cohort__deviation-label">
            +{TARGET_DPHIS - MEDIAN}
          </text>
        </g>
      )}

      {/* Target node */}
      <g className="lp-cohort__target" data-state={formed >= PEERS.length ? 'deviating' : 'idle'}>
        <circle cx={cx} cy={cy} r="34" className="lp-cohort__target-halo" />
        <circle cx={cx} cy={cy} r="24" className="lp-cohort__target-ring" />
        <circle cx={cx} cy={cy} r="11" className="lp-cohort__target-core" />
        <text x={cx} y={cy + 62} textAnchor="middle" className="lp-cohort__target-label">
          TARGET PROJECT
        </text>
        <text x={cx} y={cy + 78} textAnchor="middle" className="lp-cohort__target-value">
          DPHIS {TARGET_DPHIS}
        </text>
      </g>
    </svg>
  );
}