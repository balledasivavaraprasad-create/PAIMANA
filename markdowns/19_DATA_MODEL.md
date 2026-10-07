# Data Model

## Core entities

### Project

Stable identity and current canonical metadata.

### ProjectSnapshot

Point-in-time state used for monitoring.

Recommended:

```text
snapshot_id
project_id
observed_at
report_period
source
source_record_id
snapshot_hash
raw_payload_reference
quality_status
```

### Prediction

```text
prediction_id
project_id
snapshot_id
model_version
cost_overrun_prediction
schedule_slippage_prediction
risk_score
combined_crosscheck
created_at
```

### Event

```text
event_id
project_id
snapshot_id
event_type
severity
trigger_metrics
created_at
```

### Investigation

```text
investigation_id
project_id
trigger_event_id
status
confidence
started_at
completed_at
termination_reason
```

### Evidence

```text
evidence_id
investigation_id
source_type
source_id
observed_at
freshness
content
reliability
role
```

### Hypothesis

```text
hypothesis_id
investigation_id
statement
status
support_score
contradiction_score
supporting_evidence_ids
contradicting_evidence_ids
falsification_condition
```

### Recommendation

```text
recommendation_id
investigation_id
statement
evidence_ids
authority_required
validation_status
approval_status
```

### Intervention

```text
intervention_id
recommendation_id
approved_by
approved_at
execution_status
executed_at
```

### InterventionOutcome

```text
outcome_id
intervention_id
recorded_at
before_metrics
after_metrics
observed_change
outcome_status
notes
```

### PeerAnalysis

```text
peer_analysis_id
project_id
cohort_id
cohort_size
cohort_quality
matching_factors
benchmarks
deviations
trajectory_summary
```

## Data lineage

Every important derived object should be traceable back to a snapshot and model/tool/source where possible.

## Null semantics

Do not use zero to mean “unknown”.

Use `null` / explicit availability status.
