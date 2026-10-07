import '../styles/landing.css';

import { ThemeProvider } from '../components/ThemeContext';
import Header from '../components/Header';
import Footer from '../components/Footer';
import ScrollProgress from '../components/ScrollProgress';
import { useLandingMeta } from '../motion/useLandingMeta';

import Hero from '../sections/Hero';
import ProofStrip from '../sections/ProofStrip';
import ProblemSection from '../sections/ProblemSection';
import DifferentiatorSection from '../sections/DifferentiatorSection';
import WhatChangedSection from '../sections/WhatChangedSection';
import PeerIntelligenceSection from '../sections/PeerIntelligenceSection';
import InvestigationSection from '../sections/InvestigationSection';
import AnalyticsSection from '../sections/AnalyticsSection';
import GovernanceSection from '../sections/GovernanceSection';
import WalkthroughSection from '../sections/WalkthroughSection';
import TechnologySection from '../sections/TechnologySection';
import FinalCTA from '../sections/FinalCTA';

/**
 * Public landing page.
 *
 * Section order follows 04_LANDING_PAGE_SPEC.md: hero, proof, problem,
 * differentiator, what-changed, peers, investigation, analytics, governance,
 * walkthrough, technology, CTA.
 *
 * The component is self-contained: it owns its theme scope, styles, and motion.
 * It mounts no providers from the authenticated application and does not read
 * or write shared application state, so it can be dropped into the router
 * without interfering with the app shell.
 */
export default function LandingPage() {
  useLandingMeta();

  return (
    <ThemeProvider className="landing-root">
      <a className="lp-skip" href="#main">
        Skip to main content
      </a>

      <ScrollProgress />
      <Header />

      <main id="main" className="lp-main" tabIndex={-1}>
        <Hero />
        <ProofStrip />
        <ProblemSection />
        <DifferentiatorSection />
        <WhatChangedSection />
        <PeerIntelligenceSection />
        <InvestigationSection />
        <AnalyticsSection />
        <GovernanceSection />
        <WalkthroughSection />
        <TechnologySection />
        <FinalCTA />
      </main>

      <Footer />
    </ThemeProvider>
  );
}