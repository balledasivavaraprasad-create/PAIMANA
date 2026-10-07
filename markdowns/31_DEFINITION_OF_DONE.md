# Definition of Done

A feature is not done because it renders.

## Product correctness

- matches the intended product narrative
- uses real data/contracts
- does not duplicate backend logic

## Visual quality

- high-quality responsive composition
- consistent design system
- professional typography
- no accidental overflow
- no broken states

## Theme quality

Test:

- dark
- light
- hover
- focus
- selected
- open menus
- dropdowns
- popovers
- tooltips

## Data quality

- loading state
- error state
- empty state
- partial state
- stale data

## Interaction quality

- keyboard accessible
- drill-down works
- filters persist correctly
- back navigation works
- links preserve context

## Technical quality

- TypeScript passes
- lint passes
- tests pass
- no console errors
- no leaked secrets

## Agent integration quality

Where applicable:

- request/response contract verified
- timeout handled
- retry handled
- domain errors mapped

## Analytics quality

- charts are data-backed
- filter interactions are connected
- no fake metrics
- large data remains usable

## Motion quality

- reduced-motion supported
- no motion harming readability
- transitions remain consistent

## Release quality

- staging smoke test passed
- production environment variables verified
- deployment rollback path known
