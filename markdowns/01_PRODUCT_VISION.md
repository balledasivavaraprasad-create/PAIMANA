# Product Vision

## One-line definition

InfraBuild-AI is a continuous infrastructure project intelligence platform that detects meaningful project changes, predicts emerging risk, compares projects with relevant peers, investigates possible causes, and supports evidence-backed intervention decisions.

## Core transformation

Traditional monitoring tends to answer:

> What is the current status?

InfraBuild-AI should answer:

> What changed, how unusual is it, what might explain it, what evidence supports that explanation, and what should an authorized decision-maker review next?

## Product loop

```text
OBSERVE
↓
Detect project state and data freshness
↓
DETECT CHANGE
↓
Identify meaningful state/risk/event changes
↓
PREDICT
↓
Estimate cost, schedule and composite risk
↓
EXPLAIN
↓
Show risk drivers and SHAP evidence
↓
COMPARE
↓
Place project against comparable peers
↓
INVESTIGATE
↓
Gather evidence through a stateful agent loop
↓
RECOMMEND
↓
Generate and validate candidate actions
↓
APPROVE
↓
Authorized human review
↓
ACT
↓
Notification / approved workflow automation
↓
MEASURE
↓
Observe post-action changes
↓
LEARN
↓
Update project and peer memory
↓
MONITOR AGAIN
```

## Primary users

### Portfolio / senior decision-maker
Needs a rapid view of where exposure and deterioration are concentrated.

### Project / monitoring officer
Needs detailed project context, change history, explanations, peer comparison and investigation evidence.

### Administrator
Needs monitoring health, notification status, model status, data quality, audit trail and access control.

### Analyst
Needs deep analytics, filtering, exports and historical comparison.

## Product promise

The system should never force the user to manually discover the problem before using the intelligence layer. A project may enter the system through scheduled synchronization, an external update, or a user edit; once current state is available, the monitoring loop should decide whether something changed enough to matter.

## Trust principles

1. Observed facts are explicitly distinguishable from predictions.
2. Predictions are explicitly distinguishable from hypotheses.
3. Hypotheses are explicitly distinguishable from verified causes.
4. Peer evidence is contextual evidence, not proof of causation.
5. Missing evidence must be visible.
6. Consequential action stays human-gated.
7. Empty data is better than fabricated precision.

## Product north-star statement

> **Turn project monitoring from retrospective reporting into proactive, evidence-backed intervention intelligence.**
