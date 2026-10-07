import React, { useState } from 'react';

interface PeerNode {
  id: string;
  name: string;
  code: string;
  sector: string;
  dphis: number;
  delta: string;
  status: 'critical' | 'stable' | 'monitored';
  cx: number;
  cy: number;
  desc: string;
}

const PEER_NODES: PeerNode[] = [
  {
    id: 'target',
    name: 'M-5 Sukkur–Multan Motorway (Package B)',
    code: 'PK-NHA-2021-084',
    sector: 'Highways & Motorways',
    dphis: 72.4,
    delta: '+14.3 Risk Accelerating',
    status: 'critical',
    cx: 260,
    cy: 160,
    desc: 'Cost/progress decoupling detected: IPC-42 disbursements outpace physical asphalt paving milestones by 14.8%.'
  },
  {
    id: 'peer1',
    name: 'Havelian–Thakot Expressway Ph 2',
    code: 'PK-NHA-2019-012',
    sector: 'Highways & Motorways',
    dphis: 44.2,
    delta: 'Normal variance (±1.8)',
    status: 'stable',
    cx: 90,
    cy: 80,
    desc: 'Treated cohort: early subcontractor advance escrow prevented schedule slippage during seismic remediation.'
  },
  {
    id: 'peer2',
    name: 'Swat Expressway Tunnel Section',
    code: 'PK-NHA-2020-044',
    sector: 'Highways & Motorways',
    dphis: 48.0,
    delta: 'Within cohort median',
    status: 'stable',
    cx: 430,
    cy: 90,
    desc: 'Geotechnical variance absorbed through pre-authorized contingency buffer without work stoppage.'
  },
  {
    id: 'peer3',
    name: 'Karachi–Hyderabad Motorway M-9 Rehab',
    code: 'PK-NHA-2022-091',
    sector: 'Highways & Motorways',
    dphis: 52.8,
    delta: '+3.1 Slight Drift',
    status: 'monitored',
    cx: 410,
    cy: 250,
    desc: 'Right-of-Way utility relocation bottleneck identified; automated inter-agency escalation dispatched.'
  }
];

export const HeroSection: React.FC<{ onOpenPlatform: () => void }> = ({ onOpenPlatform }) => {
  const [activeNodeId, setActiveNodeId] = useState<string>('target');
  const [isSimulating, setIsSimulating] = useState(false);
  const activeNode = PEER_NODES.find((n) => n.id === activeNodeId) || PEER_NODES[0];

  const handleSimulate = () => {
    setIsSimulating(true);
    setTimeout(() => {
      setIsSimulating(false);
    }, 1800);
  };

  return (
    <section id="hero" style={{ paddingTop: '150px', paddingBottom: '90px', position: 'relative' }}>
      <div className="el-container">
        {/* Eyebrow */}
        <div className="el-eyebrow reveal-on-scroll stagger-1">
          <span className="el-eyebrow-dot" />
          <span>INFRABUILD-AI • CONTINUOUS INFRASTRUCTURE INTELLIGENCE</span>
        </div>

        {/* Enormous Editorial Headline */}
        <h1 className="el-hero-title reveal-on-scroll stagger-2">
          YOUR INFRASTRUCTURE<br />
          PORTFOLIO CHANGES<br />
          BEFORE THE CRISIS DOES.
        </h1>

        {/* Supporting Paragraph */}
        <p className="el-subcopy reveal-on-scroll stagger-3">
          InfraBuild-AI continuously observes national capital assets across ministries, predicts non-linear cost and schedule drift, 
          benchmarks projects against relevant peer cohorts, and conducts forensic cross-audits before minor deviations compound into public crises.
        </p>

        {/* Action Buttons */}
        <div className="reveal-on-scroll stagger-4" style={{ display: 'flex', alignItems: 'center', gap: '14px', flexWrap: 'wrap' }}>
          <button type="button" onClick={onOpenPlatform} className="el-btn-black">
            <span>Sign in to get started</span>
            <span style={{ fontSize: '16px' }}>→</span>
          </button>
          <a
            href="#problem"
            onClick={(e) => {
              e.preventDefault();
              document.getElementById('problem')?.scrollIntoView({ behavior: 'smooth' });
            }}
            className="el-btn-outline"
          >
            <span>Explore Portfolio Intelligence</span>
          </a>
        </div>

        {/* Capability Chips */}
        <div className="el-chips-row reveal-on-scroll stagger-5">
          {[
            'Continuous Monitoring',
            'Predictive DPHIS Risk',
            'Peer Cohort Intelligence',
            'Forensic Cross-Auditing',
            'Human-Gated Decision Protocol',
          ].map((chip, idx) => (
            <div key={idx} className="el-chip">
              <span style={{ color: '#0284C7', fontSize: '10px' }}>●</span>
              <span>{chip}</span>
            </div>
          ))}
        </div>

        {/* SOFT PEACH BACKGROUND FIELD & LIVE PRODUCT MOCKUP */}
        <div
          className="el-soft-region el-soft-peach reveal-on-scroll"
          style={{
            marginTop: '64px',
            position: 'relative',
            border: '1px solid #FDE2D2'
          }}
        >
          {/* Subtle Ambient Radial Glow */}
          <div
            className="el-ambient-field-blur"
            style={{
              top: '-20%',
              right: '-10%',
              width: '550px',
              height: '550px',
              background: 'radial-gradient(circle, rgba(253, 216, 186, 0.6) 0%, rgba(255, 244, 237, 0) 70%)',
            }}
          />

          {/* Product Surface Card */}
          <div className="el-product-card" style={{ position: 'relative', zIndex: 1 }}>
            {/* Header bar of mockup */}
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                paddingBottom: '16px',
                marginBottom: '20px',
                borderBottom: '1px solid var(--el-border)',
                flexWrap: 'wrap',
                gap: '12px',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <div
                  style={{
                    width: '10px',
                    height: '10px',
                    borderRadius: '50%',
                    backgroundColor: '#DC2626',
                    boxShadow: '0 0 12px rgba(220, 38, 38, 0.9)',
                  }}
                />
                <div>
                  <div style={{ fontSize: '14.5px', fontWeight: 800, color: 'var(--el-text-primary)' }}>
                    {activeNode.name}
                  </div>
                  <div style={{ fontSize: '11px', color: 'var(--el-text-muted)', fontFamily: 'var(--el-font-mono)' }}>
                    {activeNode.code} • {activeNode.sector}
                  </div>
                </div>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <button
                  type="button"
                  onClick={handleSimulate}
                  style={{
                    background: isSimulating ? 'var(--el-text-primary)' : 'var(--el-bg-surface)',
                    color: isSimulating ? 'var(--bg-base-contrast, #070A12)' : 'var(--el-text-primary)',
                    border: '1px solid var(--el-border)',
                    borderRadius: 'var(--el-radius-pill)',
                    padding: '4px 12px',
                    fontSize: '11px',
                    fontWeight: 700,
                    cursor: 'pointer',
                    boxShadow: isSimulating ? '0 0 14px rgba(2, 132, 199, 0.4)' : 'none',
                    transition: 'all 0.2s ease',
                  }}
                >
                  {isSimulating ? '⚡ Ingesting Live Telemetry...' : '⚡ Pulse Telemetry Feed'}
                </button>

                <span
                  style={{
                    fontSize: '11px',
                    fontWeight: 700,
                    textTransform: 'uppercase',
                    letterSpacing: '0.04em',
                    padding: '4px 10px',
                    borderRadius: 'var(--el-radius-pill)',
                    backgroundColor: activeNode.status === 'critical' ? 'rgba(220, 38, 38, 0.1)' : 'rgba(5, 150, 105, 0.1)',
                    color: activeNode.status === 'critical' ? '#DC2626' : '#059669',
                    border: activeNode.status === 'critical' ? '1px solid rgba(220, 38, 38, 0.2)' : '1px solid rgba(5, 150, 105, 0.2)',
                  }}
                >
                  {activeNode.status === 'critical' ? 'HIGH RISK ALERT' : 'COHORT BENCHMARK'}
                </span>
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
                  LIVE TELEMETRY
                </span>
              </div>
            </div>

            {/* Main Interactive Topology Preview: Left SVG Peer Network, Right Project Intelligence */}
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(290px, 1fr))',
                gap: '24px',
                alignItems: 'stretch',
              }}
            >
              {/* LEFT: Project Relationship & Monitoring Visualization */}
              <div
                style={{
                  backgroundColor: 'var(--bg-inset, #FAFAF7)',
                  border: '1px solid var(--border-subtle, var(--el-border))',
                  borderRadius: 'var(--el-radius-md)',
                  padding: '20px',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between',
                  minHeight: '340px',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                  <span
                    style={{
                      fontSize: '11px',
                      fontWeight: 800,
                      color: 'var(--el-text-muted)',
                      textTransform: 'uppercase',
                      letterSpacing: '0.06em',
                    }}
                  >
                    PEER COHORT TOPOLOGY (28 CORRIDORS)
                  </span>
                  <span style={{ fontSize: '11px', color: '#0284C7', fontWeight: 700 }}>
                    Click Node to Inspect
                  </span>
                </div>

                {/* SVG Topology Network with flowing data packet animation */}
                <div style={{ position: 'relative', width: '100%', height: '240px' }}>
                  <svg viewBox="0 0 500 320" style={{ width: '100%', height: '100%', overflow: 'visible' }}>
                    {/* Background Connection Web */}
                    <line x1="90" y1="80" x2="260" y2="160" stroke="#E2E1DA" strokeWidth="1.5" />
                    <line x1="430" y1="90" x2="260" y2="160" stroke="#E2E1DA" strokeWidth="1.5" />
                    <line x1="410" y1="250" x2="260" y2="160" stroke="#E2E1DA" strokeWidth="1.5" />
                    <line x1="90" y1="80" x2="430" y2="90" stroke="#F0EFEA" strokeWidth="1" strokeDasharray="3 3" />
                    <line x1="430" y1="90" x2="410" y2="250" stroke="#F0EFEA" strokeWidth="1" strokeDasharray="3 3" />

                    {/* Flowing animated data packets running into target node */}
                    <line x1="90" y1="80" x2="260" y2="160" stroke="#0284C7" strokeWidth="2" className="el-flowing-line" opacity="0.8" />
                    <line x1="430" y1="90" x2="260" y2="160" stroke="#0284C7" strokeWidth="2" className="el-flowing-line" opacity="0.8" />
                    <line x1="410" y1="250" x2="260" y2="160" stroke="#0284C7" strokeWidth="2" className="el-flowing-line" opacity="0.8" />

                    {/* Active Highlight Connection Arcs */}
                    <line
                      x1={activeNode.cx}
                      y1={activeNode.cy}
                      x2="260"
                      y2="160"
                      stroke={activeNode.status === 'critical' ? '#DC2626' : '#0284C7'}
                      strokeWidth="3"
                    />

                    {/* Nodes */}
                    {PEER_NODES.map((node) => {
                      const isSelected = activeNodeId === node.id;
                      return (
                        <g
                          key={node.id}
                          onClick={() => setActiveNodeId(node.id)}
                          style={{ cursor: 'pointer' }}
                        >
                          {/* Radiating radar wave for selected/critical node */}
                          {isSelected && (
                            <circle
                              cx={node.cx}
                              cy={node.cy}
                              r="28"
                              fill="none"
                              stroke={node.status === 'critical' ? '#DC2626' : '#0284C7'}
                              strokeWidth="1.5"
                              opacity="0.5"
                              className="el-radar-ring"
                            />
                          )}
                          <circle
                            cx={node.cx}
                            cy={node.cy}
                            r={node.id === 'target' ? '20' : '15'}
                            fill={
                              node.id === 'target'
                                ? '#DC2626'
                                : isSelected
                                ? '#0284C7'
                                : '#FFFFFF'
                            }
                            stroke={
                              node.id === 'target'
                                ? '#991B1B'
                                : isSelected
                                ? '#0284C7'
                                : '#B5B4AC'
                            }
                            strokeWidth={isSelected ? '3' : '1.5'}
                            style={{ transition: 'all 0.3s cubic-bezier(0.16, 1, 0.3, 1)' }}
                          />
                          <text
                            x={node.cx}
                            y={node.cy + 32}
                            fill="var(--el-text-primary, #FFFFFF)"
                            fontSize="11"
                            fontWeight={isSelected ? '800' : '600'}
                            textAnchor="middle"
                          >
                            {node.id === 'target' ? 'TARGET ASSET' : node.code.split('-')[2]}
                          </text>
                        </g>
                      );
                    })}
                  </svg>
                </div>

                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    fontSize: '11px',
                    color: 'var(--el-text-muted)',
                    borderTop: '1px dashed #E2E1DA',
                    paddingTop: '10px',
                  }}
                >
                  <span>Similarity Index: <strong style={{ color: 'var(--el-text-primary)' }}>High (94.2%)</strong></span>
                  <span>Cohort Deviation: <strong style={{ color: '#DC2626' }}>+26.3 pts</strong></span>
                </div>
              </div>

              {/* RIGHT: Project Intelligence Panel */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '14px', justifyContent: 'space-between' }}>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
                  {/* Metric 1 */}
                  <div
                    style={{
                      padding: '18px',
                      backgroundColor: 'var(--bg-inset, #FAFAF7)',
                      borderRadius: 'var(--el-radius-md)',
                      border: '1px solid var(--border-subtle, var(--el-border))',
                      transition: 'transform 0.2s ease',
                    }}
                  >
                    <div style={{ fontSize: '11px', fontWeight: 800, color: 'var(--el-text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                      PROJECT DPHIS INDEX
                    </div>
                    <div style={{ fontSize: '36px', fontWeight: 800, color: activeNode.status === 'critical' ? '#DC2626' : 'var(--el-text-primary)', letterSpacing: '-0.02em', margin: '6px 0 2px 0' }}>
                      {isSimulating ? (activeNode.dphis + 1.2).toFixed(1) : activeNode.dphis}
                    </div>
                    <div style={{ fontSize: '12px', color: activeNode.status === 'critical' ? '#DC2626' : '#059669', fontWeight: 700 }}>
                      {activeNode.delta}
                    </div>
                  </div>

                  {/* Metric 2 */}
                  <div
                    style={{
                      padding: '18px',
                      backgroundColor: 'var(--bg-inset, #FAFAF7)',
                      borderRadius: 'var(--el-radius-md)',
                      border: '1px solid var(--border-subtle, var(--el-border))',
                    }}
                  >
                    <div style={{ fontSize: '11px', fontWeight: 800, color: 'var(--el-text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                      PEER COHORT MEDIAN
                    </div>
                    <div style={{ fontSize: '36px', fontWeight: 800, color: 'var(--el-text-primary)', letterSpacing: '-0.02em', margin: '6px 0 2px 0' }}>
                      46.1
                    </div>
                    <div style={{ fontSize: '12px', color: 'var(--el-text-muted)' }}>
                      94th percentile in cohort
                    </div>
                  </div>
                </div>

                {/* Event Description Card */}
                <div
                  style={{
                    padding: '18px',
                    backgroundColor: 'var(--bg-inset, #FAFAF7)',
                    borderRadius: 'var(--el-radius-md)',
                    border: '1px solid var(--border-subtle, var(--el-border))',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                    <span style={{ fontSize: '11px', fontWeight: 800, color: 'var(--el-text-muted)', textTransform: 'uppercase' }}>
                      DETECTED EVENT
                    </span>
                    <span style={{ fontSize: '11px', fontWeight: 800, color: '#DC2626', background: 'var(--badge-critical-bg, #FEE2E2)', padding: '3px 8px', borderRadius: '4px' }}>
                      Cost / Progress Mismatch
                    </span>
                  </div>
                  <div style={{ fontSize: '13px', color: 'var(--el-text-secondary)', lineHeight: 1.55 }}>
                    {activeNode.desc}
                  </div>
                </div>

                {/* Investigation Status Badge */}
                <div
                  style={{
                    padding: '14px 18px',
                    backgroundColor: 'var(--badge-intelligence-bg, #EFF6FF)',
                    borderRadius: 'var(--el-radius-md)',
                    border: '1px solid var(--badge-intelligence-border, #BFDBFE)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                  }}
                >
                  <div>
                    <span style={{ fontSize: '11px', fontWeight: 800, color: 'var(--badge-intelligence-text, #1E40AF)', textTransform: 'uppercase' }}>
                      FORENSIC CORRELATION ACTIVE (91% CONFIDENCE)
                    </span>
                    <div style={{ fontSize: '12px', color: 'var(--text-secondary, #1E3A8A)', marginTop: '2px' }}>
                      Diagnostic evidence assembled: Subcontractor liquidity bottleneck identified on Sukkur north bridge package; the cause is not established.
                    </div>
                  </div>
                  <span style={{ fontSize: '16px', color: 'var(--badge-intelligence-text, #1E40AF)', fontWeight: 800 }}>→</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};
