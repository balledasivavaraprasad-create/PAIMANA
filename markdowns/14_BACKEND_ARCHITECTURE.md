# Backend Architecture

## Objective

Create a backend that cleanly separates:

- domain logic
- monitoring
- agentic investigation
- analytics aggregation
- notification automation
- persistence
- auth

## Recommended service boundaries

```text
API Layer
  ↓
Application Services
  ├── MonitoringService
  ├── InvestigationService
  ├── AnalyticsService
  ├── NotificationAutomationService
  ├── InterventionService
  └── ProjectService

Domain / Agent Integration
  └── Python PAIMANA Agent

Persistence
  ├── project data store
  ├── monitoring history
  ├── investigations
  ├── alerts
  ├── interventions
  └── audit
```

## FastAPI preference

If the main application backend uses FastAPI, expose integration through a FastAPI adapter rather than exposing the standalone stdlib server directly to the browser.

## Principle

The main backend should become the public application API.

The Python agent can remain a domain/library component behind it.

## Monitoring entry points

Support:

1. project update event
2. scheduled scan
3. synchronized source update
4. manual re-evaluation with explicit permission

## Monitoring pipeline

```text
new state
→ validation
→ snapshot identity/hash
→ compare previous state
→ if material/temporal reassessment
→ feature engineering
→ prediction
→ SHAP/explanation
→ DPHIS
→ event engine
→ peer context
→ investigation trigger
```

## Background jobs

Use a job/queue mechanism only if the existing infrastructure supports it cleanly.

Do not make HTTP requests wait on LLMs, n8n, peer analysis or email delivery where asynchronous processing is appropriate.

## Data ownership

The backend should define which system owns each record.

Do not create duplicated “source of truth” copies of project metadata unnecessarily.
