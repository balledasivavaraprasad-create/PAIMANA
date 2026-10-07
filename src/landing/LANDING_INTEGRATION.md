# InfraBuild-AI / Paimana 2.0 Editorial Landing Page — Integration Contract

This document specifies the integration, architecture, motion discipline, and spatial composition for the public editorial landing page of **InfraBuild-AI / Paimana 2.0**.

---

## 1. Executive Summary & Aesthetic North Star

The public landing experience has been created as an **Editorial Product Film** that users can scroll through:

- **Aesthetic**: Restrained, calm, intelligent, expensive, and contemporary. Warm white/cream base (`#FAF9F5`), near-black typography (`#121314`), subtle borders (`#E5E3DC`), and large soft organic color fields (Peach, Lavender, Mint, Sky Blue).
- **Visual Contrast**: A single high-contrast midnight section for **Human Approval** (`#0B0F17`).
- **Typography**: High contrast, tight line-heights, tight letter-spacing, and clean geometric proportions powered by *Plus Jakarta Sans* and *JetBrains Mono*.
- **Motion Quality**: Zero bounce, zero neon clichés, zero gimmicky rotating 3D models. Driven by precision cubic-bezier reveals (`0.16, 1, 0.3, 1`), staggered view entries, top reading progress indicator, live SVG telemetry arcs, and interactive state morphing.

---

## 2. Section Map & Storytelling Sequence

The page follows the exact 15-stage narrative:

1. **Floating Pill Navigation (`Navigation.tsx`)**:
   - Floating dark pill (`rgba(18, 19, 20, 0.94)` with 20px blur)
   - Left: Brand mark `▲ PAIMANA .AI`
   - Middle: Smooth anchor links (`Risk Pattern`, `Surveillance`, `Peer Cohorts`, `Workstation`, `System Loop`)
   - Right: High-contrast white CTA (`Enter Platform →`)

2. **Hero Section (`HeroSection.tsx`)**:
   - Eyebrow: `PAIMANA 2.0 • CONTINUOUS INFRASTRUCTURE INTELLIGENCE`
   - Headline: `YOUR INFRASTRUCTURE PORTFOLIO CHANGES BEFORE THE CRISIS DOES.`
   - Large soft peach organic region with live interactive peer cohort topology SVG
   - Interactive node switching (Target asset, Havelian-Thakot, Swat Expressway, Karachi-Hyderabad M-9)

3. **The Problem (`ProblemSection.tsx`)**:
   - Statement: `RISK DOESN'T ARRIVE ALL AT ONCE.`
   - Interactive 4-stage progression: `01 Normal Baseline` (38.2 DPHIS) → `02 Small Divergence` (48.6 DPHIS) → `03 Risk Acceleration` (64.8 DPHIS) → `04 Critical Event` (78.4 DPHIS)
   - Real-time progress vs IPC expenditure disparity bar and epidemiological notes

4. **Continuous Monitoring (`ContinuousMonitoringSection.tsx`)**:
   - Statement: `SEE WHAT CHANGED.`
   - Soft lavender region with interactive cycle comparison: `Baseline Snapshot (T-30d)` vs `Current Telemetry (Latest)`
   - Dynamic delta detection badges

5. **Peer Intelligence (`PeerIntelligenceSection.tsx`)**:
   - Statement: `A PROJECT ISN'T UNDERSTOOD IN ISOLATION.`
   - Dynamic scatter SVG with multi-factor similarity filter (fading distant candidates, highlighting 94% similarity cohort and target outlier)

6. **Agentic Investigation (`InvestigationSection.tsx`)**:
   - Statement: `WHEN THE SIGNAL MATTERS, INVESTIGATE.`
   - 5-step investigative trace (`01 Telemetry Trigger`, `02 Peer Cohort Probe`, `03 Ledger & Billing Audit`, `04 Hypothesis Falsification`, `05 Executive Action Formulation`) with interactive stepping and tool outputs

7. **Evidence Epistemology (`EvidenceSection.tsx`)**:
   - Statement: `KNOW WHAT IS OBSERVED. KNOW WHAT IS INFERRED.`
   - 4 distinct epistemological cards: `Observed Fact`, `Model Inference`, `Agent Hypothesis`, `Residual Uncertainty`

8. **Human Approval (`HumanApprovalSection.tsx`)**:
   - Midnight black section (`#0B0F17`): `INTELLIGENCE WITHOUT UNACCOUNTABLE AUTOMATION.`
   - 5-stage sovereign authorization pipeline (`Investigation` → `Recommendation` → `Validation` → `Human Approval` → `Governed Action`) with active intervention order `#INT-2026-089`

9. **Portfolio Workstation (`AnalyticsSection.tsx`)**:
   - Statement: `SEE THE PORTFOLIO. NOT JUST THE PROJECT.`
   - Interactive 4-tab national telemetry workstation: `Risk Matrix`, `DPHIS Drift`, `Sector Variance`, `Intervention Impact`

10. **Outcomes & Scale (`OutcomesSection.tsx`)**:
    - Statement: `PRECISION AT NATIONAL SCALE.`
    - Spacious editorial metrics: `428 Assets Monitored`, `1,420 Signals Detected`, `186 Investigations`, `94 Decisions Governed`

11. **System Lifecycle (`WalkthroughSection.tsx`)**:
    - Sticky 5-stage walkthrough: `01 Observe`, `02 Detect`, `03 Investigate`, `04 Act`, `05 Learn` with synchronized telemetry cards

12. **Technical Foundation (`TechnologySection.tsx`)**:
    - Statement: `ENGINEERED FOR RIGOR. NOT DEMO THEATRICS.`
    - Role-based architecture: `XGBoost (Predict)`, `SHAP (Explain)`, `Peer Intelligence (Contextualize)`, `LLM Supervisor (Investigate)`, `n8n (Automate)`, `Langfuse (Observe)`, `MongoDB (Persist)`, `React + TypeScript (Experience)`

13. **Frequently Asked Questions (`FaqSection.tsx`)**:
    - Clean minimal accordion answering core platform capabilities, empirical peer cohorting, and governance boundaries

14. **Final Call to Action (`FinalCtaSection.tsx`)**:
    - Grand soft peach sanctuary: `KNOW WHAT CHANGED BEFORE IT BECOMES OBVIOUS.`
    - Direct access buttons into the Command Platform

15. **Editorial Footer (`FooterSection.tsx`)**:
    - Minimalist footer with Product, Platform, Governance, and Deployment columns

---

## 3. Component Architecture & File Inventory

All files are self-contained under `frontend/landing/`:

```
frontend/landing/
├── editorial/
│   ├── Navigation.tsx
│   ├── HeroSection.tsx
│   ├── ProblemSection.tsx
│   ├── ContinuousMonitoringSection.tsx
│   ├── PeerIntelligenceSection.tsx
│   ├── InvestigationSection.tsx
│   ├── EvidenceSection.tsx
│   ├── HumanApprovalSection.tsx
│   ├── AnalyticsSection.tsx
│   ├── OutcomesSection.tsx
│   ├── WalkthroughSection.tsx
│   ├── TechnologySection.tsx
│   ├── FaqSection.tsx
│   ├── FinalCtaSection.tsx
│   ├── FooterSection.tsx
│   └── EditorialLandingPage.tsx
├── styles/
│   └── editorial-landing.css
└── index.ts
```

---

## 4. Routing & Seamless Application Switching

Routing is configured in `frontend/main.tsx`:
- Root path (`/` or `#/`) renders `EditorialLandingPage`.
- Command center route (`/app` or `#/app`) renders `AuthenticatedApp`.
- Clicking `Enter Platform →` from any landing page section smoothly switches the view and updates `window.location.hash = '/app'`.
- In `AuthenticatedApp`, a floating pill button `← Public Landing Page` allows instant return to the landing page.

---

## 5. Build & Test Verification

- **Production Build**: Clean compilation via `npm run build` (`tsc && vite build`).
- **Test Suite**: 35/35 passing unit and integration tests via `npm run test` (`vitest run`).
- **Live Server**: Active on `http://localhost:3001/`.