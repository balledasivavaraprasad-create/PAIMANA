# API Contracts

## Contract philosophy

Backend responses should be stable, explicit, typed, and frontend-friendly.

Use ISO 8601 timestamps.
Use IDs, not display names, for references.
Return `null` for unavailable optional values rather than fake zero values.

## Project

```http
GET /api/projects
GET /api/projects/{project_id}
POST /api/projects
PATCH /api/projects/{project_id}
```

## Risk

```http
GET /api/projects/{project_id}/risk
GET /api/projects/{project_id}/risk/history
GET /api/projects/{project_id}/explanations
```

Suggested response shape:

```json
{
  "project_id": "...",
  "current": {
    "dphis": 72.4,
    "risk_tier": "High",
    "predicted_cost_overrun_pct": 14.2,
    "predicted_schedule_slippage_months": 5.6
  },
  "previous": {
    "dphis": 58.1
  },
  "change": {
    "dphis_delta": 14.3,
    "trend": "increasing"
  },
  "events": [],
  "data_quality": {}
}
```

## Peers

```http
GET /api/projects/{project_id}/peers
GET /api/projects/{project_id}/peer-analysis
```

Response should include:

- cohort size
- cohort quality
- matching criteria
- peer median/percentiles
- target deviation
- trajectory comparison
- peer anomalies
- relevant peer interventions/outcomes

## Investigation

```http
GET /api/investigations
GET /api/investigations/{investigation_id}
POST /api/investigations
POST /api/investigations/{investigation_id}/approve
POST /api/investigations/{investigation_id}/reject
POST /api/investigations/{investigation_id}/outcome
```

## Alerts

```http
GET /api/alerts
POST /api/alerts/{alert_id}/acknowledge
```

## Analytics

Potential aggregated endpoints:

```http
GET /api/analytics/overview
GET /api/analytics/risk-trends
GET /api/analytics/risk-matrix
GET /api/analytics/changes
GET /api/analytics/events
GET /api/analytics/geography
GET /api/analytics/sectors
GET /api/analytics/agencies
GET /api/analytics/cost
GET /api/analytics/schedule
GET /api/analytics/investigations
GET /api/analytics/interventions
GET /api/analytics/data-quality
GET /api/analytics/model-health
```

These are conceptual contracts. Reuse existing routes when equivalent data already exists.

## Monitoring status

```http
GET /api/system/monitoring-status
```

Suggested fields:

```json
{
  "status": "active",
  "last_sync_at": "...",
  "last_scan_at": "...",
  "next_scan_at": "...",
  "projects_monitored": 123,
  "stale_projects": 4
}
```

## Errors

Use structured errors:

```json
{
  "error": {
    "code": "PROJECT_NOT_FOUND",
    "message": "Project not found",
    "request_id": "..."
  }
}
```
