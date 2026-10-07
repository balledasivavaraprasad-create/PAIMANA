# PAIMANA Agent v2 — what changed and why

This is the implementation of the architecture review's recommendations. Per the
review's own conclusion, **90% of the original monitoring engine is unchanged** —
validation, feature engineering, the three models, the tier/alert policy, and the
deterministic-first explanation layer are all exactly as before. What's new sits
on top of it.

| # | Problem (review) | What was added | Where |
|---|---|---|---|
| 1 | Not actually continuous | Periodic re-scan trigger alongside the existing on-change trigger | `scheduler.py`, `MonitoringAgent.run_scheduled_scan()` |
| 2 | Not very agentic | Supervisor agent (History → Peer → RootCause → Recommendation), evidence-backed, human-approval-gated | `investigator.py` |
| 3 | Models aren't chained | Left as-is (independent models + cross-check score) — the review agreed this design is fine, just needs accurate framing in the pitch | *(no code change)* |
| 4 | Global thresholds only | Per-project alert threshold + THRESHOLD_CROSSED/RISK_ACCELERATING/MILESTONE_DELAYED/PROGRESS_STALLED/COST_PROGRESS_MISMATCH event taxonomy, layered on top of (not replacing) the tier/alert policy | `events.py`, `Store.set_threshold()`/`get_threshold()` |
| 5 | Explanation isn't SHAP | Real SHAP attributions on the risk model, feeding the existing rule-based drivers rather than replacing them | `shap_explain.py` |
| 6 | ML limitations (leakage, unstable cost model, unvalidated alert policy) | No code fixes this — it needs retraining with time-based forward evaluation, which is outside what a wrapper package can do. Documented here so it isn't silently dropped: **do not present these as production-accurate models in the pitch.** Say "prototype predictive models; the monitoring/agentic layer is what's production-shaped." | *(needs a retraining pass on your side — see README's original `LEAKY_FIELDS` note in `features.py`)* |
| 7 | No project memory / no learning loop | Risk-history + detected-issues + interventions/outcomes view, and a write path so an approved recommendation's real-world outcome gets recorded | `memory.py`, `Store` (`issues`, `interventions` tables) |

Signature feature ("Why did risk change?") is the SHAP lines attached to `res["why_changed"]`
and appended to every alert message in `agent._send_alert`.

## New API surface (`server.py`)

```
GET  /projects/<code>/memory              risk history + issues + interventions
GET  /events?project=<code>               event log
GET  /investigations?project=<code>       investigation reports (pending_approval / approved)
POST /investigations/<id>/approve         human sign-off -> records an intervention
POST /investigations/<id>/outcome         close the loop: {"intervention_id":, "outcome":}
PUT  /projects/<code>/threshold           {"threshold": 62}
POST /scan                                run one scheduled-scan pass now, body = [project, ...]
```

## Design choices worth knowing about

- **No LangGraph dependency.** `investigator.py` implements the Supervisor pattern
  as plain Python functions in named agent roles. The seams are kept so any one step
  (History/Peer/RootCause/Recommendation) could be swapped for a LangGraph node or an
  LLM-driven planner later without touching the others — but the portfolio project
  doesn't need the extra dependency to demonstrate the pattern.
- **Peer evidence is self-sourced.** There's no external project catalogue wired in,
  so the Peer agent looks across every other project *this agent has itself
  monitored* in the same sector/cost band. It starts thin and gets more useful the
  longer the engine runs — that's an honest characteristic to mention in a demo, not
  a bug to hide.
- **SHAP is an enrichment, not a hard dependency.** It needs a handful of real
  feature rows as a background sample (there's no raw training data shipped with the
  models, only `reference_stats.json`'s summary stats), so the agent builds a small
  rolling background from projects it evaluates and quietly falls back to the
  original rule-based drivers until it has enough (5+ rows). If `shap` isn't
  installed at all, same graceful fallback.
- **Investigations never auto-execute.** `investigate()` writes a
  `pending_approval` report. Nothing calls out to n8n or notifies anyone from
  inside it — that's deliberately left as the next integration point once you wire
  a real n8n webhook in, matching "Human approval -> n8n" in the review's diagram.

## Tests

- `tests/test_agent.py` — original suite, unmodified, still passes.
- `tests/test_agent_v2.py` — new: exercises per-project thresholds, the event
  engine, the investigator (with real peer evidence), project memory, the
  intervention/outcome loop, and the scheduler, against the real models.
