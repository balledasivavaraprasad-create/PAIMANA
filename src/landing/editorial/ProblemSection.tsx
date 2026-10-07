import React, { useState, useEffect } from 'react';

type RiskStage = 'normal' | 'small_change' | 'acceleration' | 'event';

const STAGE_KEYS: RiskStage[] = ['normal', 'small_change', 'acceleration', 'event'];

export const ProblemSection: React.FC = () => {
  const [stage, setStage] = useState<RiskStage>('small_change');
  const [isPlaying, setIsPlaying] = useState<boolean>(false);

  useEffect(() => {
    if (!isPlaying) return;
    const interval = setInterval(() => {
      setStage((prev) => {
        const nextIdx = (STAGE_KEYS.indexOf(prev) + 1) % STAGE_KEYS.length;
        return STAGE_KEYS[nextIdx];
      });
    }, 2800);
    return () => clearInterval(interval);
  }, [isPlaying]);

  const stageData = {
    normal: {
      label: '01 NORMAL BASELINE',
      dphis: 38.2,
      progress: 68.0,
      expenditure: 67.4,
      status: 'On Schedule & Budget',
      statusColor: '#15803D',
      bgColor: '#DCFCE7',
      event: 'Nominal Operations',
      note: 'All physical milestones and IPC disbursements align precisely with CDWP/ECNEC baseline sanction.',
    },
    small_change: {
      label: '02 SMALL DIVERGENCE',
      dphis: 48.6,
      progress: 70.1,
      expenditure: 74.5,
      status: 'Minor Draw Divergence',
      statusColor: '#B45309',
      bgColor: '#FEF3C7',
      event: 'Progress Velocity Slowdown',
      note: 'Financial draw begins outpacing verified physical earthwork milestones by 4.4 percentage points.',
    },
    acceleration: {
      label: '03 RISK ACCELERATION',
      dphis: 64.8,
      progress: 71.0,
      expenditure: 82.0,
      status: 'High Acceleration Warning',
      statusColor: '#C2410C',
      bgColor: '#FFEDD5',
      event: 'Subcontractor Billing Stall',
      note: '30-day DPHIS slope accelerates sharply (+16.2 pts). Critical-path asphalt equipment idling on site.',
    },
    event: {
      label: '04 CRITICAL EVENT',
      dphis: 78.4,
      progress: 71.2,
      expenditure: 88.5,
      status: 'Statutory Threshold Breach',
      statusColor: '#B91C1C',
      bgColor: '#FEE2E2',
      event: 'Cost-Progress Mismatch Triggered',
      note: 'DPHIS crosses 75 threshold. PC-1 revision risk triggered; automated forensic cross-audit of contractor IPC ledger and InSAR telemetry initiated for human review.',
    },
  };

  const cur = stageData[stage];

  return (
    <section id="problem" className="el-section" style={{ borderTop: '1px solid var(--el-border)', background: 'transparent' }}>
      <div className="el-container">
        <div className="el-sticky-layout">
          {/* Left: Editorial Statement & Interactive Stage Selector */}
          <div className="el-sticky-sidebar reveal-on-scroll stagger-1">
            <div className="el-eyebrow">
              <span className="el-eyebrow-dot" />
              <span>THE LATENT RISK PATTERN</span>
            </div>

            <h2 className="el-section-title">
              RISK DOESN'T ARRIVE<br />
              ALL AT ONCE.
            </h2>

            <p className="el-subcopy">
              Infrastructure failures rarely begin with an overnight disaster. They accumulate through quiet, unobserved misalignments: 
              a delayed utility clearance, a minor divergence between fund draw and physical earthwork, or an unacknowledged subcontractor liquidity dispute.
            </p>

            {/* Timeline Simulator Controls */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginTop: '20px' }}>
              <button
                type="button"
                onClick={() => setIsPlaying(!isPlaying)}
                style={{
                  padding: '8px 18px',
                  borderRadius: 'var(--el-radius-pill)',
                  backgroundColor: isPlaying ? '#DC2626' : '#121314',
                  color: '#FFFFFF',
                  border: 'none',
                  fontSize: '12px',
                  fontWeight: 700,
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  boxShadow: '0 4px 14px rgba(0,0,0,0.15)',
                  transition: 'all 0.2s ease',
                }}
              >
                <span>{isPlaying ? '⏸ Pause Evolution' : '▶ Play Timeline Simulation'}</span>
              </button>
              {isPlaying && (
                <span style={{ fontSize: '11px', color: '#DC2626', fontWeight: 600 }}>
                  ● Scrubbing Risk Stages...
                </span>
              )}
            </div>

            {/* Stage Selector Pills */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginTop: '24px' }}>
              {(
                [
                  { id: 'normal', key: '01 NORMAL BASELINE', score: '38.2' },
                  { id: 'small_change', key: '02 SMALL DIVERGENCE', score: '48.6' },
                  { id: 'acceleration', key: '03 RISK ACCELERATION', score: '64.8' },
                  { id: 'event', key: '04 CRITICAL EVENT', score: '78.4' },
                ] as { id: RiskStage; key: string; score: string }[]
              ).map((item) => {
                const isSelected = stage === item.id;
                return (
                  <button
                    key={item.id}
                    onClick={() => {
                      setStage(item.id);
                      setIsPlaying(false);
                    }}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      padding: '12px 18px',
                      borderRadius: 'var(--el-radius-md)',
                      backgroundColor: isSelected ? '#FFFFFF' : 'transparent',
                      border: isSelected ? '1px solid var(--el-border)' : '1px solid transparent',
                      boxShadow: isSelected ? '0 6px 20px rgba(0,0,0,0.06)' : 'none',
                      cursor: 'pointer',
                      textAlign: 'left',
                      transform: isSelected ? 'translateX(4px)' : 'none',
                      transition: 'all 0.25s cubic-bezier(0.16, 1, 0.3, 1)',
                    }}
                  >
                    <span
                      style={{
                        fontSize: '12.5px',
                        fontWeight: isSelected ? 800 : 500,
                        color: isSelected ? 'var(--el-text-primary)' : 'var(--el-text-secondary)',
                      }}
                    >
                      {item.key}
                    </span>
                    <span
                      style={{
                        fontSize: '12px',
                        fontWeight: 800,
                        color: isSelected ? 'var(--el-text-primary)' : 'var(--el-text-muted)',
                        fontFamily: 'var(--el-font-mono)',
                      }}
                    >
                      DPHIS: {item.score}
                    </span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Right: Dynamic Product Vector */}
          <div className="reveal-on-scroll stagger-2">
            <div className="el-product-card" style={{ padding: '36px' }}>
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  paddingBottom: '16px',
                  marginBottom: '28px',
                  borderBottom: '1px solid var(--el-border)',
                }}
              >
                <div>
                  <span
                    style={{
                      fontSize: '11px',
                      fontWeight: 800,
                      color: 'var(--el-text-muted)',
                      textTransform: 'uppercase',
                      letterSpacing: '0.04em',
                    }}
                  >
                    PROJECT TELEMETRY VECTOR • SUKKUR-MULTAN CORRIDOR
                  </span>
                  <div style={{ fontSize: '15px', fontWeight: 800, color: 'var(--el-text-primary)', marginTop: '2px' }}>
                    {cur.event}
                  </div>
                </div>

                <span
                  style={{
                    fontSize: '12px',
                    fontWeight: 800,
                    padding: '4px 14px',
                    borderRadius: 'var(--el-radius-pill)',
                    backgroundColor: cur.bgColor,
                    color: cur.statusColor,
                    transition: 'all 0.3s ease',
                  }}
                >
                  {cur.status}
                </span>
              </div>

              {/* DPHIS Metric Display */}
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                  gap: '20px',
                  marginBottom: '32px',
                }}
              >
                <div style={{ backgroundColor: 'var(--bg-inset, #FAFAF7)', padding: '20px', borderRadius: 'var(--el-radius-md)', border: '1px solid var(--el-border)' }}>
                  <span style={{ fontSize: '11px', fontWeight: 800, color: 'var(--el-text-muted)', textTransform: 'uppercase' }}>
                    DPHIS RISK INDEX
                  </span>
                  <div
                    style={{
                      fontSize: '46px',
                      fontWeight: 800,
                      color: cur.dphis > 60 ? '#DC2626' : cur.dphis > 45 ? '#D97706' : '#15803D',
                      letterSpacing: '-0.03em',
                      margin: '6px 0 2px 0',
                      transition: 'color 0.4s ease',
                    }}
                  >
                    {cur.dphis}
                  </div>
                  <div style={{ fontSize: '11px', color: 'var(--el-text-muted)' }}>
                    Scale: 0 (Min) – 100 (Critical Failure)
                  </div>
                </div>

                <div style={{ backgroundColor: 'var(--bg-inset, #FAFAF7)', padding: '20px', borderRadius: 'var(--el-radius-md)', border: '1px solid var(--el-border)' }}>
                  <span style={{ fontSize: '11px', fontWeight: 800, color: 'var(--el-text-muted)', textTransform: 'uppercase' }}>
                    EXPENDITURE / PROGRESS
                  </span>
                  <div
                    style={{
                      fontSize: '46px',
                      fontWeight: 800,
                      color: 'var(--el-text-primary)',
                      letterSpacing: '-0.03em',
                      margin: '6px 0 2px 0',
                    }}
                  >
                    {cur.expenditure}
                    <span style={{ fontSize: '20px', fontWeight: 600, color: 'var(--el-text-muted)' }}>%</span>
                  </div>
                  <div style={{ fontSize: '11px', color: 'var(--el-text-muted)' }}>
                    Physical Verified: <strong style={{ color: 'var(--el-text-primary)' }}>{cur.progress}%</strong>
                  </div>
                </div>
              </div>

              {/* Divergence Progress Bar Visualization */}
              <div style={{ marginBottom: '28px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', marginBottom: '8px' }}>
                  <span style={{ fontWeight: 700, color: 'var(--el-text-primary)' }}>Financial Drawdown (IPC Certified)</span>
                  <span style={{ fontWeight: 800, color: 'var(--el-text-primary)' }}>{cur.expenditure}%</span>
                </div>
                <div style={{ width: '100%', height: '10px', backgroundColor: 'var(--border-subtle, #F0EFEA)', borderRadius: '5px', overflow: 'hidden', marginBottom: '16px' }}>
                  <div
                    style={{
                      width: `${cur.expenditure}%`,
                      height: '100%',
                      backgroundColor: cur.expenditure - cur.progress > 10 ? '#DC2626' : '#0284C7',
                      transition: 'width 0.6s cubic-bezier(0.16, 1, 0.3, 1), background-color 0.4s ease',
                      borderRadius: '5px',
                    }}
                  />
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', marginBottom: '8px' }}>
                  <span style={{ fontWeight: 700, color: 'var(--el-text-primary)' }}>Physical Completion (LIDAR Survey)</span>
                  <span style={{ fontWeight: 800, color: 'var(--el-text-primary)' }}>{cur.progress}%</span>
                </div>
                <div style={{ width: '100%', height: '10px', backgroundColor: 'var(--border-subtle, #F0EFEA)', borderRadius: '5px', overflow: 'hidden' }}>
                  <div
                    style={{
                      width: `${cur.progress}%`,
                      height: '100%',
                      backgroundColor: '#059669',
                      transition: 'width 0.6s cubic-bezier(0.16, 1, 0.3, 1)',
                      borderRadius: '5px',
                    }}
                  />
                </div>
              </div>

              {/* Explanatory Observation Box */}
              <div
                style={{
                  padding: '18px',
                  backgroundColor: 'var(--bg-inset, #FAFAF7)',
                  borderRadius: 'var(--el-radius-md)',
                  border: '1px solid var(--el-border)',
                }}
              >
                <div style={{ fontSize: '11px', fontWeight: 800, color: 'var(--el-text-muted)', textTransform: 'uppercase', marginBottom: '4px' }}>
                  EPIDEMIOLOGY NOTE
                </div>
                <div style={{ fontSize: '13px', color: 'var(--el-text-secondary)', lineHeight: 1.55 }}>
                  {cur.note}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};
