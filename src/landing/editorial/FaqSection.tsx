import React, { useState } from 'react';

interface FaqItem {
  q: string;
  a: string;
}

const FAQ_ITEMS: FaqItem[] = [
  {
    q: 'What is InfraBuild-AI / Paimana 2.0?',
    a: 'InfraBuild-AI is the continuous infrastructure intelligence layer designed for national planning commissions, provincial line departments, and project executing agencies. It tracks capital assets, predicts project health drift using calibrated gradient-boosted models, benchmarks anomalies against empirical peer cohorts, and conducts agentic forensic investigations before schedule or cost failures become public crises.'
  },
  {
    q: 'How does continuous monitoring work?',
    a: 'The platform ingests multi-stream telemetry—including financial IPC drawdowns, physical milestone inspections, contractor reports, drone LIDAR surveys, and meteorological data—without requiring manual report preparation. Automated snapshot differential engines detect divergence between physical completion and monetary disbursement in near real-time.'
  },
  {
    q: 'How is peer intelligence used?',
    a: 'Rather than evaluating an asset in a vacuum, InfraBuild-AI indexes projects into multi-dimensional similarity cohorts (by sector, terrain, procurement type, contractor tier, and scope). This isolates whether an anomaly is asset-specific or indicative of a systemic supply-chain disruption.'
  },
  {
    q: 'Does the system automatically intervene?',
    a: 'No. The platform enforces strict human-gated decision governance. While the agentic supervisor autonomously discovers evidence, models causal hypotheses, and formulates intervention recommendations, all financial adjustments, contractor notices, and resequencing orders require authorized human approval from Member Finance, the Project Director, or ECNEC.'
  },
  {
    q: 'How are recommendations validated?',
    a: 'Each recommendation is paired with an explicit counterfactual impact analysis, confidence score, and projected schedule recovery. Following approval, closed-loop telemetry tracks actual progress against the predicted counterfactual to calibrate future model weights.'
  },
  {
    q: 'How is uncertainty represented?',
    a: 'InfraBuild-AI adheres to strict epistemological transparency: observations (verified empirical data), inferences (machine model outputs), hypotheses (agent reasoning), and residual uncertainties are explicitly separated in all views and reports.'
  }
];

export const FaqSection: React.FC = () => {
  const [openIndex, setOpenIndex] = useState<number | null>(0);

  const toggle = (idx: number) => {
    setOpenIndex(openIndex === idx ? null : idx);
  };

  return (
    <section id="faq" className="el-section" style={{ background: 'transparent', borderTop: '1px solid var(--el-border)' }}>
      <div className="el-container">
        <div className="el-eyebrow reveal-on-scroll stagger-1">
          <span className="el-eyebrow-dot" />
          <span>QUESTIONS & ANSWERS</span>
        </div>

        <h2 className="el-section-title reveal-on-scroll stagger-2" style={{ maxWidth: '820px' }}>
          FREQUENTLY<br />
          ASKED QUESTIONS
        </h2>

        {/* Minimal Accordion List */}
        <div
          className="reveal-on-scroll stagger-3"
          style={{
            marginTop: '56px',
            maxWidth: '840px',
            borderTop: '1px solid var(--el-border)',
          }}
        >
          {FAQ_ITEMS.map((item, idx) => {
            const isOpen = openIndex === idx;
            return (
              <div
                key={idx}
                style={{
                  borderBottom: '1px solid var(--el-border)',
                  padding: '24px 0',
                }}
              >
                <button
                  onClick={() => toggle(idx)}
                  style={{
                    width: '100%',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    background: 'none',
                    border: 'none',
                    textAlign: 'left',
                    padding: 0,
                    cursor: 'pointer',
                    outline: 'none',
                  }}
                >
                  <span style={{
                    fontSize: '18px',
                    fontWeight: 700,
                    color: '#121314',
                    letterSpacing: '-0.01em',
                    paddingRight: '20px',
                  }}>
                    {item.q}
                  </span>
                  <span style={{
                    fontSize: '22px',
                    fontWeight: 400,
                    color: '#737578',
                    transform: isOpen ? 'rotate(45deg)' : 'none',
                    transition: 'transform 0.25s ease',
                    display: 'inline-block',
                  }}>
                    +
                  </span>
                </button>

                {isOpen && (
                  <p style={{
                    marginTop: '16px',
                    marginBottom: '4px',
                    fontSize: '14.5px',
                    lineHeight: 1.65,
                    color: '#4E5055',
                    maxWidth: '740px',
                  }}>
                    {item.a}
                  </p>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
};
