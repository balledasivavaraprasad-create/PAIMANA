# Architecture Decision Record — Target Product Architecture

## Decision

Rebuild InfraBuild-AI as a product platform with a polished public landing page and a modular authenticated command center around the existing agentic monitoring engine.

## Core decision

```text
Public Product Layer
        ↓
Authenticated Experience
        ↓
Application Backend
        ↓
Domain Services
        ├── Monitoring
        ├── Peer Intelligence
        ├── Investigation
        ├── Analytics
        ├── Notification Automation
        └── Intervention Tracking
        ↓
Existing PAIMANA Agent + ML Models
```

## Rationale

The existing agent contains valuable domain logic and should not be rewritten simply to support a frontend redesign.

The frontend needs better product structure than the current page-by-page dashboard approach.

## Key architectural boundary

The browser does not own:

- DPHIS calculation
- threshold/event logic
- agent decision logic
- recipient trust
- webhook secrets
- intervention authorization

The browser visualizes these domain states.

## Success criteria

The final product feels like one system, not separate pages built by separate agents.
