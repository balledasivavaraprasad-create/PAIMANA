# Project Detail / Intelligence Page

## Purpose

This is the deepest operational page for one project.

The page should answer:

> What is happening with this project, what changed, how unusual is it, what evidence exists, and what can be reviewed next?

## Header

Show:

- project name
- project code
- ministry
- sector
- implementing agency
- state
- monitoring status
- last observed timestamp

Primary actions:

- Investigate
- View history
- Review alerts

## Hero intelligence strip

Show four major metrics:

1. DPHIS
2. DPHIS change
3. predicted cost overrun
4. predicted schedule slippage

Make the distinction between current value and predicted value visually obvious.

## Section: What changed?

Before → current comparison.

Dimensions:

- progress
- expenditure
- cost
- completion date
- milestones
- DPHIS

Explain the detected event(s).

## Section: Why is risk changing?

SHAP visualization plus concise evidence-backed interpretation.

Separate:

- model driver
- observed metric
- interpretation

Do not label SHAP as causal proof.

## Section: Peer context

Show:

- peer cohort size
- similarity quality
- peer median DPHIS
- target DPHIS
- peer percentile if meaningful
- target deviation
- peer trajectory

Use a compact scatter/distribution/trajectory visual.

### Peer interpretation

Possible statuses:

- Similar to peer cohort
- Project-specific outlier
- Cohort-wide deterioration
- Insufficient peer evidence

## Section: Investigation

Show:

- trigger
- current hypotheses
- confidence
- evidence count
- contradictions
- evidence gaps
- tools used
- current status

Open the complete investigation drawer/page from here.

## Section: Recommendations

Show candidate actions with:

- evidence basis
- expected benefit if available
- authority required
- uncertainty
- precedent references
- validation state
- approval state

## Section: Intervention

If approved/executed:

- action
- approval timestamp
- execution status
- response time
- observed outcome
- before/after DPHIS
- before/after progress
- outcome notes

Use wording like “Observed change after intervention,” not unsupported causal claims.

## Section: Timeline

Unified timeline for:

- snapshots
- events
- alerts
- investigations
- approvals
- interventions
- outcomes

## Section: Data quality

Show missing/stale/low-confidence inputs.
