import React from 'react';

export const OutcomesSection: React.FC = () => {
  return (
    <section id="outcomes" className="el-section" style={{ background: 'transparent', borderTop: '1px solid var(--el-border)' }}>
      <div className="el-container">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', flexWrap: 'wrap', gap: '24px', marginBottom: '80px' }}>
          <div>
            <div className="el-eyebrow reveal-on-scroll stagger-1">
              <span className="el-eyebrow-dot" />
              <span>PORTFOLIO REACH & TELEMETRY</span>
            </div>
            <h2 className="el-section-title reveal-on-scroll stagger-2" style={{ maxWidth: '720px', marginBottom: 0 }}>
              PRECISION AT NATIONAL SCALE.
            </h2>
          </div>
          <div className="reveal-on-scroll stagger-3" style={{ fontSize: '11px', color: '#88898C', letterSpacing: '0.06em', textTransform: 'uppercase', fontWeight: 600 }}>
            Live National Portfolio Telemetry
          </div>
        </div>

        {/* Editorial Metrics Grid - Spacious, Large Typography, Small Labels */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
            gap: '48px',
            position: 'relative',
          }}
        >
          {/* Item 1 */}
          <div className="reveal-on-scroll stagger-1" style={{ position: 'relative' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '16px' }}>
              <div style={{ width: '6px', height: '6px', borderRadius: '50%', background: 'var(--el-text-primary, #121314)' }} />
              <div style={{ width: '40px', height: '1px', background: 'var(--border-subtle, #D6D5CF)' }} />
              <span style={{ fontSize: '11px', fontWeight: 700, color: 'var(--text-muted, #737578)', letterSpacing: '0.06em', textTransform: 'uppercase' }}>
                Assets Monitored
              </span>
            </div>
            <div style={{ fontSize: '72px', fontWeight: 800, color: 'var(--el-text-primary, #121314)', letterSpacing: '-0.04em', lineHeight: 1.0, marginBottom: '14px', fontVariantNumeric: 'tabular-nums' }}>
              428
            </div>
            <p style={{ fontSize: '13px', color: 'var(--text-muted, #737578)', lineHeight: 1.55, margin: 0, maxWidth: '240px' }}>
              High-value civil capital assets continuously ingested across transportation, energy, and water infrastructure.
            </p>
          </div>

          {/* Item 2 */}
          <div className="reveal-on-scroll stagger-2" style={{ position: 'relative' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '16px' }}>
              <div style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#0284C7' }} />
              <div style={{ width: '40px', height: '1px', background: 'var(--border-subtle, #D6D5CF)' }} />
              <span style={{ fontSize: '11px', fontWeight: 700, color: 'var(--text-muted, #737578)', letterSpacing: '0.06em', textTransform: 'uppercase' }}>
                Signals Detected
              </span>
            </div>
            <div style={{ fontSize: '72px', fontWeight: 800, color: 'var(--el-text-primary, #121314)', letterSpacing: '-0.04em', lineHeight: 1.0, marginBottom: '14px', fontVariantNumeric: 'tabular-nums' }}>
              1,420
            </div>
            <p style={{ fontSize: '13px', color: 'var(--text-muted, #737578)', lineHeight: 1.55, margin: 0, maxWidth: '240px' }}>
              Early velocity shifts, schedule slippages, and financial-physical draw mismatches caught before public escalation.
            </p>
          </div>

          {/* Item 3 */}
          <div className="reveal-on-scroll stagger-3" style={{ position: 'relative' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '16px' }}>
              <div style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#7C3AED' }} />
              <div style={{ width: '40px', height: '1px', background: 'var(--border-subtle, #D6D5CF)' }} />
              <span style={{ fontSize: '11px', fontWeight: 700, color: 'var(--text-muted, #737578)', letterSpacing: '0.06em', textTransform: 'uppercase' }}>
                Investigations
              </span>
            </div>
            <div style={{ fontSize: '72px', fontWeight: 800, color: 'var(--el-text-primary, #121314)', letterSpacing: '-0.04em', lineHeight: 1.0, marginBottom: '14px', fontVariantNumeric: 'tabular-nums' }}>
              186
            </div>
            <p style={{ fontSize: '13px', color: 'var(--text-muted, #737578)', lineHeight: 1.55, margin: 0, maxWidth: '240px' }}>
              Rigorous multi-source forensic investigations synthesized with peer cohort baselines and verified evidence trails.
            </p>
          </div>

          {/* Item 4 */}
          <div className="reveal-on-scroll stagger-4" style={{ position: 'relative' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '16px' }}>
              <div style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#059669' }} />
              <div style={{ width: '40px', height: '1px', background: 'var(--border-subtle, #D6D5CF)' }} />
              <span style={{ fontSize: '11px', fontWeight: 700, color: 'var(--text-muted, #737578)', letterSpacing: '0.06em', textTransform: 'uppercase' }}>
                Decisions Governed
              </span>
            </div>
            <div style={{ fontSize: '72px', fontWeight: 800, color: 'var(--el-text-primary, #121314)', letterSpacing: '-0.04em', lineHeight: 1.0, marginBottom: '14px', fontVariantNumeric: 'tabular-nums' }}>
              94
            </div>
            <p style={{ fontSize: '13px', color: 'var(--text-muted, #737578)', lineHeight: 1.55, margin: 0, maxWidth: '240px' }}>
              Human-approved executive interventions executed with documented audit trails and post-remedy validation tracking.
            </p>
          </div>
        </div>

        {/* Minimal dot-line architectural decoration */}
        <div className="reveal-on-scroll" style={{ marginTop: '80px', paddingTop: '32px', borderTop: '1px dashed var(--border-subtle, #E2E1DA)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', color: 'var(--text-muted, #88898C)', fontSize: '12px' }}>
          <span>Continuous telemetry synchronized across federal and provincial line departments</span>
          <div style={{ display: 'flex', gap: '8px' }}>
            <span style={{ width: '5px', height: '5px', borderRadius: '50%', background: '#A1A1AA' }} />
            <span style={{ width: '5px', height: '5px', borderRadius: '50%', background: '#A1A1AA' }} />
            <span style={{ width: '5px', height: '5px', borderRadius: '50%', background: '#A1A1AA' }} />
          </div>
        </div>
      </div>
    </section>
  );
};
