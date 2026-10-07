# Agentic Investigation UI

## Purpose

Expose the investigation as a trustworthy, inspectable process rather than a chat transcript.

## Investigation states

```text
TRIGGERED
INVESTIGATING
EVIDENCE_COLLECTION
HYPOTHESIS_REVIEW
READY_FOR_DECISION
PENDING_APPROVAL
APPROVED
REJECTED
EXECUTED
OUTCOME_RECORDED
CONCLUDED_INSUFFICIENT_EVIDENCE
FAILED
```

## Investigation header

Show:

- investigation ID
- project
- trigger event
- started at
- current status
- confidence level
- decision readiness

## Evidence board

Group evidence into:

- observed facts
- derived signals
- supporting evidence
- contradicting evidence
- unresolved gaps

Every evidence item should show:

- source/tool
- timestamp
- data freshness if available
- confidence/reliability indicator

## Hypothesis board

Each hypothesis card:

- statement
- support level
- supporting evidence count
- contradicting evidence count
- status
- discriminating evidence needed
- falsification condition

Do not present normalized heuristic scores as statistically calibrated probabilities.

## Agent activity timeline

Example:

```text
14:02  Investigation triggered
14:02  Loaded baseline state
14:03  Built peer cohort — 18 projects
14:03  Detected target deviation
14:04  Selected milestone_audit
14:04  Observation returned
14:05  Hypothesis H2 weakened
14:05  Selected financial_velocity
14:06  Evidence gap remains
14:06  Investigation concluded
```

## Tool detail

Show tool calls progressively.

Default UI should show human-readable names.

Technical users may expand to inspect inputs/outputs.

Never expose credentials or sensitive transport data.

## “Why did the agent stop?”

Every investigation should explain one of:

- evidence sufficient
- decision readiness reached
- budget exhausted
- repeated evidence / diminishing returns
- unresolved contradiction
- source unavailable
- confidence below decision threshold

## Recommendation section

Show multiple candidates when available.

For each:

- recommendation
- evidence basis
- likely objective
- risks/constraints
- required authority
- precedent used
- validation status

## Human approval

Approval UI should clearly show:

- what is being approved
- why it was proposed
- what evidence supports it
- what is uncertain
- what automation will happen after approval

Never blur “recommendation” and “approved action”.

## Agent observability

Do not expose every internal Langfuse/span field in the normal UI. Provide a concise execution trace, with technical detail available in an advanced drawer.
