import React, { useState, useEffect } from 'react';

interface Stage {
  num: string;
  title: string;
  subtitle: string;
  description: string;
  uiHeader: string;
  uiBadge: string;
  uiContent: React.ReactNode;
}

const STAGES: Stage[] = [
  {
    num: '01',
    title: 'OBSERVE',
    subtitle: 'Continuous Multi-Stream Telemetry Ingestion',
    description: 'Autonomous data listeners ingest physical milestones, financial IPC drawdowns, meteorological anomalies, and drone surveys without manual reporting friction.',
    uiHeader: 'Data Ingestion Stream & Validation Engine',
    uiBadge: 'Ingestion Active',
    uiContent: (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px 16px', background: 'var(--bg-inset, #FAFAF7)', borderRadius: '12px', border: '1px solid var(--border-subtle, #ECEBE4)' }}>
          <div>
            <div style={{ fontSize: '13px', fontWeight: 700, color: 'var(--el-text-primary, #121314)' }}>PAIMANA ERP Core Ledger</div>
            <div style={{ fontSize: '11px', color: 'var(--text-muted, #737578)' }}>Financial dispatches, interim payment certificates (IPC-42)</div>
          </div>
          <span style={{ fontSize: '11px', color: '#15803D', fontWeight: 700 }}>Sync OK (2m ago)</span>
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px 16px', background: 'var(--bg-inset, #FAFAF7)', borderRadius: '12px', border: '1px solid var(--border-subtle, #ECEBE4)' }}>
          <div>
            <div style={{ fontSize: '13px', fontWeight: 700, color: 'var(--el-text-primary, #121314)' }}>Site Inspection & Drone Survey Feed</div>
            <div style={{ fontSize: '11px', color: 'var(--text-muted, #737578)' }}>Physical earthworks volume & structural completion vectors</div>
          </div>
          <span style={{ fontSize: '11px', color: '#15803D', fontWeight: 700 }}>Sync OK (14m ago)</span>
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px 16px', background: 'var(--bg-inset, #FAFAF7)', borderRadius: '12px', border: '1px solid var(--border-subtle, #ECEBE4)' }}>
          <div>
            <div style={{ fontSize: '13px', fontWeight: 700, color: 'var(--el-text-primary, #121314)' }}>Meteorological & Geo Hazard Station</div>
            <div style={{ fontSize: '11px', color: 'var(--text-muted, #737578)' }}>Monsoon precipitation anomaly vs historical seasonal baselines</div>
          </div>
          <span style={{ fontSize: '11px', color: '#15803D', fontWeight: 700 }}>Sync OK (1h ago)</span>
        </div>
      </div>
    ),
  },
  {
    num: '02',
    title: 'DETECT',
    subtitle: 'Dynamic Project Health Index Scoring (DPHIS)',
    description: 'Gradient boosted ensemble models calculate project risk trajectories, flagging subtle divergence between progress and spend before milestones fail.',
    uiHeader: 'DPHIS Drift & Anomaly Trigger Pipeline',
    uiBadge: 'Signal Triggered',
    uiContent: (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <span style={{ fontSize: '11px', color: 'var(--text-muted, #737578)', textTransform: 'uppercase', fontWeight: 700 }}>Anomaly Signature</span>
            <div style={{ fontSize: '16px', fontWeight: 800, color: '#DC2626' }}>Progress-Expenditure Decoupling</div>
          </div>
          <div style={{ textAlign: 'right' }}>
            <span style={{ fontSize: '11px', color: 'var(--text-muted, #737578)', fontWeight: 600 }}>DPHIS Impact</span>
            <div style={{ fontSize: '22px', fontWeight: 800, color: '#DC2626' }}>54.0 → 72.4</div>
          </div>
        </div>
        <div style={{ background: 'var(--bg-inset, #FAFAF7)', borderRadius: '12px', padding: '16px', border: '1px solid var(--border-subtle, #ECEBE4)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', marginBottom: '8px' }}>
            <span style={{ color: 'var(--text-muted, #737578)' }}>Physical Progress:</span>
            <span style={{ fontWeight: 700, color: 'var(--el-text-primary, #121314)' }}>58.1% (+1.7% in 60d)</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', marginBottom: '8px' }}>
            <span style={{ color: 'var(--text-muted, #737578)' }}>Budget Drawn (IPC):</span>
            <span style={{ fontWeight: 700, color: '#DC2626' }}>74.8% (+16.8% in 60d)</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px' }}>
            <span style={{ color: 'var(--text-muted, #737578)' }}>Drift Velocity:</span>
            <span style={{ fontWeight: 700, color: '#DC2626' }}>+3.2x normal statutory threshold</span>
          </div>
        </div>
      </div>
    ),
  },
  {
    num: '03',
    title: 'INVESTIGATE',
    subtitle: 'Multi-Source Forensic Evidence Synthesis',
    description: 'The forensic investigative engine cross-correlates contractor billing logs, InSAR ground telemetry, and peer cohort baselines to assemble an evidence-backed diagnostic dossier.',
    uiHeader: 'Forensic Evidence Correlation Engine',
    uiBadge: 'Diagnostic Evidence Assembled',
    uiContent: (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
        <div style={{ borderLeft: '3px solid #0284C7', paddingLeft: '12px' }}>
          <div style={{ fontSize: '11px', fontWeight: 800, color: '#0284C7', textTransform: 'uppercase' }}>Evidence Stream 1 — Supply Chain</div>
          <p style={{ fontSize: '12.5px', color: 'var(--el-text-primary, #121314)', margin: '4px 0 0 0', lineHeight: 1.4 }}>
            Discovered: Pre-stressed girder deliveries delayed 42 days due to steel import quota reassessment.
          </p>
        </div>
        <div style={{ borderLeft: '3px solid #7C3AED', paddingLeft: '12px' }}>
          <div style={{ fontSize: '11px', fontWeight: 800, color: '#7C3AED', textTransform: 'uppercase' }}>Evidence Stream 2 — Peer Cohort Benchmark</div>
          <p style={{ fontSize: '12.5px', color: 'var(--el-text-primary, #121314)', margin: '4px 0 0 0', lineHeight: 1.4 }}>
            Compared against 8 similar motorway packages: Peer median completion for Package B is 112 days vs current projected 214 days.
          </p>
        </div>
        <div style={{ borderLeft: '3px solid #059669', paddingLeft: '12px' }}>
          <div style={{ fontSize: '11px', fontWeight: 800, color: '#059669', textTransform: 'uppercase' }}>Diagnostic Finding</div>
          <p style={{ fontSize: '12.5px', color: 'var(--el-text-primary, #121314)', margin: '4px 0 0 0', lineHeight: 1.4 }}>
            Observed: Lead contractor advance draws are not reaching site subcontractors, creating an artificial supply squeeze; root cause is not established.
          </p>
        </div>
      </div>
    ),
  },
  {
    num: '04',
    title: 'ACT',
    subtitle: 'Human-Gated Executive Decision Protocol',
    description: 'High-leverage interventions are generated with explicit tradeoffs, counterfactual impact projections, and ministerial audit trails requiring authorized human sign-off.',
    uiHeader: 'Executive Intervention Approval Gate',
    uiBadge: 'Pending Ministerial Review',
    uiContent: (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
        <div style={{ background: 'var(--badge-intelligence-bg, #EFF6FF)', border: '1px solid var(--badge-intelligence-border, #BFDBFE)', borderRadius: '12px', padding: '16px' }}>
          <div style={{ fontSize: '12px', fontWeight: 800, color: 'var(--badge-intelligence-text, #1E40AF)', marginBottom: '4px' }}>
            Recommended Action: Direct Vendor Escrow + Milestone Resequencing
          </div>
          <p style={{ fontSize: '12px', color: 'var(--text-secondary, #1E3A8A)', margin: 0, lineHeight: 1.45 }}>
            Hold remaining 25% IPC disbursement in verified escrow; disburse directly against girder delivery invoices to restart erection.
          </p>
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingTop: '6px' }}>
          <span style={{ fontSize: '12px', color: 'var(--text-muted, #737578)' }}>Sign-off: Member Finance / NHA</span>
          <button style={{
            background: 'var(--el-text-primary, #121314)',
            color: 'var(--bg-base-contrast, #FFFFFF)',
            border: 'none',
            borderRadius: 'var(--el-radius-pill)',
            padding: '8px 18px',
            fontSize: '12px',
            fontWeight: 700,
            cursor: 'pointer',
          }}>
            Authorize Order
          </button>
        </div>
      </div>
    ),
  },
  {
    num: '05',
    title: 'LEARN',
    subtitle: 'Closed-Loop Calibration & Outcome Validation',
    description: 'Post-intervention milestones are tracked against predicted counterfactuals. The system continuously refines its predictive weights and causal priors.',
    uiHeader: 'Post-Intervention Outcome Calibration',
    uiBadge: 'Closed-Loop Confirmed',
    uiContent: (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span style={{ fontSize: '13px', fontWeight: 700, color: 'var(--el-text-primary, #121314)' }}>Intervention Result (+90 Days)</span>
          <span style={{ fontSize: '12px', color: '#15803D', fontWeight: 800 }}>Schedule Recovered: 38 Days</span>
        </div>
        <div style={{ background: 'var(--badge-healthy-bg, #F0FDF4)', border: '1px solid var(--badge-healthy-border, #BBF7D0)', borderRadius: '12px', padding: '16px' }}>
          <div style={{ fontSize: '12.5px', color: 'var(--badge-healthy-text, #166534)', lineHeight: 1.5 }}>
            DPHIS normalized from 72.4 → 44.1. Closed-loop calibration complete: increased predictive feature weight on early subcontractor advance drawdowns across all civil packages.
          </div>
        </div>
      </div>
    ),
  },
];

export const WalkthroughSection: React.FC = () => {
  const [selectedStage, setSelectedStage] = useState<number>(0);
  const [autoAdvance, setAutoAdvance] = useState<boolean>(true);
  const current = STAGES[selectedStage];

  // Auto-advance loop with user override
  useEffect(() => {
    if (!autoAdvance) return;
    const timer = setInterval(() => {
      setSelectedStage((prev) => (prev + 1) % STAGES.length);
    }, 4000);
    return () => clearInterval(timer);
  }, [autoAdvance]);

  return (
    <section id="how-it-works" className="el-section" style={{ background: 'transparent', borderTop: '1px solid var(--el-border)' }}>
      <div className="el-container">
        <div className="el-eyebrow reveal-on-scroll stagger-1">
          <span className="el-eyebrow-dot" />
          <span>SYSTEM ARCHITECTURE IN PRACTICE</span>
        </div>

        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', flexWrap: 'wrap', gap: '20px', marginBottom: '24px' }}>
          <h2 className="el-section-title reveal-on-scroll stagger-2" style={{ maxWidth: '820px', marginBottom: 0 }}>
            HOW INFRASTRUCTURE INTELLIGENCE OPERATES.
          </h2>

          <button
            type="button"
            onClick={() => setAutoAdvance(!autoAdvance)}
            style={{
              padding: '6px 14px',
              borderRadius: 'var(--el-radius-pill)',
              border: '1px solid var(--el-border)',
              background: autoAdvance ? 'var(--el-text-primary, #121314)' : 'var(--el-bg-surface, #FFFFFF)',
              color: autoAdvance ? 'var(--bg-base-contrast, #FFFFFF)' : 'var(--el-text-primary, #121314)',
              fontSize: '11.5px',
              fontWeight: 700,
              cursor: 'pointer',
              transition: 'all 0.2s ease',
            }}
          >
            {autoAdvance ? '⏸ Pause Auto-Cycle' : '▶ Enable Auto-Cycle'}
          </button>
        </div>

        <p className="el-subcopy reveal-on-scroll stagger-3" style={{ maxWidth: '640px' }}>
          A continuous five-stage loop transitioning from observational telemetry to autonomous investigation, 
          human-governed action, and closed-loop learning.
        </p>

        {/* 2-Column Storytelling Grid */}
        <div
          className="reveal-on-scroll stagger-4"
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
            gap: '56px',
            marginTop: '48px',
            alignItems: 'start',
          }}
        >
          {/* Left: Stage Navigation */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {STAGES.map((s, idx) => {
              const isActive = selectedStage === idx;
              return (
                <div
                  key={s.num}
                  onClick={() => {
                    setSelectedStage(idx);
                    setAutoAdvance(false);
                  }}
                  style={{
                    padding: '24px 28px',
                    borderRadius: '18px',
                    border: isActive ? '1px solid var(--el-border)' : '1px solid transparent',
                    background: isActive ? 'var(--el-bg-surface, #FFFFFF)' : 'transparent',
                    boxShadow: isActive ? '0 10px 28px rgba(0,0,0,0.04)' : 'none',
                    cursor: 'pointer',
                    transform: isActive ? 'translateX(6px)' : 'none',
                    transition: 'all 0.3s cubic-bezier(0.16, 1, 0.3, 1)',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '14px', marginBottom: '8px' }}>
                    <span
                      style={{
                        fontSize: '12px',
                        fontWeight: 800,
                        color: isActive ? 'var(--el-text-primary, #121314)' : 'var(--el-text-muted, #9CA3AF)',
                        fontFamily: 'var(--el-font-mono)',
                      }}
                    >
                      {s.num}
                    </span>
                    <h3
                      style={{
                        fontSize: '20px',
                        fontWeight: 800,
                        color: isActive ? 'var(--el-text-primary, #121314)' : 'var(--el-text-secondary, #737578)',
                        margin: 0,
                        letterSpacing: '-0.02em',
                      }}
                    >
                      {s.title}
                    </h3>
                  </div>
                  <p
                    style={{
                      fontSize: '13px',
                      color: isActive ? 'var(--el-text-secondary, #4B5563)' : 'var(--el-text-muted, #9CA3AF)',
                      lineHeight: 1.55,
                      margin: 0,
                    }}
                  >
                    {s.description}
                  </p>
                </div>
              );
            })}
          </div>

          {/* Right: Dynamic Product UI Surface */}
          <div style={{ position: 'sticky', top: '100px' }}>
            <div
              style={{
                background: 'var(--bg-panel, #FFFFFF)',
                border: '1px solid var(--el-border)',
                borderRadius: '24px',
                padding: '36px',
                boxShadow: 'var(--card-shadow, 0 24px 64px rgba(0, 0, 0, 0.05))',
                minHeight: '420px',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
              }}
            >
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{ fontSize: '11px', fontWeight: 800, color: 'var(--text-muted, #737578)', fontFamily: 'var(--el-font-mono)' }}>
                      STAGE {current.num}
                    </span>
                    <span style={{ fontSize: '11px', color: 'var(--border-strong, #D1D0C7)' }}>/</span>
                    <span style={{ fontSize: '12px', fontWeight: 700, color: 'var(--el-text-primary, #121314)' }}>
                      {current.uiHeader}
                    </span>
                  </div>
                  <span
                    style={{
                      fontSize: '11px',
                      fontWeight: 700,
                      padding: '3px 10px',
                      borderRadius: 'var(--el-radius-pill)',
                      background: 'var(--badge-neutral-bg, #F0EFEA)',
                      color: 'var(--badge-neutral-text, #121314)',
                    }}
                  >
                    {current.uiBadge}
                  </span>
                </div>

                <div style={{ marginBottom: '24px' }}>
                  <div style={{ fontSize: '15px', fontWeight: 700, color: 'var(--el-text-primary, #121314)', marginBottom: '4px' }}>
                    {current.subtitle}
                  </div>
                  <div style={{ fontSize: '12px', color: 'var(--text-muted, #737578)' }}>
                    Interactive telemetry simulation for national infrastructure assets.
                  </div>
                </div>

                {/* Dynamic Stage Content */}
                {current.uiContent}
              </div>

              {/* Progress dots at bottom */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '32px', paddingTop: '20px', borderTop: '1px solid var(--border-subtle, #F0EFEA)' }}>
                <span style={{ fontSize: '11px', color: 'var(--text-muted, #88898C)', fontWeight: 600 }}>
                  Stage {selectedStage + 1} of {STAGES.length}
                </span>
                <div style={{ display: 'flex', gap: '6px' }}>
                  {STAGES.map((_, idx) => (
                    <button
                      key={idx}
                      onClick={() => {
                        setSelectedStage(idx);
                        setAutoAdvance(false);
                      }}
                      style={{
                        width: idx === selectedStage ? '24px' : '6px',
                        height: '6px',
                        borderRadius: '3px',
                        background: idx === selectedStage ? 'var(--el-text-primary, #121314)' : 'var(--border-strong, #D1D0C7)',
                        border: 'none',
                        padding: 0,
                        cursor: 'pointer',
                        transition: 'all 0.25s ease',
                      }}
                    />
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};
