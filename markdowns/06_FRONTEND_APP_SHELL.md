# Frontend App Shell

## Stack expectations

- React
- TypeScript
- existing router if present, otherwise a conventional React router
- Plotly / `react-plotly.js` for analytical visualizations
- existing state/data-fetching approach where stable
- CSS system already present where possible

Do not introduce a second styling system merely for the redesign.

## Shell structure

```text
AppShell
├── TopBar
├── MainNavigation / Sidebar
├── ContextHeader
├── MainContent
└── GlobalCommand / Notifications
```

## Top bar

Include:

- product mark
- current section
- monitoring status
- global search/command
- alerts
- user menu
- theme toggle

## Monitoring status

Should represent actual backend status.

Possible states:

- Monitoring active
- Last sync delayed
- Data stale
- System degraded
- Integration unavailable

Never fake “live” status.

## Responsive behavior

Desktop-first but support:

- laptop
- tablet
- mobile summary mode

Dense tables should become horizontal scroll or card list on small screens; never squash columns into illegibility.

## Theme provider

Centralize:

- semantic colors
- background/surface tokens
- typography tokens
- chart theme
- focus styles

Plotly theme should consume the same design tokens.

## Global data states

Provide reusable:

- `PageSkeleton`
- `SectionSkeleton`
- `EmptyState`
- `ErrorState`
- `PartialDataState`
- `StaleDataBanner`

## Toasts

Use toasts only for transient events. Important alert/investigation state must also be persisted visually in the relevant page.

## Modals

Prefer drawers or side panels for investigation details when users need to retain portfolio context.
