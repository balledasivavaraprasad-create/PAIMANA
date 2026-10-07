import React, { useState } from 'react';

export const InvestigationSection: React.FC = () => {
  const [activeStep, setActiveStep] = useState(2);

  const steps = [
    {
      num: '01',
      title: 'TELEMETRY ANOMALY TRIGGER',
      desc: 'Risk acceleration delta (+18.4 pts) and expenditure/progress mismatch detected in continuous surveillance cycle.',
      detail: 'Event: PROGRESS_EXPENDITURE_MISMATCH • Trigger Confidence: 98%',
      tool: 'paimana_snapshot_audit',
    },
    {
      num: '02',
      title: 'PEER COHORT PROBE',
      desc: 'Benchmarked against 8 comparable motorway corridors; isolated target as an extreme 94th percentile outlier.',
      detail: 'Target DPHIS: 72.4 vs Peer Median: 46.1 (Deviation: +26.3 pts)',
      tool: 'peer_cohort_benchmark',
    },
    {
      num: '03',
      title: 'LEDGER & IPC BILLING AUDIT',
      desc: 'Executed financial velocity probe into lead contractor escrow accounts; identified unearned advance draws while asphalt package is stalled.',
      detail: 'Lead contractor withheld sub-payments to bridge girder fabricator resulting in critical-path stoppage.',
      tool: 'financial_velocity_probe',
    },
    {
      num: '04',
      title: 'COUNTER-EVIDENCE VERIFICATION',
      desc: 'Geotechnical borehole records confirmed ground stability at Indus River crossing, disproving soil liquefaction; the cause is not established.',
      detail: 'Liquefaction risk dismissed; supply chain liquidity confirmed as active constraint.',
      tool: 'geotech_record_scanner',
    },
    {
      num: '05',
      title: 'EXECUTIVE ACTION FORMULATION',
      desc: 'Formulated executive recommendation for milestone-gated escrow release and contractor warning letter; gated for human sign-off.',
      detail: 'Ready for Review • Required Authority: Member Finance / Project Director.',
      tool: 'recommendation_engine',
    },
  ];

  return (
    <section id="investigation" className="el-section" style={{ borderTop: '1px solid var(--el-border)', background: 'transparent' }}>
      <div className="el-container">
        <div className="el-sticky-layout">
          {/* Left Text */}
          <div className="reveal-on-scroll stagger-1">
            <div className="el-eyebrow">
              <span className="el-eyebrow-dot" style={{ backgroundColor: '#7C3AED' }} />
              <span>FORENSIC EVIDENCE PROTOCOL</span>
            </div>

            <h2 className="el-section-title">
              WHEN THE SIGNAL<br />
              MATTERS,<br />
              INVESTIGATE.
            </h2>

            <p className="el-subcopy">
              A static dashboard merely displays delayed expenditure figures. InfraBuild-AI cross-examines 
              contractor Interim Payment Certificates against satellite InSAR millimeter displacement, 
              physical weighbridge logs, and historical peer corridor benchmarks to assemble an evidence-backed diagnostic dossier.
            </p>

            {/* Interactive Step Navigator */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginTop: '32px' }}>
              {steps.map((st, idx) => {
                const isCurrent = activeStep === idx;
                return (
                  <button
                    key={st.num}
                    type="button"
                    onClick={() => setActiveStep(idx)}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '14px',
                      padding: '12px 18px',
                      borderRadius: 'var(--el-radius-md)',
                      backgroundColor: isCurrent ? 'var(--el-bg-surface, #FFFFFF)' : 'transparent',
                      border: isCurrent ? '1px solid var(--el-border)' : '1px solid transparent',
                      boxShadow: isCurrent ? '0 4px 16px rgba(0,0,0,0.04)' : 'none',
                      cursor: 'pointer',
                      textAlign: 'left',
                      transition: 'all 0.2s ease',
                    }}
                  >
                    <span
                      style={{
                        fontSize: '11px',
                        fontWeight: 700,
                        color: isCurrent ? 'var(--el-text-primary, #121314)' : 'var(--el-text-muted, #9CA3AF)',
                        fontFamily: 'var(--el-font-mono)',
                      }}
                    >
                      {st.num}
                    </span>
                    <span
                      style={{
                        fontSize: '13px',
                        fontWeight: isCurrent ? 700 : 500,
                        color: isCurrent ? 'var(--el-text-primary, #121314)' : 'var(--el-text-secondary, #4E5055)',
                      }}
                    >
                      {st.title}
                    </span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Right Product Visualization */}
          <div className="reveal-on-scroll stagger-2">
            <div className="el-product-card" style={{ padding: '36px' }}>
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  paddingBottom: '16px',
                  marginBottom: '24px',
                  borderBottom: '1px solid var(--el-border)',
                }}
              >
                <div>
                  <span style={{ fontSize: '11px', fontWeight: 700, color: 'var(--el-text-muted)', textTransform: 'uppercase' }}>
                    FORENSIC TRACE • STEP {steps[activeStep].num} OF 05
                  </span>
                  <div style={{ fontSize: '15px', fontWeight: 700, color: 'var(--el-text-primary, #121314)', marginTop: '2px' }}>
                    {steps[activeStep].title}
                  </div>
                </div>

                <span
                  style={{
                    fontSize: '11px',
                    fontWeight: 700,
                    padding: '4px 10px',
                    borderRadius: 'var(--el-radius-pill)',
                    backgroundColor: 'var(--badge-neutral-bg, #EFF6FF)',
                    color: 'var(--badge-neutral-text, #0284C7)',
                    border: '1px solid var(--badge-neutral-border, #BFDBFE)',
                  }}
                >
                  TOOL: {steps[activeStep].tool}
                </span>
              </div>

              {/* Description */}
              <p style={{ fontSize: '14px', color: 'var(--el-text-primary, #121314)', lineHeight: 1.6, marginBottom: '24px' }}>
                {steps[activeStep].desc}
              </p>

              {/* Observation Detail Card */}
              <div
                style={{
                  padding: '18px',
                  backgroundColor: 'var(--bg-inset, #FAFAF7)',
                  borderRadius: 'var(--el-radius-md)',
                  border: '1px solid var(--border-subtle, var(--el-border))',
                  marginBottom: '24px',
                }}
              >
                <div style={{ fontSize: '11px', fontWeight: 700, color: 'var(--el-text-muted)', textTransform: 'uppercase', marginBottom: '6px' }}>
                  SYNTHESIZED OBSERVATION
                </div>
                <div style={{ fontSize: '13px', color: 'var(--el-text-secondary, #374151)', lineHeight: 1.5 }}>
                  {steps[activeStep].detail}
                </div>
              </div>

              {/* Step Navigation Controls */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingTop: '16px', borderTop: '1px solid var(--el-border)' }}>
                <button
                  type="button"
                  disabled={activeStep === 0}
                  onClick={() => setActiveStep((prev) => Math.max(0, prev - 1))}
                  style={{
                    padding: '8px 16px',
                    borderRadius: 'var(--el-radius-pill)',
                    border: '1px solid var(--el-border)',
                    backgroundColor: 'var(--el-bg-surface, #FFFFFF)',
                    color: 'var(--el-text-primary)',
                    fontSize: '12px',
                    fontWeight: 600,
                    cursor: activeStep === 0 ? 'not-allowed' : 'pointer',
                    opacity: activeStep === 0 ? 0.4 : 1,
                  }}
                >
                  ← Previous Step
                </button>

                <div style={{ display: 'flex', gap: '6px' }}>
                  {steps.map((_, idx) => (
                    <span
                      key={idx}
                      style={{
                        width: idx === activeStep ? '20px' : '6px',
                        height: '6px',
                        borderRadius: '3px',
                        backgroundColor: idx === activeStep ? 'var(--el-text-primary, #121314)' : 'var(--border-strong, #D1D0C7)',
                        transition: 'all 0.2s ease',
                      }}
                    />
                  ))}
                </div>

                <button
                  type="button"
                  disabled={activeStep === steps.length - 1}
                  onClick={() => setActiveStep((prev) => Math.min(steps.length - 1, prev + 1))}
                  style={{
                    padding: '8px 16px',
                    borderRadius: 'var(--el-radius-pill)',
                    border: '1px solid var(--el-border)',
                    backgroundColor: 'var(--el-bg-surface, #FFFFFF)',
                    color: 'var(--el-text-primary)',
                    fontSize: '12px',
                    fontWeight: 600,
                    cursor: activeStep === steps.length - 1 ? 'not-allowed' : 'pointer',
                    opacity: activeStep === steps.length - 1 ? 0.4 : 1,
                  }}
                >
                  Next Step →
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};
