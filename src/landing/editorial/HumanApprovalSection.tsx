import React, { useState } from 'react';

export const HumanApprovalSection: React.FC<{ onOpenPlatform: () => void }> = ({ onOpenPlatform }) => {
  const [isAuthorized, setIsAuthorized] = useState(false);

  return (
    <section id="governance" className="el-section el-section-dark-boundary" style={{ backgroundColor: '#0A0E17', color: '#FFFFFF' }}>
      <div className="el-container">
        <div className="el-eyebrow reveal-on-scroll stagger-1" style={{ color: '#38BDF8' }}>
          <span className="el-eyebrow-dot" style={{ backgroundColor: '#38BDF8', boxShadow: '0 0 12px rgba(56, 189, 248, 0.8)' }} />
          <span style={{ color: '#38BDF8' }}>SOVEREIGN DECISION BOUNDARY</span>
        </div>

        <h2 className="el-section-title reveal-on-scroll stagger-2" style={{ color: '#FFFFFF', maxWidth: '880px', textShadow: '0 2px 20px rgba(0,0,0,0.5)' }}>
          INTELLIGENCE<br />
          WITHOUT UNACCOUNTABLE<br />
          AUTOMATION.
        </h2>

        <p className="el-subcopy reveal-on-scroll stagger-3" style={{ color: '#E2E8F0', maxWidth: '720px', fontSize: '16px', lineHeight: 1.65 }}>
          Observational surveillance and agentic evidence synthesis are continuous. But consequential civil interventions—statutory contractor default notices, escrow disbursement holds, and PC-1 revisions—remain strictly behind explicit human authorization boundaries.
        </p>

        {/* 5-Stage Approval Flow Visual Card */}
        <div
          className="reveal-on-scroll stagger-4"
          style={{
            marginTop: '56px',
            padding: '36px',
            backgroundColor: 'var(--bg-panel, #0C0C0E)',
            borderRadius: '24px',
            border: '1px solid var(--border-subtle, rgba(255, 255, 255, 0.12))',
            boxShadow: 'var(--card-shadow, 0 24px 64px rgba(0, 0, 0, 0.8))',
            display: 'flex',
            flexDirection: 'column',
            gap: '32px',
          }}
        >
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '16px' }}>
            {[
              { num: '01', title: 'Investigation', role: 'Autonomous Agent', status: 'Synthesized', color: '#38BDF8' },
              { num: '02', title: 'Recommendation', role: 'Candidate Engine', status: 'Formulated', color: '#818CF8' },
              { num: '03', title: 'Precedent Validation', role: 'Peer Cohort Check', status: 'Verified', color: '#C084FC' },
              { num: '04', title: 'Human Approval', role: 'Project Director / ECNEC', status: isAuthorized ? 'Approved by Member' : 'Sign-off Required', color: isAuthorized ? '#34D399' : '#FBBF24', isGate: true },
              { num: '05', title: 'Governed Action', role: 'Dispatch Engine', status: isAuthorized ? 'Order Dispatched' : 'Pending Gate', color: isAuthorized ? '#34D399' : '#94A3B8' },
            ].map((step, idx) => (
              <div
                key={idx}
                style={{
                  padding: '20px 18px',
                  backgroundColor: step.isGate ? (isAuthorized ? 'rgba(52, 211, 153, 0.14)' : 'rgba(245, 158, 11, 0.1)') : 'rgba(255, 255, 255, 0.03)',
                  border: step.isGate ? (isAuthorized ? '1px solid rgba(52, 211, 153, 0.6)' : '1px solid rgba(245, 158, 11, 0.4)') : '1px solid rgba(255, 255, 255, 0.08)',
                  borderRadius: '16px',
                  position: 'relative',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between',
                  minHeight: '135px',
                  transition: 'all 0.3s ease',
                }}
              >
                <div>
                  <div style={{ fontSize: '10px', color: '#64748B', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                    STAGE {step.num}
                  </div>
                  <div style={{ fontSize: '15px', fontWeight: 800, color: '#FFFFFF', margin: '4px 0' }}>
                    {step.title}
                  </div>
                  <div style={{ fontSize: '12px', color: '#94A3B8' }}>{step.role}</div>
                </div>

                <div
                  style={{
                    fontSize: '11px',
                    fontWeight: 700,
                    color: step.color,
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                    marginTop: '12px',
                    borderTop: '1px solid rgba(255, 255, 255, 0.06)',
                    paddingTop: '8px',
                  }}
                >
                  <span style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: step.color }} />
                  <span>{step.status}</span>
                </div>
              </div>
            ))}
          </div>

          {/* Interactive Decision Gateway Bar */}
          <div
            style={{
              padding: '24px 28px',
              backgroundColor: isAuthorized ? 'rgba(52, 211, 153, 0.06)' : 'rgba(255, 255, 255, 0.02)',
              borderRadius: '16px',
              border: isAuthorized ? '1px solid rgba(52, 211, 153, 0.3)' : '1px solid rgba(255, 255, 255, 0.08)',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              flexWrap: 'wrap',
              gap: '16px',
              transition: 'all 0.3s ease',
            }}
          >
            <div>
              <div style={{ fontSize: '11px', color: isAuthorized ? '#34D399' : '#38BDF8', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                {isAuthorized ? '✓ ORDER SEALED & DISPATCHED' : 'PENDING MINISTERIAL SIGN-OFF • ORDER #INT-2026-089'}
              </div>
              <div style={{ fontSize: '15px', color: '#FFFFFF', fontWeight: 700, marginTop: '2px' }}>
                M-5 Corridor • Hold Sub-Contractor Advance IPC-43 Pending Escrow Verification
              </div>
              <div style={{ fontSize: '12px', color: '#94A3B8', marginTop: '4px' }}>
                Counterfactual projection: Prevents estimated 74-day milestone delay by securing direct supplier escrow.
              </div>
            </div>

            <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
              <button
                type="button"
                onClick={() => setIsAuthorized(!isAuthorized)}
                style={{
                  padding: '10px 20px',
                  borderRadius: 'var(--el-radius-pill)',
                  backgroundColor: isAuthorized ? '#059669' : '#FFFFFF',
                  color: isAuthorized ? '#FFFFFF' : '#121314',
                  border: 'none',
                  fontSize: '12.5px',
                  fontWeight: 800,
                  cursor: 'pointer',
                  boxShadow: isAuthorized ? '0 0 16px rgba(16, 185, 129, 0.5)' : 'none',
                  transition: 'all 0.25s ease',
                }}
              >
                {isAuthorized ? '✓ Authorized (Click to Revoke)' : '✍ Authorize Order'}
              </button>

              <button
                type="button"
                onClick={onOpenPlatform}
                style={{
                  padding: '10px 20px',
                  borderRadius: 'var(--el-radius-pill)',
                  backgroundColor: 'transparent',
                  color: '#38BDF8',
                  border: '1px solid rgba(56, 189, 248, 0.4)',
                  fontSize: '12.5px',
                  fontWeight: 700,
                  cursor: 'pointer',
                  transition: 'all 0.2s ease',
                }}
              >
                Open Audit Trail →
              </button>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};
