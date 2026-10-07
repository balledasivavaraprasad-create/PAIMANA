# Analytics Page

## Mission

Analytics should be the portfolio intelligence laboratory, not a decorative KPI page.

The page must help users answer:

- What is happening across the portfolio?
- What changed?
- Where is risk concentrated?
- Which projects are unusual compared with peers?
- Which event patterns are increasing?
- What is the agent investigating?
- What happened after intervention?

## Required visualizations

### 1. Portfolio risk trend

Plotly line chart:

X = monitoring/report period
Y = DPHIS

Optional toggles:

- average
- median
- high threshold
- critical threshold
- project count

### 2. Risk distribution

Histogram/violin/box.

Compare current and previous monitoring periods.

### 3. Cost vs schedule risk matrix

Scatter/bubble chart:

X = predicted cost overrun
Y = schedule slippage
Size = budget
Color = DPHIS/risk tier

Click-through to project.

### 4. Before vs current DPHIS

X = previous DPHIS
Y = current DPHIS

Diagonal reference line.

Use this to communicate monitoring change.

### 5. DPHIS change distribution

Diverging bar/histogram showing:

- large increase
- moderate increase
- stable
- moderate decrease
- large decrease

### 6. Event timeline + heatmap

Event types:

- THRESHOLD_CROSSED
- RISK_ACCELERATING
- MILESTONE_DELAYED
- PROGRESS_STALLED
- COST_PROGRESS_MISMATCH
- DATA_STALE
- PEER_OUTLIER / COHORT_ANOMALY when implemented

### 7. Geographic analytics

Plotly India map where reliable geometry/data are available.

Switch metrics:

- average DPHIS
- high/critical count
- budget exposure
- delayed projects

### 8. Sector analytics

- average DPHIS by sector
- tier distribution
- budget exposure
- risk change

### 9. Agency analytics

- project count
- average DPHIS
- slippage
- mismatch
- investigations
- interventions

### 10. Cost analytics

- original vs revised cost
- expenditure vs physical progress
- cost overrun distribution
- cost-progress mismatch trend

### 11. Schedule analytics

- planned vs revised completion
- slippage distribution
- project age vs progress
- milestone delays

### 12. Investigation funnel

```text
Events
↓
Investigations
↓
Recommendations
↓
Human review
↓
Approved
↓
Executed
↓
Outcome recorded
```

### 13. Intervention outcomes

Before/after comparison.

Do not imply causality from simple before/after changes.

### 14. Data health

- fresh
- stale
- missing baseline
- missing required fields
- sync failures

## Global analytics filter bar

Filters must affect the entire page:

- date/period
- ministry
- sector
- state
- agency
- risk tier
- event
- project stage
- budget band
- freshness

## Cross-filter behavior

Clicking a state, sector, event category or chart point should update the page filter state.

## Insight panel

Add a “Portfolio Intelligence” panel with 3–5 deterministic data-backed findings.

Every statement should point to supporting data or a filtered project set.

LLM summarization may be added later as a wording layer, never as the source of numbers.

## Plotly requirements

Use `react-plotly.js` where practical.
Create shared chart configuration and theme utilities.
Use memoized data transformations.
Lazy-load large charts where helpful.

## Export

CSV for filtered tabular analytics.
Plot export via Plotly.
Optional report/PDF export only if supported by the existing product stack.
