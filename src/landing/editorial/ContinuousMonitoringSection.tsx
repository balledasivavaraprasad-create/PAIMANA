import React, { useState } from 'react';

export const ContinuousMonitoringSection: React.FC = () => {
  const [activeCycle, setActiveCycle] = useState<'cycle1' | 'cycle2'>('cycle2');

  return (
    <section id="monitoring" className="el-section" style={{ borderTop: '1px solid var(--el-border)', background: 'transparent' }}>
      <div className="el-container">
        <div className="el-soft-region el-soft-lavender reveal-on-scroll">
          <div className="el-sticky-layout">
            {/* Left Editorial Text */}
            <div className="reveal-on-scroll stagger-1">
              <div className="el-eyebrow">
                <span className="el-eyebrow-dot" style={{ backgroundColor: '#7C3AED' }} />
                <span>CONTINUOUS OBSERVATIONAL ENGINE</span>
              </div>

              <h2 className="el-section-title">
                SEE WHAT<br />
                CHANGED.
              </h2>

              <p className="el-subcopy">
                InfraBuild-AI continuously compares the current project state against previous observations 
                rather than waiting for an officer to discover the problem during an ad-hoc quarterly review.
              </p>

              {/* Cycle Toggle Button */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginTop: '28px', flexWrap: 'wrap' }}>
                <button
                  type="button"
                  onClick={() => setActiveCycle('cycle1')}
                  style={{
                    padding: '10px 20px',
                    borderRadius: 'var(--el-radius-pill)',
                    backgroundColor: activeCycle === 'cycle1' ? 'var(--el-text-primary)' : 'var(--el-bg-surface)',
                    color: activeCycle === 'cycle1' ? 'var(--bg-base-contrast, #070A12)' : 'var(--el-text-primary)',
                    border: '1px solid var(--el-border)',
                    fontSize: '13px',
                    fontWeight: 600,
                    cursor: 'pointer',
                    boxShadow: activeCycle === 'cycle1' ? '0 4px 14px rgba(0,0,0,0.15)' : 'none',
                    transition: 'all 0.2s ease',
                  }}
                >
                  Baseline Snapshot (T-30d)
                </button>
                <button
                  type="button"
                  onClick={() => setActiveCycle('cycle2')}
                  style={{
                    padding: '10px 20px',
                    borderRadius: 'var(--el-radius-pill)',
                    backgroundColor: activeCycle === 'cycle2' ? 'var(--el-text-primary)' : 'var(--el-bg-surface)',
                    color: activeCycle === 'cycle2' ? 'var(--bg-base-contrast, #070A12)' : 'var(--el-text-primary)',
                    border: '1px solid var(--el-border)',
                    fontSize: '13px',
                    fontWeight: 600,
                    cursor: 'pointer',
                    boxShadow: activeCycle === 'cycle2' ? '0 4px 14px rgba(0,0,0,0.15)' : 'none',
                    transition: 'all 0.2s ease',
                  }}
                >
                  Current Telemetry (Latest)
                </button>
              </div>

              <div style={{ marginTop: '24px', fontSize: '12px', color: '#737578' }}>
                Automated multi-stream ingestion from provincial finance ledgers, site inspections, and drone survey feeds.
              </div>
            </div>

            {/* Right Comparison UI Card */}
            <div className="reveal-on-scroll stagger-2">
              <div className="el-product-card" style={{ padding: '32px' }}>
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
                      SURVEILLANCE CYCLE • SUKKUR-MULTAN CORRIDOR
                    </span>
                    <div style={{ fontSize: '14px', fontWeight: 700, color: 'var(--el-text-primary)', marginTop: '2px' }}>
                      {activeCycle === 'cycle1' ? 'Cycle T-30d • Pre-Disruption Baseline' : 'Cycle Current • Anomaly Trigger Active'}
                    </div>
                  </div>

                  <span
                    style={{
                      fontSize: '11.5px',
                      fontWeight: 700,
                      padding: '4px 10px',
                      borderRadius: 'var(--el-radius-pill)',
                      backgroundColor: activeCycle === 'cycle1' ? '#EFF6FF' : '#FEE2E2',
                      color: activeCycle === 'cycle1' ? '#2563EB' : '#DC2626',
                    }}
                  >
                    {activeCycle === 'cycle1' ? 'NOMINAL STATE' : 'DELTA DETECTED'}
                  </span>
                </div>

                {/* Side-by-side metric comparison */}
                <div
                  style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
                    gap: '16px',
                    marginBottom: '24px',
                  }}
                >
                  {/* Previous State */}
                  <div style={{ padding: '16px', backgroundColor: 'var(--bg-inset, #FAFAF7)', borderRadius: 'var(--el-radius-md)', border: '1px solid var(--el-border)' }}>
                    <div style={{ fontSize: '11px', fontWeight: 700, color: 'var(--el-text-muted)', textTransform: 'uppercase' }}>
                      PREVIOUS SNAPSHOT
                    </div>
                    <div style={{ fontSize: '28px', fontWeight: 800, color: 'var(--el-text-primary, #4B5563)', margin: '4px 0' }}>
                      54.0 <span style={{ fontSize: '13px', fontWeight: 500 }}>DPHIS</span>
                    </div>
                    <div style={{ fontSize: '12px', color: 'var(--el-text-muted, #6B7280)' }}>
                      Progress: 56.4% | IPC: 58.0%
                    </div>
                  </div>

                  {/* Current State */}
                  <div
                    style={{
                      padding: '16px',
                      backgroundColor: activeCycle === 'cycle2' ? 'var(--badge-critical-bg, #FEF2F2)' : 'var(--bg-inset, #FAFAF7)',
                      borderRadius: 'var(--el-radius-md)',
                      border: activeCycle === 'cycle2' ? '1px solid var(--badge-critical-border, #FECACA)' : '1px solid var(--el-border)',
                      transition: 'all 0.3s ease',
                    }}
                  >
                    <div style={{ fontSize: '11px', fontWeight: 700, color: activeCycle === 'cycle2' ? 'var(--badge-critical-text, #B91C1C)' : 'var(--el-text-muted)', textTransform: 'uppercase' }}>
                      CURRENT SNAPSHOT
                    </div>
                    <div style={{ fontSize: '28px', fontWeight: 800, color: activeCycle === 'cycle2' ? '#DC2626' : 'var(--el-text-primary)', margin: '4px 0' }}>
                      {activeCycle === 'cycle2' ? '72.4' : '54.0'}{' '}
                      <span style={{ fontSize: '13px', fontWeight: 500 }}>DPHIS</span>
                    </div>
                    <div style={{ fontSize: '12px', color: activeCycle === 'cycle2' ? '#DC2626' : 'var(--el-text-muted, #6B7280)', fontWeight: activeCycle === 'cycle2' ? 600 : 400 }}>
                      {activeCycle === 'cycle2' ? 'Progress: 58.1% | IPC: 74.8%' : 'Progress: 56.4% | IPC: 58.0%'}
                    </div>
                  </div>
                </div>

                {/* Detected Badges */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      padding: '12px 16px',
                      borderRadius: 'var(--el-radius-md)',
                      backgroundColor: activeCycle === 'cycle2' ? 'var(--badge-critical-bg, #FEE2E2)' : 'var(--bg-inset, #FAFAF7)',
                      border: '1px solid var(--el-border)',
                      transition: 'background-color 0.3s ease',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span style={{ color: activeCycle === 'cycle2' ? '#DC2626' : '#9CA3AF' }}>●</span>
                      <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--el-text-primary)' }}>
                        DPHIS Velocity Anomaly
                      </span>
                    </div>
                    <span style={{ fontSize: '12px', fontWeight: 700, color: activeCycle === 'cycle2' ? '#DC2626' : '#9CA3AF' }}>
                      {activeCycle === 'cycle2' ? '+18.4 pts in 30d' : 'Nominal Drift'}
                    </span>
                  </div>

                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      padding: '12px 16px',
                      borderRadius: 'var(--el-radius-md)',
                      backgroundColor: activeCycle === 'cycle2' ? 'var(--badge-attention-bg, #FEF3C7)' : 'var(--bg-inset, #FAFAF7)',
                      border: '1px solid var(--el-border)',
                      transition: 'background-color 0.3s ease',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span style={{ color: activeCycle === 'cycle2' ? '#D97706' : '#9CA3AF' }}>●</span>
                      <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--el-text-primary)' }}>
                        IPC-Physical Progress Decoupling
                      </span>
                    </div>
                    <span style={{ fontSize: '12px', fontWeight: 700, color: activeCycle === 'cycle2' ? '#D97706' : '#9CA3AF' }}>
                      {activeCycle === 'cycle2' ? '16.7% Divergence' : 'Aligned'}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};
