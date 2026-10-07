# Peer Intelligence Specification

## Purpose

A concerning project should be contextualized relative to projects that are sufficiently comparable.

## Peer cohort construction

Possible factors:

- sector
- project type
- implementing agency
- state/region
- cost band
- progress stage
- project age/duration
- completion horizon

Use configurable weights and explicit inclusion/exclusion rules.

## Peer quality

Expose:

- cohort size
- similarity quality
- data freshness
- missingness
- cohort consistency

Possible status:

```text
HIGH_QUALITY
MODERATE
WEAK
INSUFFICIENT
```

## Peer metrics

For target project compare:

- DPHIS
- DPHIS change
- cost overrun
- schedule slippage
- expenditure
- physical progress
- milestone performance
- event frequency
- risk trajectory

## Peer deviation

A peer deviation is a contextual anomaly, not a causal explanation.

Example:

```text
Target DPHIS: 72
Peer median: 46
Deviation: +26
```

## Peer-wide vs project-specific

Classify when enough evidence exists:

- project-specific anomaly
- cohort-wide deterioration
- sector/regional pattern
- unclear

## Peer interventions

Retrieve comparable interventions and observed outcomes.

Show:

- similarity
- intervention
- observed outcome
- time-to-outcome
- whether risk improved after the action

Do not claim that peer history proves an intervention will work for the target.

## Peer-aware agent tool family

Longer-term capabilities:

```text
peer_discovery
peer_benchmark
peer_trajectory
peer_outlier
peer_event_analysis
peer_intervention_history
peer_outcome_history
```

## UI

The key visual should communicate:

> **How different is this project from projects like it?**

Do not reduce peer intelligence to a “Similar Projects” list.
