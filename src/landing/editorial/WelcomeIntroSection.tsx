import React, { useEffect, useRef } from 'react';

interface WelcomeIntroSectionProps {
  onSignIn: () => void;
  onExploreLanding: () => void;
}

export const WelcomeIntroSection: React.FC<WelcomeIntroSectionProps> = ({
  onSignIn,
  onExploreLanding,
}) => {
  const sectionRef = useRef<HTMLElement>(null);

  // Seamless scroll-down detection:
  // When user is near the top and scrolls down, smoothly glide into the landing page
  useEffect(() => {
    let isTransitioning = false;

    const handleWheel = (e: WheelEvent) => {
      if (isTransitioning) return;
      if (window.scrollY < 80 && e.deltaY > 25) {
        isTransitioning = true;
        onExploreLanding();
        setTimeout(() => {
          isTransitioning = false;
        }, 1000);
      }
    };

    const handleKeyDown = (e: KeyboardEvent) => {
      if (isTransitioning) return;
      if (window.scrollY < 80 && (e.key === 'ArrowDown' || e.key === 'PageDown' || e.key === ' ')) {
        if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return;
        isTransitioning = true;
        e.preventDefault();
        onExploreLanding();
        setTimeout(() => {
          isTransitioning = false;
        }, 1000);
      }
    };

    window.addEventListener('wheel', handleWheel, { passive: true });
    window.addEventListener('keydown', handleKeyDown);

    return () => {
      window.removeEventListener('wheel', handleWheel);
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [onExploreLanding]);

  return (
    <section
      id="welcome-intro"
      ref={sectionRef}
      style={{
        minHeight: '100vh',
        width: '100%',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        alignItems: 'center',
        position: 'relative',
        boxSizing: 'border-box',
        padding: '130px 24px 60px 24px',
        textAlign: 'center',
        overflow: 'hidden',
      }}
    >
      {/* Cinematic Content Wrapper with Staggered Kinetic Entrance */}
      <div
        style={{
          maxWidth: '960px',
          width: '100%',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          position: 'relative',
          zIndex: 2,
        }}
      >
        {/* 1. Pulsing Sovereign Radar Beacon & Emblem */}
        <div
          className="welcome-anim-beacon"
          style={{
            position: 'relative',
            width: '84px',
            height: '84px',
            marginBottom: '28px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          {/* Animated Concentric Radar Ping Waves */}
          <div
            className="welcome-radar-ping wave-1"
            style={{
              position: 'absolute',
              inset: '-18px',
              borderRadius: '50%',
              border: '1.5px solid rgba(99, 102, 241, 0.45)',
              pointerEvents: 'none',
            }}
          />
          <div
            className="welcome-radar-ping wave-2"
            style={{
              position: 'absolute',
              inset: '-36px',
              borderRadius: '50%',
              border: '1px solid rgba(56, 189, 248, 0.35)',
              pointerEvents: 'none',
            }}
          />

          {/* Central Emblem Surface */}
          <div
            style={{
              width: '56px',
              height: '56px',
              borderRadius: '16px',
              background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.92) 0%, rgba(6, 182, 212, 0.90) 100%)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 12px 36px -6px rgba(99, 102, 241, 0.55), 0 0 24px rgba(6, 182, 212, 0.35)',
              border: '1px solid rgba(255, 255, 255, 0.4)',
              transform: 'rotate(45deg)',
              transition: 'transform 0.4s cubic-bezier(0.16, 1, 0.3, 1)',
            }}
          >
            <div style={{ transform: 'rotate(-45deg)', color: '#FFFFFF', fontSize: '22px', fontWeight: 800 }}>
              ▲
            </div>
          </div>
        </div>

        {/* 2. Live Status Protocol Eyebrow Badge */}
        <div
          className="welcome-anim-eyebrow"
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '10px',
            padding: '7px 18px',
            borderRadius: '9999px',
            backgroundColor: 'rgba(255, 255, 255, 0.08)',
            border: '1px solid var(--el-border)',
            backdropFilter: 'blur(16px)',
            WebkitBackdropFilter: 'blur(16px)',
            marginBottom: '26px',
            boxShadow: '0 8px 24px -4px rgba(0, 0, 0, 0.25)',
          }}
        >
          <span
            style={{
              width: '8px',
              height: '8px',
              borderRadius: '50%',
              backgroundColor: '#10B981',
              boxShadow: '0 0 12px #10B981, 0 0 20px rgba(16, 185, 129, 0.7)',
              animation: 'welcomePulseDot 2s infinite ease-in-out',
            }}
          />
          <span
            style={{
              fontSize: '11.5px',
              fontWeight: 800,
              letterSpacing: '0.08em',
              textTransform: 'uppercase',
              color: 'var(--el-text-primary)',
            }}
          >
            SOVEREIGN TELEMETRY GATEWAY • AUTONOMOUS INFRASTRUCTURE COMMAND
          </span>
        </div>

        {/* 3. The Grand Welcome Headline */}
        <h1
          className="welcome-anim-title"
          style={{
            fontFamily: 'var(--el-font-sans, "Plus Jakarta Sans", sans-serif)',
            fontSize: 'clamp(2.75rem, 6.4vw, 5.5rem)',
            fontWeight: 800,
            lineHeight: 1.02,
            letterSpacing: '-0.04em',
            margin: '0 0 22px 0',
            color: 'var(--el-text-primary)',
          }}
        >
          Welcome to{' '}
          <span
            className="welcome-gradient-text"
            style={{
              display: 'inline-block',
              background: 'linear-gradient(135deg, var(--el-text-primary) 20%, #818CF8 60%, #38BDF8 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
            }}
          >
            InfraBuild AI
          </span>
        </h1>

        {/* 4. Subheadline & Value Proposition */}
        <p
          className="welcome-anim-subcopy"
          style={{
            fontFamily: 'var(--el-font-sans, "Plus Jakarta Sans", sans-serif)',
            fontSize: 'clamp(1.05rem, 1.35vw, 1.25rem)',
            lineHeight: 1.6,
            color: 'var(--el-text-secondary)',
            maxWidth: '720px',
            margin: '0 0 36px 0',
          }}
        >
          Continuous national infrastructure intelligence, predictive risk surveillance, and automated forensic cross-auditing — protecting capital delivery across 428 national corridors before minor deviations become public crises.
        </p>

        {/* 5. Live Telemetry Metric Strip (Interactive Miniature Flashcards) */}
        <div
          className="welcome-anim-metrics"
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
            gap: '14px',
            width: '100%',
            maxWidth: '820px',
            marginBottom: '40px',
          }}
        >
          <div
            className="welcome-metric-card"
            style={{
              backgroundColor: 'var(--bg-panel, rgba(12, 12, 14, 0.92))',
              border: '1px solid var(--el-border)',
              borderRadius: '16px',
              padding: '16px 18px',
              backdropFilter: 'blur(20px)',
              WebkitBackdropFilter: 'blur(20px)',
              textAlign: 'center',
              boxShadow: '0 12px 30px -8px rgba(0, 0, 0, 0.35)',
              transition: 'all 0.3s cubic-bezier(0.16, 1, 0.3, 1)',
            }}
          >
            <div style={{ fontSize: '26px', fontWeight: 800, color: 'var(--el-text-primary)', letterSpacing: '-0.02em' }}>
              428
            </div>
            <div style={{ fontSize: '11px', fontWeight: 700, color: 'var(--el-text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em', marginTop: '4px' }}>
              Corridors Monitored
            </div>
          </div>

          <div
            className="welcome-metric-card"
            style={{
              backgroundColor: 'var(--bg-panel, rgba(12, 12, 14, 0.92))',
              border: '1px solid var(--el-border)',
              borderRadius: '16px',
              padding: '16px 18px',
              backdropFilter: 'blur(20px)',
              WebkitBackdropFilter: 'blur(20px)',
              textAlign: 'center',
              boxShadow: '0 12px 30px -8px rgba(0, 0, 0, 0.35)',
              transition: 'all 0.3s cubic-bezier(0.16, 1, 0.3, 1)',
            }}
          >
            <div style={{ fontSize: '26px', fontWeight: 800, color: '#34D399', letterSpacing: '-0.02em' }}>
              14.8%
            </div>
            <div style={{ fontSize: '11px', fontWeight: 700, color: 'var(--el-text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em', marginTop: '4px' }}>
              Early Drift Detection
            </div>
          </div>

          <div
            className="welcome-metric-card"
            style={{
              backgroundColor: 'var(--bg-panel, rgba(12, 12, 14, 0.92))',
              border: '1px solid var(--el-border)',
              borderRadius: '16px',
              padding: '16px 18px',
              backdropFilter: 'blur(20px)',
              WebkitBackdropFilter: 'blur(20px)',
              textAlign: 'center',
              boxShadow: '0 12px 30px -8px rgba(0, 0, 0, 0.35)',
              transition: 'all 0.3s cubic-bezier(0.16, 1, 0.3, 1)',
            }}
          >
            <div style={{ fontSize: '26px', fontWeight: 800, color: 'var(--el-text-primary)', letterSpacing: '-0.02em' }}>
              28
            </div>
            <div style={{ fontSize: '11px', fontWeight: 700, color: 'var(--el-text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em', marginTop: '4px' }}>
              Peer Cohort Clusters
            </div>
          </div>

          <div
            className="welcome-metric-card"
            style={{
              backgroundColor: 'var(--bg-panel, rgba(12, 12, 14, 0.92))',
              border: '1px solid var(--el-border)',
              borderRadius: '16px',
              padding: '16px 18px',
              backdropFilter: 'blur(20px)',
              WebkitBackdropFilter: 'blur(20px)',
              textAlign: 'center',
              boxShadow: '0 12px 30px -8px rgba(0, 0, 0, 0.35)',
              transition: 'all 0.3s cubic-bezier(0.16, 1, 0.3, 1)',
            }}
          >
            <div style={{ fontSize: '26px', fontWeight: 800, color: '#38BDF8', letterSpacing: '-0.02em' }}>
              0
            </div>
            <div style={{ fontSize: '11px', fontWeight: 700, color: 'var(--el-text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em', marginTop: '4px' }}>
              Unaccountable Actions
            </div>
          </div>
        </div>

        {/* 6. Primary Action CTAs */}
        <div
          className="welcome-anim-actions"
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '16px',
            flexWrap: 'wrap',
            justifyContent: 'center',
            marginBottom: '48px',
          }}
        >
          {/* Primary "Sign in to get started" CTA */}
          <button
            type="button"
            onClick={onSignIn}
            className="el-btn-black welcome-btn-get-started"
            style={{
              padding: '15px 34px',
              fontSize: '15px',
              fontWeight: 700,
              borderRadius: '9999px',
              display: 'inline-flex',
              alignItems: 'center',
              gap: '10px',
              cursor: 'pointer',
              border: '1px solid var(--el-text-primary)',
              boxShadow: '0 12px 36px -4px rgba(0, 0, 0, 0.35)',
              transition: 'all 0.25s cubic-bezier(0.16, 1, 0.3, 1)',
            }}
          >
            <span>Sign in to get started</span>
            <span
              className="welcome-btn-arrow"
              style={{
                fontSize: '16px',
                display: 'inline-block',
                transition: 'transform 0.25s ease',
              }}
            >
              →
            </span>
          </button>

          {/* Secondary "Explore Portfolio Film" CTA */}
          <button
            type="button"
            onClick={onExploreLanding}
            className="el-btn-outline"
            style={{
              padding: '15px 30px',
              fontSize: '15px',
              fontWeight: 600,
              borderRadius: '9999px',
              display: 'inline-flex',
              alignItems: 'center',
              gap: '8px',
              cursor: 'pointer',
              backdropFilter: 'blur(16px)',
              WebkitBackdropFilter: 'blur(16px)',
            }}
          >
            <span>Explore Portfolio Film</span>
            <span style={{ fontSize: '15px' }}>↓</span>
          </button>
        </div>

        {/* 7. Animated Scroll-Down Exploration Cue */}
        <div
          className="welcome-anim-scrollcue"
          onClick={onExploreLanding}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => {
            if (e.key === 'Enter' || e.key === ' ') {
              e.preventDefault();
              onExploreLanding();
            }
          }}
          style={{
            display: 'inline-flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: '8px',
            cursor: 'pointer',
            opacity: 0.85,
            transition: 'opacity 0.2s ease',
          }}
        >
          <span
            style={{
              fontSize: '11px',
              fontWeight: 700,
              letterSpacing: '0.12em',
              textTransform: 'uppercase',
              color: 'var(--el-text-muted)',
            }}
          >
            Scroll to Explore
          </span>
          <div
            className="welcome-mouse-indicator"
            style={{
              width: '22px',
              height: '34px',
              borderRadius: '12px',
              border: '1.5px solid var(--el-border)',
              display: 'flex',
              justifyContent: 'center',
              paddingTop: '6px',
              boxSizing: 'border-box',
            }}
          >
            <div
              className="welcome-mouse-wheel"
              style={{
                width: '3.5px',
                height: '7px',
                borderRadius: '9999px',
                backgroundColor: 'var(--el-text-primary)',
              }}
            />
          </div>
        </div>
      </div>
    </section>
  );
};
