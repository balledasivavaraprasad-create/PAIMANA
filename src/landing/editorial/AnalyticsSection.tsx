import React, { useState } from 'react';

type AnalyticsTab = 'matrix' | 'trend' | 'heatmap' | 'deviation';

export const AnalyticsSection: React.FC = () => {
  const [activeTab, setActiveTab] = useState<AnalyticsTab>('matrix');
  const [hoveredPoint, setHoveredPoint] = useState<string | null>(null);

  return (
    <section id="analytics" className="el-section" style={{ background: 'transparent', borderTop: '1px solid var(--el-border)' }}>
      <div className="el-container">
        <div className="el-eyebrow reveal-on-scroll stagger-1">
          <span className="el-eyebrow-dot" />
          <span>PORTFOLIO INTELLIGENCE WORKSTATION</span>
        </div>

        <h2 className="el-section-title reveal-on-scroll stagger-2" style={{ maxWidth: '820px' }}>
          SEE THE PORTFOLIO.<br />
          NOT JUST THE PROJECT.
        </h2>

        <p className="el-subcopy reveal-on-scroll stagger-3" style={{ maxWidth: '640px' }}>
          Infrastructure assets rarely fail in complete isolation. Aggregate multi-sector telemetry across provincial 
          and federal ministries into systemic risk topologies, macro variance patterns, and cohort-wide intervention trajectories.
        </p>

        {/* Workstation Container */}
        <div
          className="reveal-on-scroll stagger-4"
          style={{
            marginTop: '56px',
            background: 'var(--bg-panel, #FFFFFF)',
            border: '1px solid var(--border-subtle, var(--el-border))',
            borderRadius: '24px',
            boxShadow: 'var(--card-shadow, 0 24px 64px rgba(0, 0, 0, 0.05))',
            overflow: 'hidden',
          }}
        >
          {/* Workstation Header Bar */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: '16px 28px',
              borderBottom: '1px solid var(--border-subtle, #EFEFEA)',
              background: 'var(--bg-inset, #FDFDFC)',
              flexWrap: 'wrap',
              gap: '12px',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#0284C7', boxShadow: '0 0 8px #0284C7' }} />
              <span style={{ fontSize: '13.5px', fontWeight: 700, color: 'var(--el-text-primary)', letterSpacing: '-0.01em' }}>
                National Portfolio Telemetry Workstation
              </span>
              <span style={{ fontSize: '11px', color: 'var(--el-text-muted)', background: 'var(--bg-subtle, #F0EFEA)', padding: '2px 8px', borderRadius: '12px', fontWeight: 600 }}>
                428 Assets Monitored
              </span>
            </div>

            {/* View Selector Tabs */}
            <div style={{ display: 'flex', gap: '4px', background: 'var(--bg-subtle, #F3F2EE)', padding: '3px', borderRadius: '10px' }}>
              {(
                [
                  { id: 'matrix', label: 'Risk Matrix' },
                  { id: 'trend', label: 'DPHIS Drift' },
                  { id: 'heatmap', label: 'Sector Variance' },
                  { id: 'deviation', label: 'Intervention Impact' },
                ] as { id: AnalyticsTab; label: string }[]
              ).map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  style={{
                    padding: '8px 18px',
                    fontSize: '12px',
                    fontWeight: activeTab === tab.id ? 800 : 500,
                    color: activeTab === tab.id ? 'var(--el-text-primary)' : 'var(--el-text-muted)',
                    background: activeTab === tab.id ? 'var(--el-bg-surface, #FFFFFF)' : 'transparent',
                    border: 'none',
                    borderRadius: '8px',
                    cursor: 'pointer',
                    boxShadow: activeTab === tab.id ? '0 2px 6px rgba(0,0,0,0.08)' : 'none',
                    transform: activeTab === tab.id ? 'scale(1.02)' : 'none',
                    transition: 'all 0.2s cubic-bezier(0.16, 1, 0.3, 1)',
                  }}
                >
                  {tab.label}
                </button>
              ))}
            </div>
          </div>

          {/* Workstation Canvas / Visual Viewport */}
          <div style={{ padding: '36px', minHeight: '440px', background: 'var(--bg-panel, #FFFFFF)' }}>
            {activeTab === 'matrix' && (
              <div className="el-analytics-grid">
                {/* 2x2 Risk Quadrant Graphic */}
                <div
                  style={{
                    border: '1px solid var(--border-subtle, #ECEBE4)',
                    borderRadius: '16px',
                    padding: '24px',
                    background: 'var(--bg-inset, #FAFAF7)',
                    position: 'relative',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '16px' }}>
                    <span style={{ fontSize: '11px', fontWeight: 800, color: 'var(--el-text-primary, #121314)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                      Severity vs Velocity Topology
                    </span>
                    <span style={{ fontSize: '11px', color: 'var(--text-muted, #737578)' }}>
                      {hoveredPoint ? `Selected: ${hoveredPoint}` : 'Hover Node to Inspect'}
                    </span>
                  </div>

                  <svg viewBox="0 0 460 270" style={{ width: '100%', height: 'auto', display: 'block', overflow: 'hidden' }}>
                    {/* Grid Lines */}
                    <line x1="55" y1="135" x2="425" y2="135" stroke="#E2E1DA" strokeDasharray="3 3" />
                    <line x1="240" y1="20" x2="240" y2="235" stroke="#E2E1DA" strokeDasharray="3 3" />

                    {/* Quadrant Region Labels */}
                    <text x="65" y="42" fill="#9CA3AF" fontSize="9.5" fontWeight="600" letterSpacing="0.03em">LOW SEVERITY / HIGH VELOCITY</text>
                    <text x="250" y="42" fill="#DC2626" fontSize="9.5" fontWeight="700" letterSpacing="0.03em">CRITICAL CONVERGENCE (18)</text>
                    <text x="65" y="222" fill="#9CA3AF" fontSize="9.5" fontWeight="600" letterSpacing="0.03em">STABLE BASELINE (312)</text>
                    <text x="250" y="222" fill="#D97706" fontSize="9.5" fontWeight="600" letterSpacing="0.03em">PERSISTENT CHRONIC (98)</text>

                    {/* Stable cluster */}
                    <circle cx="95" cy="180" r="4.5" fill="#9CA3AF" opacity="0.6" />
                    <circle cx="125" cy="190" r="5.5" fill="#9CA3AF" opacity="0.6" />
                    <circle cx="145" cy="170" r="4.5" fill="#9CA3AF" opacity="0.6" />
                    <circle cx="170" cy="200" r="6" fill="#9CA3AF" opacity="0.6" />
                    <circle cx="115" cy="160" r="4.5" fill="#9CA3AF" opacity="0.6" />

                    {/* Chronic cluster */}
                    <circle cx="280" cy="170" r="5" fill="#F59E0B" opacity="0.75" />
                    <circle cx="310" cy="185" r="4.5" fill="#F59E0B" opacity="0.75" />
                    <circle cx="345" cy="165" r="6" fill="#F59E0B" opacity="0.75" />

                    {/* Critical Outliers with hover states and cleanly separated text labels */}
                    {/* Node 1: M-5 Motorway */}
                    <g
                      onMouseEnter={() => setHoveredPoint('M-5 Motorway (Pkg B) - 72.4 DPHIS')}
                      onMouseLeave={() => setHoveredPoint(null)}
                      style={{ cursor: 'pointer' }}
                    >
                      <circle cx="310" cy="85" r="9" fill="#DC2626" opacity="0.9" />
                      <circle cx="310" cy="85" r="16" fill="none" stroke="#DC2626" strokeWidth="1" className="el-radar-ring" opacity="0.35" />
                      <rect x="235" y="58" width="150" height="18" rx="4" fill="rgba(254, 242, 242, 0.92)" stroke="#FECACA" strokeWidth="0.8" />
                      <text x="310" y="70" textAnchor="middle" fill="#DC2626" fontSize="10" fontWeight="800">M-5 Motorway (Pkg B)</text>
                    </g>

                    {/* Node 2: Tarbela 5th Ext */}
                    <g
                      onMouseEnter={() => setHoveredPoint('Tarbela 5th Ext - 68.0 DPHIS')}
                      onMouseLeave={() => setHoveredPoint(null)}
                      style={{ cursor: 'pointer' }}
                    >
                      <circle cx="260" cy="112" r="7.5" fill="#DC2626" opacity="0.85" />
                      <rect x="208" y="126" width="104" height="17" rx="4" fill="rgba(255, 255, 255, 0.9)" stroke="#E5E7EB" strokeWidth="0.8" />
                      <text x="260" y="138" textAnchor="middle" fill="#1F2937" fontSize="9.5" fontWeight="700">Tarbela 5th Ext</text>
                    </g>

                    {/* Node 3: HVDC Matiari-Lahore */}
                    <g
                      onMouseEnter={() => setHoveredPoint('HVDC Matiari-Lahore - 64.2 DPHIS')}
                      onMouseLeave={() => setHoveredPoint(null)}
                      style={{ cursor: 'pointer' }}
                    >
                      <circle cx="365" cy="110" r="7.5" fill="#DC2626" opacity="0.85" />
                      <rect x="305" y="126" width="120" height="17" rx="4" fill="rgba(255, 255, 255, 0.9)" stroke="#E5E7EB" strokeWidth="0.8" />
                      <text x="365" y="138" textAnchor="middle" fill="#1F2937" fontSize="9.5" fontWeight="700">HVDC Matiari-Lahore</text>
                    </g>

                    {/* Axes */}
                    <line x1="55" y1="20" x2="55" y2="235" stroke="#4B5563" strokeWidth="1.5" />
                    <line x1="55" y1="235" x2="425" y2="235" stroke="#4B5563" strokeWidth="1.5" />
                    <text x="425" y="254" fill="#6B7280" fontSize="9.5" fontWeight="600" textAnchor="end" letterSpacing="0.04em">DPHIS SEVERITY →</text>
                    <text x="-128" y="32" transform="rotate(-90)" fill="#6B7280" fontSize="9.5" fontWeight="600" textAnchor="middle" letterSpacing="0.04em">DRIFT VELOCITY →</text>
                  </svg>
                </div>

                {/* Top Critical Signals Summary */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                  <div style={{ fontSize: '11px', fontWeight: 800, color: 'var(--el-text-primary, #121314)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                    Active Divergence Alerts
                  </div>

                  {[
                    {
                      id: 'PRJ-M5-084',
                      name: 'M-5 Sukkur–Multan Motorway Pkg B',
                      sector: 'Highways & Motorways',
                      risk: '72.4 DPHIS',
                      trend: '+18 in 30d',
                      cause: 'IPC disbursements ahead of physical asphalt milestones by 16.7%',
                    },
                    {
                      id: 'PRJ-TAR-310',
                      name: 'Tarbela Hydropower 5th Extension',
                      sector: 'Hydropower & Dams',
                      risk: '68.0 DPHIS',
                      trend: '+12 in 30d',
                      cause: 'Tunnel 5 penstock intake fabrication delayed 44 days',
                    },
                    {
                      id: 'PRJ-MAT-502',
                      name: 'HVDC Grid Line Matiari–Lahore',
                      sector: 'Power Transmission',
                      risk: '64.2 DPHIS',
                      trend: '+9 in 30d',
                      cause: 'Tower foundation Right-of-Way compensation disputes',
                    },
                  ].map((item) => (
                    <div
                      key={item.id}
                      style={{
                        padding: '16px',
                        background: 'var(--bg-inset, #FAFAF7)',
                        border: '1px solid var(--border-subtle, #ECEBE4)',
                        borderRadius: '14px',
                        display: 'flex',
                        flexDirection: 'column',
                        gap: '6px',
                        transition: 'transform 0.2s ease, border-color 0.2s ease',
                      }}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.transform = 'translateY(-2px)';
                        e.currentTarget.style.borderColor = 'var(--border-strong, #C5C3BA)';
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.transform = 'none';
                        e.currentTarget.style.borderColor = 'var(--border-subtle, #ECEBE4)';
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                          <span style={{ fontSize: '11px', fontWeight: 800, color: '#DC2626', background: 'var(--badge-critical-bg, #FEE2E2)', padding: '2px 6px', borderRadius: '4px' }}>
                            {item.risk}
                          </span>
                          <span style={{ fontSize: '13px', fontWeight: 700, color: 'var(--el-text-primary, #121314)' }}>{item.name}</span>
                        </div>
                        <span style={{ fontSize: '11px', fontWeight: 700, color: '#DC2626' }}>{item.trend}</span>
                      </div>
                      <div style={{ fontSize: '12px', color: 'var(--text-muted, #737578)' }}>{item.cause}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {activeTab === 'trend' && (
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', flexWrap: 'wrap', gap: '12px' }}>
                  <div>
                    <h3 style={{ fontSize: '16px', fontWeight: 800, color: 'var(--el-text-primary, #121314)', margin: '0 0 4px 0' }}>
                      6-Month DPHIS Drift Across National Sectors
                    </h3>
                    <p style={{ fontSize: '12px', color: 'var(--text-muted, #737578)', margin: 0 }}>
                      Cross-portfolio baseline progression with machine-forecasted intervention trajectories.
                    </p>
                  </div>
                  <div style={{ display: 'flex', gap: '16px', fontSize: '12px', flexWrap: 'wrap' }}>
                    <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <span style={{ width: '12px', height: '3px', background: '#DC2626' }} /> Highways (+24%)
                    </span>
                    <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <span style={{ width: '12px', height: '3px', background: '#0284C7' }} /> Energy (+6%)
                    </span>
                    <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <span style={{ width: '12px', height: '3px', background: '#059669' }} /> Water / Irrigation (-4%)
                    </span>
                  </div>
                </div>

                <svg viewBox="0 0 800 240" style={{ width: '100%', height: 'auto', background: 'var(--bg-inset, #FAFAF7)', borderRadius: '12px', border: '1px solid var(--border-subtle, #ECEBE4)', padding: '16px' }}>
                  <line x1="50" y1="40" x2="760" y2="40" stroke="#EAE9E2" strokeDasharray="3 3" />
                  <line x1="50" y1="100" x2="760" y2="100" stroke="#EAE9E2" strokeDasharray="3 3" />
                  <line x1="50" y1="160" x2="760" y2="160" stroke="#EAE9E2" strokeDasharray="3 3" />
                  <line x1="50" y1="210" x2="760" y2="210" stroke="#D1D0C7" />

                  <text x="40" y="45" fill="#9CA3AF" fontSize="10" textAnchor="end">80</text>
                  <text x="40" y="105" fill="#9CA3AF" fontSize="10" textAnchor="end">60</text>
                  <text x="40" y="165" fill="#9CA3AF" fontSize="10" textAnchor="end">40</text>
                  <text x="40" y="215" fill="#9CA3AF" fontSize="10" textAnchor="end">20</text>

                  {/* Highways Curve (Red) */}
                  <path d="M 60 170 C 180 160, 320 145, 450 110 C 580 80, 680 55, 750 48" fill="none" stroke="#DC2626" strokeWidth="3" />
                  {/* Energy Curve (Blue) */}
                  <path d="M 60 150 C 180 148, 320 140, 450 135 C 580 130, 680 120, 750 115" fill="none" stroke="#0284C7" strokeWidth="2.5" />
                  {/* Water Curve (Green) */}
                  <path d="M 60 140 C 180 145, 320 155, 450 162 C 580 170, 680 178, 750 182" fill="none" stroke="#059669" strokeWidth="2.5" strokeDasharray="4 2" />

                  <circle cx="750" cy="48" r="6" fill="#DC2626" />
                  <text x="750" y="34" fill="#DC2626" fontSize="11" fontWeight="800" textAnchor="middle">72.4 DPHIS</text>
                </svg>
              </div>
            )}

            {activeTab === 'heatmap' && (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px' }}>
                {[
                  { sector: 'National Highways & Motorways', total: 142, atRisk: 34, avgDphis: 58, drift: '+14%' },
                  { sector: 'Power Generation & Grid', total: 118, atRisk: 19, avgDphis: 49, drift: '+5%' },
                  { sector: 'Water & Irrigation Dams', total: 86, atRisk: 9, avgDphis: 38, drift: '-2%' },
                  { sector: 'Railways & Mass Transit', total: 82, atRisk: 21, avgDphis: 61, drift: '+18%' },
                ].map((sec) => (
                  <div
                    key={sec.sector}
                    style={{
                      background: 'var(--bg-inset, #FAFAF7)',
                      border: '1px solid var(--border-subtle, #ECEBE4)',
                      borderRadius: '16px',
                      padding: '24px',
                      display: 'flex',
                      flexDirection: 'column',
                      justifyContent: 'space-between',
                      transition: 'transform 0.2s ease, box-shadow 0.2s ease',
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.transform = 'translateY(-3px)';
                      e.currentTarget.style.boxShadow = '0 12px 28px rgba(0,0,0,0.04)';
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.transform = 'none';
                      e.currentTarget.style.boxShadow = 'none';
                    }}
                  >
                    <div>
                      <div style={{ fontSize: '11px', fontWeight: 800, color: 'var(--text-muted, #737578)', textTransform: 'uppercase', marginBottom: '8px' }}>
                        Sector Cohort
                      </div>
                      <div style={{ fontSize: '15px', fontWeight: 800, color: 'var(--el-text-primary, #121314)', marginBottom: '16px' }}>
                        {sec.sector}
                      </div>
                    </div>

                    <div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px', fontSize: '12px' }}>
                        <span style={{ color: 'var(--text-muted, #737578)' }}>Avg DPHIS:</span>
                        <span style={{ fontWeight: 800, color: 'var(--el-text-primary, #121314)' }}>{sec.avgDphis}</span>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px', fontSize: '12px' }}>
                        <span style={{ color: 'var(--text-muted, #737578)' }}>Critical Assets:</span>
                        <span style={{ fontWeight: 800, color: '#DC2626' }}>{sec.atRisk} / {sec.total}</span>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px' }}>
                        <span style={{ color: 'var(--text-muted, #737578)' }}>Drift Velocity:</span>
                        <span style={{ fontWeight: 800, color: sec.drift.startsWith('+') ? '#DC2626' : '#059669' }}>
                          {sec.drift}
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {activeTab === 'deviation' && (
              <div style={{ padding: '12px 0' }}>
                <div style={{ marginBottom: '20px' }}>
                  <h3 style={{ fontSize: '16px', fontWeight: 800, color: 'var(--el-text-primary, #121314)', margin: '0 0 6px 0' }}>
                    Intervention Outcome Differential (Governed vs Unaddressed Cohorts)
                  </h3>
                  <p style={{ fontSize: '12px', color: 'var(--text-muted, #737578)', margin: 0 }}>
                    Empirical difference in delay trajectory when agentic recommendations are executed within 14 days of anomaly detection.
                  </p>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '24px' }}>
                  <div style={{ background: 'var(--badge-healthy-bg, #F0FDF4)', border: '1px solid var(--badge-healthy-border, #BBF7D0)', borderRadius: '18px', padding: '28px' }}>
                    <div style={{ fontSize: '11px', fontWeight: 800, color: 'var(--badge-healthy-text, #15803D)', textTransform: 'uppercase', marginBottom: '8px' }}>
                      Recommended Action Executed (94 Projects)
                    </div>
                    <div style={{ fontSize: '42px', fontWeight: 800, color: 'var(--badge-healthy-text, #14532D)', letterSpacing: '-0.02em', marginBottom: '8px' }}>
                      -42%
                    </div>
                    <p style={{ fontSize: '13.5px', color: 'var(--badge-healthy-text, #166534)', margin: 0, lineHeight: 1.55 }}>
                      Average reduction in subsequent milestone delay variance after structured contractor audit or milestone resequencing.
                    </p>
                  </div>

                  <div style={{ background: 'var(--badge-critical-bg, #FEF2F2)', border: '1px solid var(--badge-critical-border, #FECACA)', borderRadius: '18px', padding: '28px' }}>
                    <div style={{ fontSize: '11px', fontWeight: 800, color: 'var(--badge-critical-text, #B91C1C)', textTransform: 'uppercase', marginBottom: '8px' }}>
                      Delayed or Unaddressed (47 Projects)
                    </div>
                    <div style={{ fontSize: '42px', fontWeight: 800, color: 'var(--badge-critical-text, #7F1D1D)', letterSpacing: '-0.02em', marginBottom: '8px' }}>
                      +118 Days
                    </div>
                    <p style={{ fontSize: '13.5px', color: 'var(--badge-critical-text, #991B1B)', margin: 0, lineHeight: 1.55 }}>
                      Uncontrolled compounding delay and cumulative budget overrun when signal investigation is deferred beyond 30 days.
                    </p>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </section>
  );
};
