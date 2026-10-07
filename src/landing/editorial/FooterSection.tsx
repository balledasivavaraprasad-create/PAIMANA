import React from 'react';

export const FooterSection: React.FC = () => {
  return (
    <footer style={{ background: 'rgba(255, 255, 255, 0.78)', backdropFilter: 'blur(20px)', WebkitBackdropFilter: 'blur(20px)', borderTop: '1px solid rgba(229, 227, 220, 0.8)', padding: '80px 0 48px 0', position: 'relative', zIndex: 1 }}>
      <div className="el-container">
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
          gap: '48px',
          marginBottom: '64px',
        }}>
          {/* Brand Mark Column */}
          <div style={{ gridColumn: 'span 2' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '16px' }}>
              <div style={{
                width: '22px',
                height: '22px',
                borderRadius: '6px',
                background: '#121314',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#FAF9F5',
                fontSize: '11px',
                fontWeight: 800,
              }}>
                ▲
              </div>
              <span style={{ fontSize: '16px', fontWeight: 800, letterSpacing: '-0.02em', color: '#121314' }}>
                PAIMANA 2.0 • InfraBuild-AI
              </span>
            </div>
            <p style={{ fontSize: '13px', color: '#737578', lineHeight: 1.6, maxWidth: '320px', margin: 0 }}>
              National Infrastructure Intelligence Command Center. Continuous observational telemetry, peer cohort benchmarks, and human-gated decision governance.
            </p>
          </div>

          {/* Column 1: Product */}
          <div>
            <div style={{ fontSize: '11px', fontWeight: 700, color: '#121314', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: '16px' }}>
              Product
            </div>
            <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: '10px', fontSize: '13px', color: '#737578' }}>
              <li><a href="#monitoring" style={{ color: 'inherit', textDecoration: 'none' }}>Continuous Monitoring</a></li>
              <li><a href="#peers" style={{ color: 'inherit', textDecoration: 'none' }}>Peer Intelligence</a></li>
              <li><a href="#investigation" style={{ color: 'inherit', textDecoration: 'none' }}>Agentic Investigation</a></li>
              <li><a href="#evidence" style={{ color: 'inherit', textDecoration: 'none' }}>Evidence Topology</a></li>
              <li><a href="#governance" style={{ color: 'inherit', textDecoration: 'none' }}>Human-Gated Action</a></li>
            </ul>
          </div>

          {/* Column 2: Platform */}
          <div>
            <div style={{ fontSize: '11px', fontWeight: 700, color: '#121314', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: '16px' }}>
              Platform
            </div>
            <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: '10px', fontSize: '13px', color: '#737578' }}>
              <li><a href="#analytics" style={{ color: 'inherit', textDecoration: 'none' }}>Portfolio Workstation</a></li>
              <li><a href="#outcomes" style={{ color: 'inherit', textDecoration: 'none' }}>National Telemetry</a></li>
              <li><a href="#how-it-works" style={{ color: 'inherit', textDecoration: 'none' }}>System Lifecycle</a></li>
              <li><a href="#technology" style={{ color: 'inherit', textDecoration: 'none' }}>Technical Architecture</a></li>
            </ul>
          </div>

          {/* Column 3: Resources */}
          <div>
            <div style={{ fontSize: '11px', fontWeight: 700, color: '#121314', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: '16px' }}>
              Governance
            </div>
            <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: '10px', fontSize: '13px', color: '#737578' }}>
              <li><a href="#faq" style={{ color: 'inherit', textDecoration: 'none' }}>Epistemological Rigor</a></li>
              <li><span style={{ cursor: 'default' }}>Model Cards & SHAP</span></li>
              <li><span style={{ cursor: 'default' }}>Audit Log Guarantees</span></li>
              <li><span style={{ cursor: 'default' }}>Security & RBAC</span></li>
            </ul>
          </div>

          {/* Column 4: Deployment */}
          <div>
            <div style={{ fontSize: '11px', fontWeight: 700, color: '#121314', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: '16px' }}>
              Deployment
            </div>
            <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: '10px', fontSize: '13px', color: '#737578' }}>
              <li><span style={{ cursor: 'default' }}>Ministry of Planning (CDWP/ECNEC)</span></li>
              <li><span style={{ cursor: 'default' }}>PAIMANA ERP Sync</span></li>
              <li><span style={{ cursor: 'default' }}>Provincial Line Departments</span></li>
            </ul>
          </div>
        </div>

        {/* Bottom Row */}
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          paddingTop: '32px',
          borderTop: '1px solid var(--el-border)',
          fontSize: '12px',
          color: '#9CA3AF',
          flexWrap: 'wrap',
          gap: '12px',
        }}>
          <div>© {new Date().getFullYear()} InfraBuild-AI • PAIMANA 2.0. Sovereign Infrastructure Intelligence.</div>
          <div style={{ display: 'flex', gap: '20px' }}>
            <span>Privacy Policy</span>
            <span>Terms of Service</span>
            <span>Security Assurance</span>
          </div>
        </div>
      </div>
    </footer>
  );
};
