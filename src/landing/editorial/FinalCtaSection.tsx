import React, { useState } from 'react';

interface FinalCtaSectionProps {
  onEnterApp?: () => void;
}

interface IncidentCase {
  id: string;
  project: string;
  location: string;
  status: string;
  sources: { name: string; icon: string; count: string; active: boolean }[];
  rows: {
    type: 'Topic' | 'Action' | 'Decisions' | 'Cohort Risk' | 'Audit Seal';
    pillColor: { bg: string; text: string };
    title: string;
    subtext: string;
    officer: string;
    avatar: string;
  }[];
}

const CASES: IncidentCase[] = [
  {
    id: 'n25',
    project: 'N-25 / M-8 Chaman Corridor Alignment',
    location: 'Balochistan • KM 48+200',
    status: 'Live Continuous Monitoring',
    sources: [
      { name: 'Copernicus InSAR', icon: '🛰️', count: '14mm/yr drift', active: true },
      { name: 'SAP S/4HANA ERP', icon: '💼', count: 'Voucher #4829', active: true },
      { name: 'Drone Orthomosaic', icon: '🛸', count: '0.42m resolution', active: true },
      { name: 'Field IoT Sensors', icon: '📡', count: '89.2% moisture', active: true },
      { name: 'PC-I Specification', icon: '📋', count: 'Rev-2 Benchmark', active: false },
      { name: 'Seismic Hazards', icon: '⚡', count: 'Active Fault 3B', active: false },
    ],
    rows: [
      {
        type: 'Topic',
        pillColor: { bg: '#FFE4E6', text: '#E11D48' },
        title: 'Sub-base asphalt compaction variance at KM 48+200',
        subtext: 'Synthetic Aperture Radar reveals progressive subgrade differential settlement across embankment sector 4',
        officer: 'Engr. Tariq Aziz (Chief Engineer)',
        avatar: 'TA',
      },
      {
        type: 'Action',
        pillColor: { bg: '#E0F2FE', text: '#0284C7' },
        title: 'Forensic team dispatched for core density sampling',
        subtext: 'Independent lab results scheduled for cross-verification against contractor quality assurance ledger',
        officer: 'Dr. Sarah Khan (DG M&E)',
        avatar: 'SK',
      },
      {
        type: 'Decisions',
        pillColor: { bg: '#DCFCE7', text: '#16A34A' },
        title: '"Ministerial hold placed on Milestone Voucher #4829 ($4.2M)"',
        subtext: 'Payment gated under Human-in-the-Loop Sovereign Protocol until laboratory clearance certificate verified',
        officer: 'Member Finance & Planning',
        avatar: 'MF',
      },
      {
        type: 'Cohort Risk',
        pillColor: { bg: '#F3E8FF', text: '#9333EA' },
        title: 'Anomaly 3.4x higher than provincial road sector benchmark',
        subtext: 'Matches early warning failure signature observed during FY23 Sukkur-Hyderabad alignment collapse',
        officer: 'Cohort Benchmark Engine',
        avatar: 'CB',
      },
      {
        type: 'Audit Seal',
        pillColor: { bg: '#FFEDD5', text: '#EA580C' },
        title: 'Cryptographic forensic audit package sealed #SHA-256',
        subtext: 'Immutable provenance record forwarded to Planning Commission (CDWP/ECNEC) portfolio dashboard',
        officer: 'Cryptographic Ledger',
        avatar: 'CL',
      },
    ],
  },
  {
    id: 'dasu',
    project: 'Dasu Hydropower Tunnel Divergence',
    location: 'Khyber Pakhtunkhwa • Section 3',
    status: 'High Priority Telemetry',
    sources: [
      { name: 'Sub-surface Acoustic', icon: '🌊', count: '2.4 kHz resonance', active: true },
      { name: 'ERP Ledger', icon: '💼', count: 'IPC #8902', active: true },
      { name: 'Geodetic Extensometer', icon: '📐', count: '6.8mm deformation', active: true },
      { name: 'Borehole Piezometer', icon: '💧', count: '14.2 bar pressure', active: true },
      { name: 'PC-I Specification', icon: '📋', count: 'Civil Works Rev-1', active: false },
      { name: 'Rockmass Cohort', icon: '⛰️', count: 'Class IV Metamorphic', active: false },
    ],
    rows: [
      {
        type: 'Topic',
        pillColor: { bg: '#FFE4E6', text: '#E11D48' },
        title: 'Crown shear strain exceeding structural tolerance threshold',
        subtext: 'Triaxial piezometers indicate pore pressure accumulation in upstream fault gouge zone',
        officer: 'Project Director Dasu',
        avatar: 'PD',
      },
      {
        type: 'Action',
        pillColor: { bg: '#E0F2FE', text: '#0284C7' },
        title: 'Emergency reinforcement shotcrete and rock-bolt resequencing',
        subtext: 'Contractor instructed to pause excavation benching until secondary steel ribs installed',
        officer: 'Resident Consultant Team',
        avatar: 'RC',
      },
      {
        type: 'Decisions',
        pillColor: { bg: '#DCFCE7', text: '#16A34A' },
        title: '"Authorized interim variation order for specialized forepoling canopy"',
        subtext: 'Contingency fund allocation approved with mandatory 48-hr geodetic re-survey',
        officer: 'Federal Power Secretary',
        avatar: 'PS',
      },
      {
        type: 'Cohort Risk',
        pillColor: { bg: '#F3E8FF', text: '#9333EA' },
        title: 'Hydropower peer cohort: Top 8% shear risk profile',
        subtext: 'Cross-referenced against Neelum-Jhelum and Tarbela 4th extension historical geological incidents',
        officer: 'Geotechnical Peer Cohort',
        avatar: 'GP',
      },
    ],
  },
  {
    id: 'kcr',
    project: 'Karachi Commuter Rail Elevated Viaduct',
    location: 'Sindh • Pier P-112 to P-128',
    status: 'Active Inspection',
    sources: [
      { name: 'InSAR Satellite', icon: '🛰️', count: 'Zero tilt deviation', active: true },
      { name: 'IFMS Drawdown', icon: '💼', count: 'Tranche 3B Validated', active: true },
      { name: 'Drone 3D Mesh', icon: '🛸', count: 'Pre-cast beam seating', active: true },
      { name: 'Concrete Maturity', icon: '🌡️', count: '28-day cure 42 MPa', active: true },
      { name: 'Urban Transit Cohort', icon: '🚆', count: '91.4% Peer Pace', active: false },
    ],
    rows: [
      {
        type: 'Topic',
        pillColor: { bg: '#FFE4E6', text: '#E11D48' },
        title: 'Pre-stressed girder placement milestone verification',
        subtext: 'Lidar point cloud confirms pier cap bearing alignment matches millimeter CAD specifications',
        officer: 'Structural Inspectorate',
        avatar: 'SI',
      },
      {
        type: 'Action',
        pillColor: { bg: '#E0F2FE', text: '#0284C7' },
        title: 'Disbursement authorization cleared for Superstructure Lot 4',
        subtext: 'Financial milestone matched 100% against verified physical asset installation',
        officer: 'Sindh Transit Authority',
        avatar: 'ST',
      },
      {
        type: 'Decisions',
        pillColor: { bg: '#DCFCE7', text: '#16A34A' },
        title: '"Approved zero-defect tranche disbursement of $8.9M"',
        subtext: 'All quality certificates cryptographically verified and committed to state audit ledger',
        officer: 'Minister of Transport',
        avatar: 'MT',
      },
    ],
  },
];

export const FinalCtaSection: React.FC<FinalCtaSectionProps> = ({ onEnterApp }) => {
  const [selectedCaseId, setSelectedCaseId] = useState<string>('n25');
  const [activeSourceIndex, setActiveSourceIndex] = useState<number>(0);

  const activeCase = CASES.find((c) => c.id === selectedCaseId) || CASES[0];

  return (
    <section className="el-section" style={{ background: 'transparent', paddingBottom: '40px', paddingTop: '30px' }}>
      <div className="el-container" style={{ width: '100%', maxWidth: '1240px', margin: '0 auto', boxSizing: 'border-box' }}>
        {/* Large Soft Radiant Apricot/Peach Region */}
        <div
          className="reveal-on-scroll is-revealed"
          style={{
            background: 'linear-gradient(180deg, rgba(255, 240, 230, 0.96) 0%, rgba(255, 233, 220, 0.93) 100%)',
            backdropFilter: 'blur(20px)',
            WebkitBackdropFilter: 'blur(20px)',
            borderRadius: 'clamp(20px, 4vw, 36px)',
            border: '1px solid rgba(252, 212, 190, 0.85)',
            padding: 'clamp(36px, 5vw, 68px) clamp(16px, 3.5vw, 32px)',
            textAlign: 'center',
            position: 'relative',
            overflow: 'hidden',
            boxShadow: '0 30px 80px -15px rgba(234, 88, 12, 0.16), 0 2px 10px rgba(0, 0, 0, 0.03)',
            boxSizing: 'border-box',
            width: '100%',
          }}
        >
          {/* Radiant ambient blurred glow behind typography */}
          <div
            className="el-ambient-field-blur"
            style={{
              top: '25%',
              left: '50%',
              width: '550px',
              height: '550px',
              transform: 'translate(-50%, -50%)',
              background: 'radial-gradient(circle, rgba(255, 160, 100, 0.55) 0%, rgba(254, 215, 170, 0.15) 60%, transparent 75%)',
              filter: 'blur(90px)',
            }}
          />

          <div style={{ position: 'relative', zIndex: 1, width: '100%' }}>
            {/* Eyebrow */}
            <div className="el-eyebrow" style={{ color: '#C2410C', marginBottom: '18px' }}>
              <span className="el-eyebrow-dot" style={{ backgroundColor: '#EA580C' }} />
              <span>PROACTIVE INFRASTRUCTURE GOVERNANCE</span>
            </div>

            {/* Headline */}
            <h2
              style={{
                fontSize: 'clamp(2.1rem, 4.6vw, 4.2rem)',
                fontWeight: 800,
                lineHeight: 1.04,
                letterSpacing: '-0.04em',
                color: 'var(--el-text-primary)',
                maxWidth: '860px',
                margin: '0 auto 20px auto',
              }}
            >
              KNOW WHAT CHANGED<br />
              BEFORE IT BECOMES OBVIOUS.
            </h2>

            {/* Subcopy */}
            <p
              style={{
                fontSize: 'clamp(14px, 1.4vw, 16.5px)',
                lineHeight: 1.65,
                color: 'var(--el-text-secondary)',
                maxWidth: '620px',
                margin: '0 auto 32px auto',
              }}
            >
              Empower ministers, portfolio directors, and project engineers with continuous observational telemetry, 
              peer cohort intelligence, and accountable agentic forensic investigation.
            </p>

            {/* Primary Action Buttons */}
            <div style={{ display: 'flex', justifyContent: 'center', gap: '14px', flexWrap: 'wrap', marginBottom: '28px' }}>
              <button
                className="el-btn-black"
                onClick={onEnterApp}
                style={{ padding: '14px 32px', fontSize: '14px', fontWeight: 700 }}
              >
                <span>Sign in to get started</span>
                <span style={{ fontSize: '16px' }}>→</span>
              </button>
              <button
                className="el-btn-outline"
                onClick={() => {
                  const elem = document.getElementById('how-it-works');
                  elem?.scrollIntoView({ behavior: 'smooth' });
                }}
                style={{ padding: '14px 26px', fontSize: '14px' }}
              >
                Review System Lifecycle
              </button>
            </div>

            {/* Capability Tag Pills (Fluid wrap for any screen) */}
            <div
              style={{
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center',
                gap: '8px',
                flexWrap: 'wrap',
                marginBottom: '36px',
                padding: '0 4px',
              }}
            >
              {[
                'Satellite InSAR Radar',
                'SAP ERP Milestones',
                'Peer Delay Cohorts',
                'Ministerial Decision Gating',
                'Cryptographic Audit Chain',
              ].map((chip) => (
                <div
                  key={chip}
                  style={{
                    backgroundColor: 'rgba(255, 255, 255, 0.88)',
                    backdropFilter: 'blur(8px)',
                    border: '1px solid rgba(251, 146, 60, 0.28)',
                    borderRadius: '9999px',
                    padding: '6px 14px',
                    fontSize: '12px',
                    fontWeight: 600,
                    color: '#4B5563',
                    boxShadow: '0 2px 6px rgba(234, 88, 12, 0.05)',
                  }}
                >
                  {chip}
                </div>
              ))}
            </div>

            {/* LIVE PRODUCT SHOWCASE CARD (Fluid and Responsive on ALL screen widths) */}
            <div className="el-showcase-card">
              {/* Top Case Switcher Pills Bar */}
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  flexWrap: 'wrap',
                  gap: '12px',
                  borderBottom: '1px solid #F3F4F6',
                  paddingBottom: '16px',
                  marginBottom: '20px',
                }}
              >
                {/* Case Selector Tabs */}
                <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                  {CASES.map((c) => {
                    const isSelected = c.id === selectedCaseId;
                    return (
                      <button
                        key={c.id}
                        onClick={() => setSelectedCaseId(c.id)}
                        style={{
                          backgroundColor: isSelected ? 'var(--el-text-primary)' : 'var(--bg-subtle, #F9FAFB)',
                          color: isSelected ? 'var(--bg-base-contrast, #070A12)' : 'var(--el-text-secondary)',
                          border: isSelected ? '1px solid var(--el-text-primary)' : '1px solid var(--el-border)',
                          borderRadius: '9999px',
                          padding: '6px 14px',
                          fontSize: '12px',
                          fontWeight: 600,
                          cursor: 'pointer',
                          transition: 'all 0.2s ease',
                        }}
                      >
                        {c.project.split(' ')[0]} {c.project.split(' ')[1]}
                      </button>
                    );
                  })}
                </div>

                {/* Live Status Badge */}
                <div
                  style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '8px',
                    fontSize: '12px',
                    fontWeight: 600,
                    color: '#059669',
                    backgroundColor: '#ECFDF5',
                    padding: '5px 12px',
                    borderRadius: '9999px',
                    border: '1px solid #A7F3D0',
                  }}
                >
                  <span
                    style={{
                      width: '7px',
                      height: '7px',
                      borderRadius: '50%',
                      backgroundColor: '#10B981',
                      boxShadow: '0 0 8px rgba(16, 185, 129, 0.8)',
                    }}
                  />
                  <span>{activeCase.status}</span>
                </div>
              </div>

              {/* Responsive Grid: Left Ingestion Network Topology | Right Incident Dispatch Protocol */}
              <div className="el-showcase-grid">
                {/* LEFT SIDE: Ingestion Network Topology with Curved Connectors */}
                <div
                  style={{
                    backgroundColor: '#FAFAF9',
                    borderRadius: '16px',
                    border: '1px solid #F0EFEA',
                    padding: '18px 16px',
                    position: 'relative',
                    overflow: 'hidden',
                    boxSizing: 'border-box',
                    width: '100%',
                  }}
                >
                  <div
                    style={{
                      fontSize: '11px',
                      fontWeight: 700,
                      textTransform: 'uppercase',
                      letterSpacing: '0.06em',
                      color: '#9CA3AF',
                      marginBottom: '14px',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      flexWrap: 'wrap',
                      gap: '4px',
                    }}
                  >
                    <span>Autonomous Data Streams</span>
                    <span style={{ fontSize: '10px', color: '#EA580C', fontWeight: 800 }}>• 6 Live Ingest Feeds</span>
                  </div>

                  {/* Visual Node Diagram */}
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', position: 'relative', width: '100%' }}>
                    {/* Left Source Nodes */}
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', zIndex: 2, flex: 1, minWidth: 0, maxWidth: '240px' }}>
                      {activeCase.sources.map((src, idx) => {
                        const isHovered = idx === activeSourceIndex;
                        return (
                          <div
                            key={src.name}
                            onMouseEnter={() => setActiveSourceIndex(idx)}
                            style={{
                              display: 'flex',
                              alignItems: 'center',
                              gap: '8px',
                              backgroundColor: isHovered ? '#FFFFFF' : '#F4F4F2',
                              border: isHovered ? '1px solid #F97316' : '1px solid #E5E7EB',
                              borderRadius: '8px',
                              padding: '5px 10px',
                              boxShadow: isHovered ? '0 4px 12px rgba(234, 88, 12, 0.15)' : 'none',
                              cursor: 'pointer',
                              transition: 'all 0.2s ease',
                              boxSizing: 'border-box',
                              width: '100%',
                            }}
                          >
                            <span style={{ fontSize: '13px', flexShrink: 0 }}>{src.icon}</span>
                            <div style={{ minWidth: 0, flex: 1, overflow: 'hidden' }}>
                              <div style={{ fontSize: '11px', fontWeight: 700, color: '#1F2937', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                                {src.name}
                              </div>
                              <div style={{ fontSize: '9.5px', color: '#6B7280', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                                {src.count}
                              </div>
                            </div>
                          </div>
                        );
                      })}
                    </div>

                    {/* Connecting SVG Flow Lines */}
                    <svg
                      style={{
                        position: 'absolute',
                        top: 0,
                        left: '110px',
                        width: 'calc(100% - 170px)',
                        height: '100%',
                        pointerEvents: 'none',
                        zIndex: 1,
                      }}
                      viewBox="0 0 160 260"
                      preserveAspectRatio="none"
                    >
                      <path d="M 0,22 C 80,22 90,130 160,130" fill="none" stroke="#FDBA74" strokeWidth="1.5" strokeDasharray="4 4" className="el-flowing-line" />
                      <path d="M 0,65 C 80,65 90,130 160,130" fill="none" stroke="#FDBA74" strokeWidth="1.5" strokeDasharray="4 4" className="el-flowing-line" />
                      <path d="M 0,108 C 80,108 90,130 160,130" fill="none" stroke="#FB923C" strokeWidth="2" />
                      <path d="M 0,152 C 80,152 90,130 160,130" fill="none" stroke="#FDBA74" strokeWidth="1.5" strokeDasharray="4 4" className="el-flowing-line" />
                      <path d="M 0,195 C 80,195 90,130 160,130" fill="none" stroke="#FED7AA" strokeWidth="1.5" />
                    </svg>

                    {/* Central Glowing Hub */}
                    <div style={{ zIndex: 2, display: 'flex', flexDirection: 'column', alignItems: 'center', marginLeft: '12px', flexShrink: 0 }}>
                      <div
                        style={{
                          width: '52px',
                          height: '52px',
                          borderRadius: '50%',
                          background: 'linear-gradient(135deg, #FF6B35 0%, #EA580C 100%)',
                          boxShadow: '0 0 24px rgba(234, 88, 12, 0.45)',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          color: '#FFFFFF',
                          fontWeight: 800,
                          fontSize: '14px',
                          border: '3.5px solid #FFF',
                          position: 'relative',
                        }}
                      >
                        ▲
                        <div
                          style={{
                            position: 'absolute',
                            inset: '-7px',
                            borderRadius: '50%',
                            border: '2px solid rgba(234, 88, 12, 0.35)',
                            animation: 'radarPing 2.5s infinite',
                          }}
                        />
                      </div>
                      <span style={{ fontSize: '9.5px', fontWeight: 800, color: '#EA580C', marginTop: '6px', letterSpacing: '0.04em' }}>
                        CORE ENGINE
                      </span>
                    </div>
                  </div>
                </div>

                {/* RIGHT SIDE: Structured Action & Decision Stream (Collabute style) */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', minWidth: 0, width: '100%' }}>
                  {/* Project Location Header */}
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: '2px', flexWrap: 'wrap', gap: '6px' }}>
                    <div>
                      <div style={{ fontSize: '14px', fontWeight: 800, color: '#111827' }}>
                        {activeCase.project}
                      </div>
                      <div style={{ fontSize: '11px', color: '#6B7280' }}>
                        {activeCase.location}
                      </div>
                    </div>
                    <span style={{ fontSize: '10.5px', color: '#9CA3AF', fontFamily: 'monospace' }}>
                      AUDIT ACTIVE
                    </span>
                  </div>

                  {/* Incident Dispatch Rows */}
                  {activeCase.rows.map((row, idx) => (
                    <div key={idx} className="el-showcase-row">
                      {/* Left Category Pill */}
                      <span
                        style={{
                          backgroundColor: row.pillColor.bg,
                          color: row.pillColor.text,
                          fontSize: '10.5px',
                          fontWeight: 700,
                          borderRadius: '6px',
                          padding: '3px 8px',
                          textAlign: 'center',
                          whiteSpace: 'nowrap',
                          flexShrink: 0,
                        }}
                      >
                        {row.type}
                      </span>

                      {/* Content */}
                      <div style={{ minWidth: 0, flex: 1 }}>
                        <div style={{ fontSize: '12px', fontWeight: 600, color: '#1F2937', lineHeight: 1.35 }}>
                          {row.title}
                        </div>
                        <div style={{ fontSize: '10.5px', color: '#6B7280', marginTop: '1px', lineHeight: 1.3 }}>
                          {row.subtext}
                        </div>
                      </div>

                      {/* Officer Avatar Badge */}
                      <div
                        className="el-showcase-avatar"
                        title={row.officer}
                        style={{
                          width: '26px',
                          height: '26px',
                          borderRadius: '50%',
                          backgroundColor: '#E5E7EB',
                          color: '#374151',
                          fontSize: '10px',
                          fontWeight: 700,
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          border: '1.5px solid #FFFFFF',
                          boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
                          flexShrink: 0,
                        }}
                      >
                        {row.avatar}
                      </div>
                    </div>
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
