# Project Portfolio Specification

## Purpose

Provide a powerful project inventory that is easy to scan and filter.

## Header

Title:

`National Project Portfolio`

Subtext should mention that the portfolio is continuously monitored.

Show monitoring timestamp using real data.

## Global filters

- ministry
- sector
- state
- agency
- risk tier
- event type
- project stage
- budget band
- data freshness
- monitoring date

Search should support project code/name.

## Portfolio views

### Table view

Columns:

- project
- sector
- state
- agency
- budget
- progress
- expenditure
- DPHIS
- trend
- active event
- peer deviation
- investigation status
- intervention status
- freshness

### Compact card view

Use for smaller screens or portfolio scanning.

## Sorting

Offer:

- DPHIS
- DPHIS change
- budget
- schedule slippage
- cost overrun
- peer deviation
- last update

## Row interactions

Click project → project intelligence page.

Click DPHIS → risk explanation panel.

Click event → investigation.

Click peer deviation → peer panel.

## No-data behavior

Never display zero values to imply data availability. Show “No data” or “Not available” when that is the truthful state.
