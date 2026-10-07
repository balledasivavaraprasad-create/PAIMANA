# InfraBuild-AI Frontend + Backend Rebuild Specification

## Purpose

This documentation pack is the shared contract for rebuilding the InfraBuild-AI product with multiple coding agents working in parallel.

The rebuild is not a blank-slate rewrite. The existing monitoring/agentic layer remains a major capability and should be integrated behind a cleaner product architecture.

The product narrative is:

> **Observe → Detect Change → Predict → Explain → Compare → Investigate → Recommend → Approve → Act → Measure → Learn → Monitor Again**

The application should feel like a high-end infrastructure intelligence platform rather than a generic admin dashboard.

## Product identity

**Product:** InfraBuild-AI

**Domain:** Infrastructure project monitoring, predictive risk intelligence, peer intelligence, agentic investigation, intervention tracking.

**Primary data context:** PAIMANA project data and related project-level sources.

## Critical implementation rule

The existing agent package is a source of truth for current capabilities. Do not silently invent that a capability exists merely because it is described in future architecture.

Current implementation includes substantial monitoring, event, state, evidence, hypothesis, memory, recommendation, governance, reliability, and automation infrastructure. Some integrations remain developmental or optional. Preserve those boundaries.

## Rebuild goals

1. Create a premium, professional landing page that explains the product in seconds.
2. Rebuild the authenticated product shell into a coherent command-center experience.
3. Make Analytics a real portfolio intelligence surface, not a KPI page.
4. Make project pages explain current state, change, peer context, investigation, and outcomes.
5. Make the agentic investigation visible and auditable without exposing noisy internal implementation details.
6. Integrate the Python agent/backend cleanly through explicit contracts.
7. Add reliable n8n alert automation without moving business decisions into n8n.
8. Make the product light-mode and dark-mode correct.
9. Use high-quality motion deliberately, never as decoration that harms usability.
10. Make parallel-agent development safe through ownership boundaries and merge contracts.

## Non-goals

Do not rebuild the ML models just because the frontend is being redesigned.
Do not claim causal certainty where the agent only has heuristic or incomplete evidence.
Do not expose internal secrets or webhook URLs to the browser.
Do not make consequential government actions fully autonomous.
Do not fill empty analytics states with fake values.

## Document map

- `01_PRODUCT_VISION.md` — product story, personas, value proposition.
- `02_PRODUCT_PRINCIPLES.md` — non-negotiable product principles.
- `03_BRAND_DESIGN_SYSTEM.md` — visual system, color, type, surfaces, components.
- `04_LANDING_PAGE_SPEC.md` — complete marketing/landing-page structure.
- `05_INFORMATION_ARCHITECTURE.md` — application navigation and page hierarchy.
- `06_FRONTEND_APP_SHELL.md` — shell, routing, theming, responsive behavior.
- `07_DASHBOARD_HOME.md` — command-center dashboard specification.
- `08_PROJECT_PORTFOLIO.md` — portfolio/project-list experience.
- `09_PROJECT_DETAIL.md` — single-project intelligence view.
- `10_ANALYTICS.md` — portfolio analytics and Plotly specification.
- `11_AGENTIC_INVESTIGATION_UI.md` — investigation experience.
- `12_ALERTS_AND_NOTIFICATIONS.md` — alert center and notifications.
- `13_AUTH_RBAC.md` — authentication, roles, permissions.
- `14_BACKEND_ARCHITECTURE.md` — backend service boundaries.
- `15_API_CONTRACTS.md` — frontend/backend API contract.
- `16_AGENT_INTEGRATION.md` — integration with the existing Python agent.
- `17_PEER_INTELLIGENCE.md` — peer cohort and peer-aware monitoring.
- `18_N8N_AUTOMATION.md` — webhook/email/OpenAI automation.
- `19_DATA_MODEL.md` — application data model.
- `20_OBSERVABILITY.md` — Langfuse and system telemetry.
- `21_SECURITY.md` — security requirements.
- `22_ACCESSIBILITY.md` — accessibility requirements.
- `23_MOTION_SYSTEM.md` — animation/microinteraction system.
- `24_PERFORMANCE.md` — performance budgets and implementation rules.
- `25_TEST_STRATEGY.md` — unit, integration, E2E and visual testing.
- `26_ENVIRONMENT_DEPLOYMENT.md` — environment and deployment contract.
- `27_ANALYTICS_DATA_CONTRACTS.md` — analytics aggregation contracts.
- `28_LOADING_ERROR_EMPTY_STATES.md` — resilient UI states.
- `29_PARALLEL_AGENT_MERGE_CONTRACT.md` — how work is divided and merged.
- `30_WORKSTREAMS.md` — recommended parallel workstreams.
- `31_DEFINITION_OF_DONE.md` — completion criteria.
- `32_COPY_GUIDELINES.md` — wording and UX writing rules.
- `33_NOT_IN_SCOPE.md` — ideas intentionally postponed.

## Architecture at a glance

```text
                    PAIMANA / PROJECT SOURCES
                               ↓
                    INGEST + DATA QUALITY
                               ↓
                    SNAPSHOT / CHANGE ENGINE
                               ↓
                  PREDICTIVE RISK INTELLIGENCE
                ┌──────────────┼──────────────┐
                ↓              ↓              ↓
             Cost risk     Time risk      Risk score
                └──────────────┼──────────────┘
                               ↓
                         SHAP + DPHIS
                               ↓
                          EVENT ENGINE
                               ↓
                    PEER INTELLIGENCE LAYER
                               ↓
                       AGENTIC INVESTIGATOR
                               ↓
                    RECOMMENDATION ENGINE
                               ↓
                       HUMAN APPROVAL
                               ↓
                     DURABLE ACTION OUTBOX
                               ↓
                              n8n
                               ↓
                         NOTIFY / ACT
                               ↓
                      OUTCOME MEASUREMENT
                               ↓
                       MEMORY / PRECEDENT
                               ↓
                       NEXT MONITORING CYCLE
```

## UI philosophy

The product should communicate intelligence through hierarchy and interaction, not through buzzwords.

A user should be able to understand:

- portfolio health
- what changed
- which projects need attention
- why something changed
- how the project compares with peers
- what the agent investigated
- what remains uncertain
- what is recommended
- what has already been approved or acted upon
- whether the intervention produced an observed change

within minutes, without reading documentation.
