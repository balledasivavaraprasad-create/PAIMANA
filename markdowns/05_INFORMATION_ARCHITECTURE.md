# Information Architecture

## Public routes

```text
/
/about
/product
/architecture
/technology
```

## Authenticated routes

```text
/app
/app/portfolio
/app/projects/:projectId
/app/analytics
/app/investigations
/app/alerts
/app/interventions
/app/data-health
/app/models
/app/settings
/app/admin
```

## Main navigation

Primary navigation should be intentionally small:

- Overview
- Portfolio
- Analytics
- Investigations
- Alerts
- Interventions

Secondary/admin navigation:

- Data Health
- Models
- Audit
- Settings

## Global command surface

A top-level command/search control may support:

- project lookup
- state/sector lookup
- event lookup
- investigation lookup

This is not a generic AI chat box. It should be an operational search/command surface.

## Project-centric navigation

From any important project representation, allow entry into:

- project overview
- risk/change
- peers
- investigations
- recommendations
- interventions
- history

## Navigation principles

Do not hide essential monitoring information in nested menus.

Do not use sidebar clutter to display every backend capability.

Admin-only concepts should not visually dominate the standard operator experience.
