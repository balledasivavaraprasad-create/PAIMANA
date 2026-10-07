# Alerts and Notifications

## Alert center

The Alerts page should answer:

- what happened?
- when?
- to which project?
- why was it triggered?
- was it acknowledged?
- was an investigation created?
- was an email sent?

## Alert card

Show:

- severity
- event type
- project
- current DPHIS
- previous DPHIS
- threshold
- trigger reason
- timestamp
- delivery status
- investigation status

## Alert taxonomy

Use existing event vocabulary where available:

- THRESHOLD_CROSSED
- RISK_ACCELERATING
- MILESTONE_DELAYED
- PROGRESS_STALLED
- COST_PROGRESS_MISMATCH
- DATA_STALE
- PEER_OUTLIER
- COHORT_ANOMALY

## Acknowledgement

Acknowledging an alert is not approving an intervention.

Keep the states separate.

## Delivery status

```text
QUEUED
SENT
RETRYING
FAILED
```

## Notification recipients

Recipients are backend-provided and must not be user-editable from arbitrary client fields unless role/permission allows it.

## Email content principle

Emails should report facts, model predictions and available contextual evidence. Avoid unsupported causal claims.

## Duplicate prevention

Use backend alert deduplication and event IDs. n8n must also enforce idempotency for repeated webhook delivery.
