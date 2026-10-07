import React, { useEffect, useRef } from 'react';

/**
 * InteractiveLivingBackground — Steady Radiant Orange Hue Atmosphere
 * 
 * - Stable, radiant orange/apricot aura matching the user's reference image
 * - Balanced 15% reduced hue intensity for an elegant, premium, fabulous finish
 * - Smooth gentle ambient drift and real-time interactive cursor parallax
 * - Color remains pure steady warm orange/apricot without color-cycling hue rotation
 * - Consistent across both public landing page and authenticated dashboard
 */
export const InteractiveLivingBackground: React.FC<{ isDark?: boolean }> = ({ isDark }) => {
  const rootRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const targetOffset = useRef({ x: 0, y: 0 });
  const currentOffset = useRef({ x: 0, y: 0 });
  const animFrameId = useRef<number | null>(null);

  // Dynamic theme tracking if not explicitly passed
  const [themeDark, setThemeDark] = React.useState<boolean>(() => {
    if (typeof isDark === 'boolean') return isDark;
    if (typeof document !== 'undefined') {
      return document.documentElement.getAttribute('data-theme') === 'dark';
    }
    return true;
  });

  useEffect(() => {
    if (typeof isDark === 'boolean') {
      setThemeDark(isDark);
      return;
    }

    const checkTheme = () => {
      const mode = document.documentElement.getAttribute('data-theme');
      setThemeDark(mode === 'dark');
    };

    checkTheme();
    const observer = new MutationObserver(checkTheme);
    observer.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });
    return () => observer.disconnect();
  }, [isDark]);

  const activeDark = typeof isDark === 'boolean' ? isDark : themeDark;

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      // Normalize to -1 to +1 from screen center
      const nx = (e.clientX / window.innerWidth - 0.5) * 2;
      const ny = (e.clientY / window.innerHeight - 0.5) * 2;
      targetOffset.current = { x: nx * 40, y: ny * 25 };

      if (rootRef.current) {
        rootRef.current.style.setProperty('--mouse-x', `${e.clientX}px`);
        rootRef.current.style.setProperty('--mouse-y', `${e.clientY}px`);
      }
    };

    const animateParallax = () => {
      currentOffset.current.x += (targetOffset.current.x - currentOffset.current.x) * 0.05;
      currentOffset.current.y += (targetOffset.current.y - currentOffset.current.y) * 0.05;

      if (containerRef.current) {
        containerRef.current.style.transform = `translate3d(${currentOffset.current.x}px, ${currentOffset.current.y}px, 0)`;
      }

      animFrameId.current = requestAnimationFrame(animateParallax);
    };

    window.addEventListener('mousemove', handleMouseMove, { passive: true });
    animFrameId.current = requestAnimationFrame(animateParallax);

    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      if (animFrameId.current) cancelAnimationFrame(animFrameId.current);
    };
  }, []);

  return (
    <div
      ref={rootRef}
      aria-hidden="true"
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        width: '100vw',
        height: '100vh',
        pointerEvents: 'none',
        zIndex: 0,
        overflow: 'hidden',
        contain: 'strict',
        backgroundColor: activeDark ? '#07090E' : '#FAF7F2',
      }}
    >
      {/* Living Atmospheric Container: Living Multi-Spectral Aurora in Dark Mode, Radiant Warmth in Light Mode */}
      <div
        ref={containerRef}
        style={{
          position: 'absolute',
          inset: '-20%',
          width: '140%',
          height: '140%',
          willChange: 'transform',
          opacity: activeDark ? 0.95 : 0.85,
        }}
      >
        {/* ORB 1: Left Atmosphere (Electric Indigo & Cobalt Stream in Dark Mode / Solar Warmth in Light Mode) */}
        <div
          style={{
            position: 'absolute',
            top: '2%',
            left: '-8%',
            width: '74vw',
            height: '88vh',
            borderRadius: '50%',
            background: activeDark
              ? 'radial-gradient(circle at 40% 40%, rgba(99, 102, 241, 0.28) 0%, rgba(59, 130, 246, 0.18) 35%, rgba(14, 165, 233, 0.08) 60%, transparent 75%)'
              : 'radial-gradient(circle at 40% 40%, rgba(255, 130, 50, 0.66) 0%, rgba(255, 165, 95, 0.46) 32%, rgba(254, 215, 175, 0.24) 60%, transparent 76%)',
            filter: activeDark ? 'blur(80px)' : 'blur(80px)',
            animation: 'gentleOrbFloatLeft 14s ease-in-out infinite alternate',
            transformOrigin: 'center center',
          }}
        />

        {/* ORB 2: Right Atmosphere (Emerald Telemetry Pulse & Cyan Wave in Dark Mode / Apricot Warmth in Light Mode) */}
        <div
          style={{
            position: 'absolute',
            top: '8%',
            right: '-10%',
            width: '78vw',
            height: '92vh',
            borderRadius: '50%',
            background: activeDark
              ? 'radial-gradient(circle at 50% 50%, rgba(16, 185, 129, 0.24) 0%, rgba(6, 182, 212, 0.16) 38%, rgba(59, 130, 246, 0.06) 65%, transparent 76%)'
              : 'radial-gradient(circle at 50% 50%, rgba(255, 150, 75, 0.62) 0%, rgba(255, 190, 125, 0.44) 36%, rgba(253, 210, 165, 0.22) 62%, transparent 76%)',
            filter: activeDark ? 'blur(85px)' : 'blur(85px)',
            animation: 'gentleOrbFloatRight 16s ease-in-out infinite alternate',
            transformOrigin: 'center center',
          }}
        />

        {/* ORB 3: Lower Horizon Atmosphere (Cosmic Violet & Rose Dusk in Dark Mode / Golden Dusk in Light Mode) */}
        <div
          style={{
            position: 'absolute',
            bottom: '2%',
            left: '10%',
            width: '85vw',
            height: '75vh',
            borderRadius: '50%',
            background: activeDark
              ? 'radial-gradient(ellipse at 50% 80%, rgba(139, 92, 246, 0.22) 0%, rgba(217, 70, 239, 0.12) 40%, rgba(79, 70, 229, 0.05) 68%, transparent 76%)'
              : 'radial-gradient(ellipse at 50% 80%, rgba(255, 140, 65, 0.55) 0%, rgba(255, 180, 120, 0.38) 38%, rgba(254, 220, 185, 0.18) 64%, transparent 76%)',
            filter: activeDark ? 'blur(90px)' : 'blur(90px)',
            animation: 'gentleOrbFloatBottom 18s ease-in-out infinite alternate',
            transformOrigin: 'center center',
          }}
        />
      </div>

      {/* Sovereign Telemetry Coordinate Grid in Dark Mode */}
      {activeDark && (
        <div
          style={{
            position: 'absolute',
            inset: 0,
            backgroundImage: `
              linear-gradient(rgba(255, 255, 255, 0.035) 1px, transparent 1px),
              linear-gradient(90deg, rgba(255, 255, 255, 0.035) 1px, transparent 1px)
            `,
            backgroundSize: '56px 56px',
            maskImage: 'radial-gradient(ellipse at 50% 45%, black 35%, transparent 80%)',
            WebkitMaskImage: 'radial-gradient(ellipse at 50% 45%, black 35%, transparent 80%)',
            opacity: 0.75,
            pointerEvents: 'none',
          }}
        />
      )}

      {/* Interactive Cursor Spotlight Beam in Dark Mode */}
      {activeDark && (
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background: 'radial-gradient(600px circle at var(--mouse-x, 50vw) var(--mouse-y, 35vh), rgba(99, 102, 241, 0.14) 0%, rgba(16, 185, 129, 0.06) 40%, transparent 75%)',
            pointerEvents: 'none',
            mixBlendMode: 'screen',
          }}
        />
      )}

      {/* Tactile Fine Grain Texture Overlay (300gsm paper micro-structure) */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          width: '100%',
          height: '100%',
          opacity: activeDark ? 0.038 : 0.022,
          backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)'/%3E%3C/svg%3E")`,
          backgroundRepeat: 'repeat',
          pointerEvents: 'none',
        }}
      />

      {/* Gentle, steady spatial drift keyframes without color-shifting */}
      <style>{`
        @keyframes gentleOrbFloatLeft {
          0% {
            transform: translate3d(-60px, 0, 0) scale(0.97);
          }
          50% {
            transform: translate3d(70px, -25px, 0) scale(1.05);
          }
          100% {
            transform: translate3d(-30px, 35px, 0) scale(1.01);
          }
        }

        @keyframes gentleOrbFloatRight {
          0% {
            transform: translate3d(50px, 0, 0) scale(1.03);
          }
          50% {
            transform: translate3d(-65px, 30px, 0) scale(0.96);
          }
          100% {
            transform: translate3d(25px, -20px, 0) scale(1.04);
          }
        }

        @keyframes gentleOrbFloatBottom {
          0% {
            transform: translate3d(-35px, 15px, 0);
          }
          50% {
            transform: translate3d(45px, -15px, 0);
          }
          100% {
            transform: translate3d(-35px, 15px, 0);
          }
        }
      `}</style>
    </div>
  );
};
