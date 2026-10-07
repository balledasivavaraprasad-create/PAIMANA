# Recommended Parallel Workstreams

## Workstream A — Design System / Shared UI

Scope:

- theme tokens
- typography
- buttons
- cards
- tables
- badges
- popovers
- dropdowns
- drawers
- modal
- reusable layout primitives

Depends on: none.

Provides: shared visual foundation.

## Workstream B — Landing Page

Scope:

- public route
- hero
- architecture storytelling
- motion
- product sections

Depends on: design system.

## Workstream C — App Shell / Navigation

Scope:

- authenticated shell
- routing
- top bar
- nav
- global search
- theme

Depends on: design system.

## Workstream D — Overview / Dashboard

Scope:

- portfolio pulse
- change feed
- risk trend
- attention matrix
- monitoring health

Depends on: shell + API contracts.

## Workstream E — Portfolio

Scope:

- project table
- filters
- sorting
- responsive cards

Depends on: shell + backend project APIs.

## Workstream F — Analytics

Scope:

- Plotly components
- analytics aggregation integration
- cross-filtering
- export

Depends on: design system + analytics data contract.

## Workstream G — Project Intelligence

Scope:

- project detail
- risk explanation
- peer panel
- timeline

Depends on: project/risk/peer APIs.

## Workstream H — Investigation UI

Scope:

- investigation page/drawer
- evidence board
- hypothesis board
- tool timeline
- approval UI

Depends on: investigation contracts.

## Workstream I — Backend / Analytics APIs

Scope:

- aggregation endpoints
- query optimization
- filtering semantics

Depends on: data model.

## Workstream J — Agent Integration / Peer Intelligence

Scope:

- adapter around current Python agent
- peer API contract
- peer cohort analytics
- investigation trigger plumbing

Depends on: agent contract.

## Workstream K — n8n Automation

Scope:

- webhook
- signature validation
- OpenAI node
- email node
- idempotency
- delivery status

Depends on: notification contract.

## Workstream L — QA / Accessibility / Performance

Scope:

- E2E
- visual regression
- dark/light verification
- accessibility
- performance

Runs continuously and finalizes after feature work.
