# Dashboard / Overview

## Purpose

The Overview page is the operational command center.

It should answer in 10 seconds:

1. What is the portfolio state?
2. What changed?
3. What needs attention?
4. What is the system doing about it?

## Section order

### 1. Portfolio Pulse

KPI cards:

- projects monitored
- high/critical projects
- average DPHIS
- risk acceleration count
- cost-progress mismatch count
- schedule-slippage count
- projected exposure if actually available
- stale data count

Each KPI can drill into the filtered portfolio.

### 2. What Changed Since Last Cycle?

Use a compact, high-signal change feed.

Each item:

- project
- previous vs current DPHIS
- key changed dimensions
- event
- peer deviation if available
- investigation status

### 3. Portfolio Risk Trend

Plotly time-series.

### 4. Attention Matrix

Plotly scatter:

X = cost risk
Y = schedule risk
Size = project budget
Color = DPHIS/risk tier

### 5. Emerging Signals

Event heatmap/timeline.

### 6. Agentic Activity

Show:

- investigations active
- pending review
- recent completed investigations
- recommendations awaiting approval

### 7. Intervention Outcomes

Compact before/after outcome summary.

### 8. Monitoring Health

- last synchronization
- stale percentage
- failures
- model status
- automation delivery status

## Design rule

The Overview is not the same as Analytics.

Overview = operational signal.

Analytics = deep exploration.
