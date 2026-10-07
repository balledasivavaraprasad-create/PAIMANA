# Existing Agent Integration Contract

## Current agent capabilities to preserve

The current agent package contains a substantial monitoring/investigation framework including:

- project validation and feature engineering
- three predictive models
- SHAP enrichment
- DPHIS/risk scoring
- event detection
- scheduled monitoring
- snapshot/history handling
- peer intelligence
- stateful investigation
- evidence normalization
- hypotheses
- contradictions
- convergence/termination
- memory/precedent
- recommendation generation/validation
- human approval
- outbox/retry mechanisms
- optional Langfuse instrumentation
- optional n8n integration

## Integration rule

Treat the agent as a domain engine, not as the frontend API.

Preferred:

```text
React
 ↓
Main backend API
 ↓
Agent adapter/service
 ↓
PAIMANA agent
```

Avoid:

```text
Browser
 ↓
Standalone agent stdlib HTTP server
```

## Result normalization

The frontend should receive concise domain objects rather than Python-specific structures.

Example:

```text
risk_score
risk_tier
risk_change
prediction_summary
shap_drivers
events
peer_context
investigation_summary
recommendations
monitoring_status
```

## Important honesty rule

The current agent has advanced architecture but some areas are still developmental or heuristic. Do not expose labels such as “verified cause” unless the backend actually satisfies the relevant evidence conditions.

## Long-running investigations

Investigation execution should be asynchronous where possible.

Frontend should show:

```text
queued
→ investigating
→ awaiting decision
→ concluded
```

rather than blocking a page request for the entire investigation.

## Domain event example

When DPHIS crosses a configured threshold:

```text
MonitoringAgent
→ event engine
→ alert event
→ investigation trigger
→ notification workflow
```

Do not duplicate threshold rules in React.
