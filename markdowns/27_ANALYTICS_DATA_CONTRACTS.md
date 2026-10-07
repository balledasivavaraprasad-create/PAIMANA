# Analytics Data Contracts

## Rule

Analytics should be backed by pre-aggregated domain data where possible.

## Overview aggregate

```json
{
  "period": {
    "from": "...",
    "to": "..."
  },
  "project_count": 0,
  "high_risk_count": 0,
  "critical_count": 0,
  "average_dphis": null,
  "risk_accelerating_count": 0,
  "stale_count": 0,
  "budget_exposure": null
}
```

## Risk trend

Return sorted time buckets:

```json
[
  {
    "period": "2026-07",
    "average_dphis": 42.1,
    "median_dphis": 39.2,
    "high_count": 12,
    "critical_count": 3,
    "project_count": 210
  }
]
```

## Risk matrix

Each point should include:

```text
project_id
project_name
cost_risk
schedule_risk
dphis
budget
sector
state
event
```

## Event heatmap

Return:

```text
event_type
period
count
```

## Peer analytics

Return:

```text
project_id
cohort_size
cohort_quality
peer_median_dphis
peer_p75_dphis
peer_p90_dphis
target_dphis
peer_deviation
peer_trend
classification
```

## Intervention outcome

Return:

```text
intervention_id
project_id
before_metrics
after_metrics
observed_change
outcome_status
```

## Null / unavailable semantics

Never use fabricated zeros.

Use:

```text
null
availability = false
reason = "insufficient_peer_data"
```

when required.
