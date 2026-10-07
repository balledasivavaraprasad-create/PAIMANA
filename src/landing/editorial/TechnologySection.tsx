import React from 'react';

interface TechItem {
  name: string;
  role: string;
  detail: string;
}

const TECH_STACK: TechItem[] = [
  {
    name: 'XGBoost',
    role: 'Predict',
    detail: 'Gradient boosted trees calibrated on 400+ national infrastructure projects for non-linear DPHIS risk scoring.'
  },
  {
    name: 'SHAP',
    role: 'Explain',
    detail: 'Shapley additive explanations isolate exact feature contributions to risk drift without black-box opacity.'
  },
  {
    name: 'Peer Intelligence',
    role: 'Contextualize',
    detail: 'High-dimensional similarity indexing groups projects by typology, terrain, budget tier, and contracting model.'
  },
  {
    name: 'LLM Supervisor',
    role: 'Investigate',
    detail: 'Multi-source evidence correlation engine cross-validates contractor claims against satellite InSAR, material invoices, and borehole sensors.'
  },
  {
    name: 'n8n',
    role: 'Automate',
    detail: 'Declarative workflow orchestration triggers external contractor notifications, report builds, and data pulls.'
  },
  {
    name: 'Langfuse',
    role: 'Observe',
    detail: 'Continuous telemetry on agent traces, tool execution latencies, token consumption, and reasoning correctness.'
  },
  {
    name: 'MongoDB',
    role: 'Persist',
    detail: 'Schema-flexible document datastore maintaining time-series project snapshots, audit trails, and evidence logs.'
  },
  {
    name: 'React + TypeScript',
    role: 'Experience',
    detail: 'Zero-latency command center with high-density tabular views, SVG topologies, and verified design token discipline.'
  }
];

export const TechnologySection: React.FC = () => {
  return (
    <section id="technology" className="el-section" style={{ background: 'transparent', borderTop: '1px solid var(--el-border)' }}>
      <div className="el-container">
        <div className="el-eyebrow reveal-on-scroll stagger-1">
          <span className="el-eyebrow-dot" />
          <span>SYSTEM FOUNDATION</span>
        </div>

        <h2 className="el-section-title reveal-on-scroll stagger-2" style={{ maxWidth: '820px' }}>
          ENGINEERED FOR RIGOR.<br />
          NOT DEMO THEATRICS.
        </h2>

        <p className="el-subcopy reveal-on-scroll stagger-3" style={{ maxWidth: '640px' }}>
          Every layer of the InfraBuild-AI stack serves an explicit role in transforming raw project observations 
          into defensible, human-gated decisions.
        </p>

        {/* Role-based Architecture Grid */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
            gap: '24px',
            marginTop: '56px',
          }}
        >
          {TECH_STACK.map((item, idx) => (
            <div
              key={item.name}
              className={`reveal-on-scroll stagger-${(idx % 5) + 1}`}
              style={{
                background: 'var(--bg-panel, #FFFFFF)',
                border: '1px solid var(--border-subtle, var(--el-border))',
                borderRadius: '18px',
                padding: '28px',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
                boxShadow: 'var(--card-shadow, 0 4px 16px rgba(0,0,0,0.02))',
                transition: 'border-color 0.2s ease, transform 0.2s ease',
              }}
            >
              <div>
                <div style={{
                  display: 'inline-block',
                  fontSize: '11px',
                  fontWeight: 800,
                  textTransform: 'uppercase',
                  letterSpacing: '0.06em',
                  color: 'var(--badge-neutral-text, #0284C7)',
                  background: 'var(--badge-neutral-bg, #EFF6FF)',
                  border: '1px solid var(--badge-neutral-border, transparent)',
                  padding: '3px 8px',
                  borderRadius: '6px',
                  marginBottom: '16px',
                }}>
                  {item.role}
                </div>
                <h3 style={{
                  fontSize: '18px',
                  fontWeight: 800,
                  color: 'var(--el-text-primary, #121314)',
                  margin: '0 0 10px 0',
                  letterSpacing: '-0.01em',
                }}>
                  {item.name}
                </h3>
                <p style={{
                  fontSize: '13px',
                  color: 'var(--el-text-secondary, #737578)',
                  lineHeight: 1.55,
                  margin: 0,
                }}>
                  {item.detail}
                </p>
              </div>

              <div style={{ marginTop: '20px', paddingTop: '14px', borderTop: '1px dashed var(--border-subtle, #F0EFEA)', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span style={{ width: '5px', height: '5px', borderRadius: '50%', background: '#059669' }} />
                <span style={{ fontSize: '11px', color: 'var(--text-muted, #737578)', fontWeight: 600 }}>Production Verified</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};
