import React from 'react';

export const EvidenceSection: React.FC = () => {
  return (
    <section id="evidence" className="el-section" style={{ borderTop: '1px solid var(--el-border)', background: 'transparent' }}>
      <div className="el-container">
        <div className="el-eyebrow reveal-on-scroll stagger-1">
          <span className="el-eyebrow-dot" style={{ backgroundColor: '#059669' }} />
          <span>EPISTEMOLOGICAL RIGOR & TRUST</span>
        </div>

        <h2 className="el-section-title reveal-on-scroll stagger-2" style={{ maxWidth: '900px' }}>
          KNOW WHAT IS OBSERVED.<br />
          KNOW WHAT IS INFERRED.
        </h2>

        <p className="el-subcopy reveal-on-scroll stagger-3" style={{ maxWidth: '720px' }}>
          Decision integrity in public infrastructure demands radical transparency. InfraBuild-AI enforces 
          a strict architectural separation between verified ground facts, machine learning model projections, 
          agentic causal hypotheses, and remaining uncertainties.
        </p>

        {/* 4 Categorized Evidence Pillars */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '20px', marginTop: '56px' }}>
          {/* Card 1: OBSERVED */}
          <div
            className="reveal-on-scroll stagger-1"
            style={{
              padding: '32px 28px',
              backgroundColor: 'var(--bg-panel, #FFFFFF)',
              border: '1px solid var(--border-subtle, var(--el-border))',
              borderRadius: '20px',
              boxShadow: 'var(--card-shadow, 0 8px 24px rgba(0,0,0,0.02))',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
              minHeight: '260px',
            }}
          >
            <div>
              <div style={{ fontSize: '11px', fontWeight: 800, color: 'var(--text-primary, #0284C7)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '14px' }}>
                01 • OBSERVED FACT
              </div>
              <p style={{ margin: '0 0 14px 0', fontSize: '16px', fontWeight: 600, color: 'var(--el-text-primary)', lineHeight: 1.45 }}>
                IPC financial expenditure is ahead of physical milestone completion by 16.7%.
              </p>
            </div>
            <div style={{ fontSize: '12px', color: 'var(--text-muted, #737578)', borderTop: '1px dashed var(--border-subtle, #E5E3DC)', paddingTop: '12px' }}>
              Source: PAIMANA ERP Verified Ledger & Resident Engineer Site Invoices (Oct 2026).
            </div>
          </div>

          {/* Card 2: MODEL */}
          <div
            className="reveal-on-scroll stagger-2"
            style={{
              padding: '32px 28px',
              backgroundColor: 'var(--bg-panel, #FFFFFF)',
              border: '1px solid var(--border-subtle, var(--el-border))',
              borderRadius: '20px',
              boxShadow: 'var(--card-shadow, 0 8px 24px rgba(0,0,0,0.02))',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
              minHeight: '260px',
            }}
          >
            <div>
              <div style={{ fontSize: '11px', fontWeight: 800, color: 'var(--text-primary, #7C3AED)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '14px' }}>
                02 • MODEL INFERENCE
              </div>
              <p style={{ margin: '0 0 14px 0', fontSize: '16px', fontWeight: 600, color: 'var(--el-text-primary)', lineHeight: 1.45 }}>
                DPHIS risk score elevated to 72.4; predicted milestone delay of 184 days without intervention.
              </p>
            </div>
            <div style={{ fontSize: '12px', color: 'var(--text-muted, #737578)', borderTop: '1px dashed var(--border-subtle, #E5E3DC)', paddingTop: '12px' }}>
              Source: XGBoost Non-Linear Hazard Model calibrated on 400+ historical highway projects.
            </div>
          </div>

          {/* Card 3: HYPOTHESIS */}
          <div
            className="reveal-on-scroll stagger-3"
            style={{
              padding: '32px 28px',
              backgroundColor: 'var(--bg-panel, #FFFFFF)',
              border: '1px solid var(--border-subtle, var(--el-border))',
              borderRadius: '20px',
              boxShadow: 'var(--card-shadow, 0 8px 24px rgba(0,0,0,0.02))',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
              minHeight: '260px',
            }}
          >
            <div>
              <div style={{ fontSize: '11px', fontWeight: 800, color: 'var(--text-primary, #D97706)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '14px' }}>
                03 • EVIDENCE HYPOTHESIS
              </div>
              <p style={{ margin: '0 0 14px 0', fontSize: '16px', fontWeight: 600, color: 'var(--el-text-primary)', lineHeight: 1.45 }}>
                Subcontractor liquidity crunch is driving advance drawdown while physical erection remains stalled.
              </p>
            </div>
            <div style={{ fontSize: '12px', color: 'var(--text-muted, #737578)', borderTop: '1px dashed var(--border-subtle, #E5E3DC)', paddingTop: '12px' }}>
              Source: Cross-correlation engine cross-referencing vendor sub-ledgers and steel delivery weighbridge logs; not evidence of causation.
            </div>
          </div>

          {/* Card 4: UNCERTAINTY */}
          <div
            className="reveal-on-scroll stagger-4"
            style={{
              padding: '32px 28px',
              backgroundColor: 'var(--bg-panel, #FFFFFF)',
              border: '1px solid var(--border-subtle, var(--el-border))',
              borderRadius: '20px',
              boxShadow: 'var(--card-shadow, 0 8px 24px rgba(0,0,0,0.02))',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
              minHeight: '260px',
            }}
          >
            <div>
              <div style={{ fontSize: '11px', fontWeight: 800, color: 'var(--text-primary, #DC2626)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '14px' }}>
                04 • RESIDUAL UNCERTAINTY
              </div>
              <p style={{ margin: '0 0 14px 0', fontSize: '16px', fontWeight: 600, color: 'var(--el-text-primary)', lineHeight: 1.45 }}>
                Subcontractor balance sheet details pending; requires third-party forensic audit before penalty enforcement.
              </p>
            </div>
            <div style={{ fontSize: '12px', color: 'var(--text-muted, #737578)', borderTop: '1px dashed var(--border-subtle, #E5E3DC)', paddingTop: '12px' }}>
              Action Required: Independent financial verification before cabinet notification.
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};
