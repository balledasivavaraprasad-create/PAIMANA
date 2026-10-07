import React, { useState } from 'react';

export const PeerIntelligenceSection: React.FC = () => {
  const [filterActive, setFilterActive] = useState(true);

  return (
    <section id="peers" className="el-section" style={{ borderTop: '1px solid var(--el-border)', background: 'transparent' }}>
      <div className="el-container">
        <div className="el-sticky-layout">
          {/* Left Text */}
          <div className="reveal-on-scroll stagger-1">
            <div className="el-eyebrow">
              <span className="el-eyebrow-dot" style={{ backgroundColor: '#0284C7' }} />
              <span>PEER COHORT INTELLIGENCE</span>
            </div>

            <h2 className="el-section-title">
              A PROJECT ISN'T<br />
              UNDERSTOOD IN<br />
              ISOLATION.
            </h2>

            <p className="el-subcopy">
              A 15% cost elevation might be macroeconomic material inflation, or it might be an isolated project failure. 
              InfraBuild-AI constructs dynamic peer cohorts based on sector, terrain, cost tier, and procurement method to establish 
              whether divergence is systemic or a severe asset-specific anomaly.
            </p>

            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginTop: '24px' }}>
              <button
                type="button"
                onClick={() => setFilterActive(!filterActive)}
                className="el-btn-black"
                style={{ fontSize: '13px', padding: '12px 22px' }}
              >
                {filterActive ? 'Show All 428 Portfolio Candidates' : 'Activate 94% Similarity Cohort (8 Peers)'}
              </button>
            </div>

            <div style={{ marginTop: '20px', fontSize: '12px', color: '#737578' }}>
              Filtered Cohort: High-speed dual-carriageway motorways, alluvial plain terrain, FIDIC EPC contracting model.
            </div>
          </div>

          {/* Right Peer Cohort Surface */}
          <div className="reveal-on-scroll stagger-2">
            <div className="el-product-card" style={{ padding: '36px' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px' }}>
                <span style={{ fontSize: '11px', fontWeight: 700, color: 'var(--el-text-muted)', textTransform: 'uppercase' }}>
                  PEER COHORT BENCHMARK MATRIX
                </span>
                <span
                  style={{
                    fontSize: '11px',
                    fontWeight: 700,
                    padding: '3px 10px',
                    borderRadius: 'var(--el-radius-pill)',
                    backgroundColor: '#FEE2E2',
                    color: '#DC2626',
                    border: '1px solid #FECACA',
                  }}
                >
                  PROJECT-SPECIFIC ANOMALY
                </span>
              </div>

              {/* Peer Scatter Grid SVG */}
              <div
                style={{
                  height: '240px',
                  backgroundColor: 'var(--bg-inset, #FAFAF7)',
                  borderRadius: 'var(--el-radius-md)',
                  position: 'relative',
                  overflow: 'hidden',
                  border: '1px solid var(--el-border)',
                }}
              >
                <svg viewBox="0 0 500 240" style={{ width: '100%', height: '100%' }}>
                  {/* Grid Lines */}
                  <line x1="40" y1="60" x2="480" y2="60" stroke="#EAE9E2" strokeDasharray="3 3" />
                  <line x1="40" y1="120" x2="480" y2="120" stroke="#EAE9E2" strokeDasharray="3 3" />
                  <line x1="40" y1="180" x2="480" y2="180" stroke="#EAE9E2" strokeDasharray="3 3" />
                  <line x1="40" y1="210" x2="480" y2="210" stroke="#D1D0C7" />

                  {/* Benchmark Band (Cohort Median) */}
                  <rect x="40" y="100" width="440" height="40" fill="#0284C7" fillOpacity="0.07" />
                  <line x1="40" y1="120" x2="480" y2="120" stroke="#0284C7" strokeWidth="1.5" strokeDasharray="4 2" />
                  <text x="50" y="115" fill="#0284C7" fontSize="10" fontWeight="700">COHORT MEDIAN (46.1 DPHIS)</text>

                  {/* Candidate peers (faded when filtered) */}
                  <circle cx="80" cy="190" r="5" fill="#9CA3AF" opacity={filterActive ? 0.15 : 0.6} />
                  <circle cx="120" cy="170" r="5" fill="#9CA3AF" opacity={filterActive ? 0.15 : 0.6} />
                  <circle cx="160" cy="200" r="6" fill="#9CA3AF" opacity={filterActive ? 0.15 : 0.6} />
                  <circle cx="210" cy="165" r="5" fill="#9CA3AF" opacity={filterActive ? 0.15 : 0.6} />
                  <circle cx="340" cy="195" r="5" fill="#9CA3AF" opacity={filterActive ? 0.15 : 0.6} />
                  <circle cx="420" cy="175" r="4" fill="#9CA3AF" opacity={filterActive ? 0.15 : 0.6} />

                  {/* High-similarity Peer Nodes */}
                  <circle cx="140" cy="125" r="7" fill="#0284C7" />
                  <text x="140" y="145" fill="var(--el-text-muted, #4B5563)" fontSize="9" textAnchor="middle">M-4 Gojra</text>

                  <circle cx="220" cy="115" r="7" fill="#0284C7" />
                  <text x="220" y="135" fill="var(--el-text-muted, #4B5563)" fontSize="9" textAnchor="middle">M-2 Sialkot</text>

                  <circle cx="310" cy="130" r="7" fill="#0284C7" />
                  <text x="310" y="150" fill="var(--el-text-muted, #4B5563)" fontSize="9" textAnchor="middle">M-11 Lahore</text>

                  <circle cx="380" cy="110" r="7" fill="#0284C7" />
                  <text x="380" y="100" fill="var(--el-text-muted, #4B5563)" fontSize="9" textAnchor="middle">M-3 Abdul Hakeem</text>

                  {/* Target Outlier Asset (Sukkur-Multan) */}
                  <circle cx="280" cy="45" r="9" fill="#DC2626" />
                  <text x="280" y="32" fill="#DC2626" fontSize="11" fontWeight="800" textAnchor="middle">
                    SUKKUR-MULTAN (72.4)
                  </text>
                  {/* Deviation Arrow */}
                  <line x1="280" y1="58" x2="280" y2="116" stroke="#DC2626" strokeWidth="1.5" strokeDasharray="3 3" />
                  <text x="290" y="90" fill="#DC2626" fontSize="10" fontWeight="700">+26.3 pts deviation</text>
                </svg>
              </div>

              {/* Bottom Cohort Details */}
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  marginTop: '20px',
                  paddingTop: '16px',
                  borderTop: '1px solid var(--el-border)',
                  fontSize: '12px',
                  color: 'var(--el-text-secondary)',
                  flexWrap: 'wrap',
                  gap: '8px',
                }}
              >
                <div>
                  Peer Baseline Cohort: <strong style={{ color: 'var(--el-text-primary)' }}>46.1 DPHIS</strong>
                </div>
                <div style={{ color: '#DC2626', fontWeight: 600 }}>
                  Project Outlier Magnitude: Severe (+2.4σ)
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};
