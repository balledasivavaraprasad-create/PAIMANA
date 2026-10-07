import React, { useEffect, useState } from 'react';
import '../styles/editorial-landing.css';
import { Navigation } from './Navigation';
import { WelcomeIntroSection } from './WelcomeIntroSection';
import { HeroSection } from './HeroSection';
import { InteractiveLivingBackground } from '../../components/InteractiveLivingBackground';
import { ProblemSection } from './ProblemSection';
import { ContinuousMonitoringSection } from './ContinuousMonitoringSection';
import { PeerIntelligenceSection } from './PeerIntelligenceSection';
import { InvestigationSection } from './InvestigationSection';
import { EvidenceSection } from './EvidenceSection';
import { HumanApprovalSection } from './HumanApprovalSection';
import { AnalyticsSection } from './AnalyticsSection';
import { OutcomesSection } from './OutcomesSection';
import { WalkthroughSection } from './WalkthroughSection';
import { TechnologySection } from './TechnologySection';
import { FaqSection } from './FaqSection';
import { FinalCtaSection } from './FinalCtaSection';
import { FooterSection } from './FooterSection';

interface EditorialLandingPageProps {
  onEnterApp?: () => void;
}

export const EditorialLandingPage: React.FC<EditorialLandingPageProps> = ({ onEnterApp }) => {
  const [scrollProgress, setScrollProgress] = useState(0);

  const handleOpenPlatform = onEnterApp || (() => {
    window.location.hash = '/app';
  });

  const handleScrollToHero = () => {
    const heroEl = document.getElementById('hero');
    if (heroEl) {
      heroEl.scrollIntoView({ behavior: 'smooth' });
    }
  };

  // Track scroll progress for reading bar
  useEffect(() => {
    let frame = 0;
    const measure = () => {
      frame = 0;
      const scrollTop = window.scrollY;
      const scrollable = document.documentElement.scrollHeight - window.innerHeight;
      setScrollProgress(scrollable > 0 ? Math.min(Math.max(scrollTop / scrollable, 0), 1) : 0);
    };

    const onScroll = () => {
      if (frame) return;
      frame = requestAnimationFrame(measure);
    };

    measure();
    window.addEventListener('scroll', onScroll, { passive: true });
    window.addEventListener('resize', onScroll, { passive: true });

    return () => {
      window.removeEventListener('scroll', onScroll);
      window.removeEventListener('resize', onScroll);
      if (frame) cancelAnimationFrame(frame);
    };
  }, []);

  // Buttery Smooth Intersection Observer for Staggered Scroll Reveals
  useEffect(() => {
    // Check elements already visible in viewport on initial load (e.g. Hero Section)
    const checkVisibleOnMount = () => {
      const windowHeight = window.innerHeight;
      document.querySelectorAll('.reveal-on-scroll').forEach((el, index) => {
        const rect = el.getBoundingClientRect();
        // If element is already in or near viewport on initial mount
        if (rect.top < windowHeight * 0.92 && rect.bottom > 0) {
          setTimeout(() => {
            el.classList.add('is-revealed');
          }, Math.min(index * 60, 240));
        }
      });
    };

    if (!('IntersectionObserver' in window)) {
      document.querySelectorAll('.reveal-on-scroll').forEach((el) => {
        el.classList.add('is-revealed');
      });
      return;
    }

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add('is-revealed');
            observer.unobserve(entry.target);
          }
        });
      },
      {
        threshold: 0.08,
        rootMargin: '0px 0px -40px 0px', // Triggers as soon as element glides into view
      }
    );

    const observeAll = () => {
      document.querySelectorAll('.reveal-on-scroll:not(.is-revealed)').forEach((el) => {
        observer.observe(el);
      });
    };

    // Initial check on mount
    checkVisibleOnMount();
    observeAll();

    // Secondary pass for any dynamically hydrated components
    const mountTimer = setTimeout(() => {
      checkVisibleOnMount();
      observeAll();
    }, 120);

    // Watch for dynamically rendered child elements
    const mutationObserver = new MutationObserver(() => {
      observeAll();
    });
    mutationObserver.observe(document.body, { childList: true, subtree: true });

    // High-performance passive scroll check ensuring no item is ever skipped if scrolled rapidly
    let scrollRaf = 0;
    const handleScrollCheck = () => {
      if (scrollRaf) return;
      scrollRaf = requestAnimationFrame(() => {
        scrollRaf = 0;
        const windowHeight = window.innerHeight;
        document.querySelectorAll('.reveal-on-scroll:not(.is-revealed)').forEach((el) => {
          const rect = el.getBoundingClientRect();
          if (rect.top < windowHeight - 10) {
            el.classList.add('is-revealed');
            observer.unobserve(el);
          }
        });
      });
    };
    window.addEventListener('scroll', handleScrollCheck, { passive: true });

    return () => {
      clearTimeout(mountTimer);
      observer.disconnect();
      mutationObserver.disconnect();
      window.removeEventListener('scroll', handleScrollCheck);
      if (scrollRaf) cancelAnimationFrame(scrollRaf);
    };
  }, []);

  return (
    <div className="editorial-landing" style={{ position: 'relative' }}>
      {/* Living Atmospheric Juggling Mesh & Tactile Noise Background */}
      <InteractiveLivingBackground />

      {/* Top Reading Progress Bar */}
      <div
        className="el-scroll-progress-bar"
        style={{ width: `${scrollProgress * 100}%` }}
      />

      {/* Floating Pill Navigation */}
      <Navigation onOpenPlatform={handleOpenPlatform} />

      {/* Main Storytelling Sections */}
      <main style={{ position: 'relative', zIndex: 1 }}>
        {/* 0. Welcome Entrance Experience: "Welcome to InfraBuild AI" */}
        <WelcomeIntroSection
          onSignIn={handleOpenPlatform}
          onExploreLanding={handleScrollToHero}
        />

        {/* 1. Hero with Peach Organic Field & Live Mockup */}
        <HeroSection onOpenPlatform={handleOpenPlatform} />

        {/* 2. The Problem: Risk doesn't arrive all at once */}
        <ProblemSection />

        {/* 3. Continuous Monitoring: See what changed */}
        <ContinuousMonitoringSection />

        {/* 4. Peer Intelligence: A project isn't understood in isolation */}
        <PeerIntelligenceSection />

        {/* 5. Agentic Investigation: When the signal matters, investigate */}
        <InvestigationSection />

        {/* 6. Evidence: Know what is observed. Know what is inferred */}
        <EvidenceSection />

        {/* 7. Human Approval: Dark Section - Intelligence without unaccountable automation */}
        <HumanApprovalSection onOpenPlatform={handleOpenPlatform} />

        {/* 8. Portfolio Analytics Workstation */}
        <AnalyticsSection />

        {/* 9. National Telemetry & Outcomes */}
        <OutcomesSection />

        {/* 10. System Walkthrough: 5 Stages (Observe, Detect, Investigate, Act, Learn) */}
        <WalkthroughSection />

        {/* 11. Technology Foundation */}
        <TechnologySection />

        {/* 12. Frequently Asked Questions */}
        <FaqSection />

        {/* 13. Final CTA with Soft Peach Field */}
        <FinalCtaSection onEnterApp={handleOpenPlatform} />
      </main>

      {/* 14. Editorial Footer */}
      <FooterSection />
    </div>
  );
};

export default EditorialLandingPage;
