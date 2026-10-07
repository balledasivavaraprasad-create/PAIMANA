import HeroIntelligenceField from '../visuals/HeroIntelligenceField';

/**
 * Hero.
 *
 * Headline and CTAs carry the argument; the intelligence field beside them
 * demonstrates it. On narrow viewports the text comes first and the visual
 * follows, so the claim is never pushed below an unproven illustration.
 */
export default function Hero() {
  return (
    <section className="lp-hero" id="hero" aria-labelledby="hero-title">
      <div className="lp-hero__bg" aria-hidden="true">
        <div className="lp-hero__grid" />
        <div className="lp-hero__wash" />
      </div>

      <div className="landing-container lp-hero__inner">
        <div className="lp-hero__text">
          <p className="lp-hero__eyebrow">
            <span className="lp-hero__eyebrow-dot" aria-hidden="true" />
            Continuous infrastructure intelligence
          </p>

          <h1 className="lp-hero__title" id="hero-title">
            Know what changed
            <br />
            before it becomes a
            <br />
            <span className="lp-hero__title-accent">project crisis.</span>
          </h1>

          <p className="lp-hero__body">
            InfraBuild-AI continuously observes project state, detects meaningful changes, predicts
            emerging cost and schedule risk, compares each project against relevant peers, investigates
            possible causes, and supports evidence-backed intervention decisions.
          </p>

          <div className="lp-hero__actions">
            <a href="#signin" className="lp-button lp-button--primary lp-button--lg">
              Open InfraBuild-AI
              <svg width="15" height="15" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" aria-hidden="true">
                <path d="M3 8h10M9 4l4 4-4 4" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </a>
            <a href="#how-it-works" className="lp-button lp-button--secondary lp-button--lg">
              Explore the intelligence loop
            </a>
          </div>

          <ul className="lp-hero__meta">
            <li className="lp-hero__meta-item">
              <span className="lp-hero__meta-label">Evidence-attributed</span>
              <span className="lp-hero__meta-value">Every prediction explained</span>
            </li>
            <li className="lp-hero__meta-item">
              <span className="lp-hero__meta-label">Peer-contextualised</span>
              <span className="lp-hero__meta-value">Compared against comparable projects</span>
            </li>
            <li className="lp-hero__meta-item">
              <span className="lp-hero__meta-label">Human-gated</span>
              <span className="lp-hero__meta-value">Approval before any action</span>
            </li>
          </ul>
        </div>

        <div className="lp-hero__visual-wrap">
          <HeroIntelligenceField />
        </div>
      </div>

      <a className="lp-hero__scroll" href="#product">
        <span className="lp-hero__scroll-label">Scroll</span>
        <span className="lp-hero__scroll-line" aria-hidden="true" />
      </a>
    </section>
  );
}