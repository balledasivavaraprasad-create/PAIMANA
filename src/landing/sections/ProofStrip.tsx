import { PROOF_STRIP } from '../data/content';

/**
 * Capability proof strip.
 *
 * States what the platform does. Deliberately contains no customer names, no
 * logos, no counts, and no outcome percentages — nothing that would require
 * substantiation we cannot supply.
 */

const PROOF_DETAIL: Record<string, string> = {
  'Continuous Monitoring': 'Every cycle, not every report',
  'Predictive Risk': 'Cost, schedule, implementation',
  'Peer Intelligence': 'Context from comparable projects',
  'Agentic Investigation': 'Evidence gathered, not guessed',
  'Human-Gated Action': 'Approval before consequence',
  'Closed-Loop Outcomes': 'Measured, then remembered',
};

export default function ProofStrip() {
  return (
    <div className="lp-proof">
      <div className="lp-proof__inner">
        <ul className="lp-proof__list">
          {PROOF_STRIP.map((item) => (
            <li key={item} className="lp-proof__item">
              <span className="lp-proof__marker" aria-hidden="true" />
              <span className="lp-proof__text">
                <span className="lp-proof__label">{item}</span>
                <span className="lp-proof__detail">{PROOF_DETAIL[item]}</span>
              </span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}