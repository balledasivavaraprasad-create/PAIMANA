# Performance Requirements

## Goals

Landing page should feel instant on first interaction.

Authenticated analytics pages should remain usable with hundreds/thousands of projects.

## Rules

- lazy-load heavy Plotly charts
- memoize transformed datasets
- debounce search
- virtualize long tables if required
- avoid repeated API calls for the same portfolio slice
- use aggregated analytics endpoints for expensive portfolio metrics
- avoid giant GeoJSON in component files
- cache stable reference data
- use route-level code splitting

## API

Avoid 10–20 independent requests for every chart when one aggregated response can serve the page safely.

## Plotly

Limit point counts for dense scatter plots when necessary.

Use downsampling/aggregation for very large series.

## Animation

Use transform/opacity where possible.

Do not animate expensive layout properties continuously.

## Monitoring

Do not run heavy model/SHAP/investigation work synchronously in user-facing requests unless the use case explicitly requires it.
