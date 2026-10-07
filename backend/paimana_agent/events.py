"""Risk-event engine.

Deliberately layered ON TOP of the existing tier/alert policy in agent.py, not a
replacement for it (see PAIMANA architecture review, problem #4):

  - Risk SEVERITY (Low/Medium/High)      -> unchanged, from agent.tier()
  - Project ALERT BOUNDARY               -> a per-project threshold (this module)
  - EVENT TYPES                          -> THRESHOLD_CROSSED / RISK_ACCELERATING /
                                             MILESTONE_DELAYED / PROGRESS_STALLED /
                                             COST_PROGRESS_MISMATCH

Events are what the scheduler/on-change trigger feed into the event log and what
decides whether the investigator agent (investigator.py) wakes up. They are
independent of whether a classic tier-based alert fires.
"""
from __future__ import annotations
import math, re
from typing import Optional

from . import features as F

EVENT_TYPES = (
    "THRESHOLD_CROSSED", "RISK_ACCELERATING", "MILESTONE_DELAYED",
    "PROGRESS_STALLED", "COST_PROGRESS_MISMATCH",
)


def _ok(x):
    return x is not None and not (isinstance(x, float) and math.isnan(x))


def detect_events(res: dict, feats: dict, prev_record: Optional[dict], last_pred: Optional[dict],
                   threshold: float, cfg: dict) -> list[dict]:
    """res: agent.on_project_saved's result dict so far (predictions/tier/score).
    feats: this evaluation's engineered features. prev_record: the previous stored
    snapshot's RAW project record (same shape store.previous_snapshot returns), used
    to detect milestone-date slips, or None. last_pred: previous row from
    Store.last_prediction (risk_score/tier history), or None."""
    ev = []
    score = res["risk_score"]
    accel_jump = cfg.get("acceleration_jump", 8)
    gap_threshold = cfg.get("cost_progress_gap", 15)
    stall_velocity = cfg.get("stall_velocity_pct_per_month", 0.5)

    prev_score = last_pred["risk_score"] if last_pred else None
    if prev_score is not None:
        if prev_score < threshold <= score:
            ev.append(dict(type="THRESHOLD_CROSSED", severity="High",
                           message=f"risk score crossed this project's alert threshold ({threshold:.0f}): "
                                   f"{prev_score:.0f} -> {score:.0f}"))
    elif score >= threshold:
        ev.append(dict(type="THRESHOLD_CROSSED", severity="High",
                       message=f"first evaluation already above this project's alert threshold "
                               f"({score:.0f} >= {threshold:.0f})"))

    if prev_score is not None and (score - prev_score) >= accel_jump:
        ev.append(dict(type="RISK_ACCELERATING", severity="Medium",
                       message=f"risk score rising quickly: +{score - prev_score:.0f} points since last evaluation"))

    cur_slip = feats.get("schedule_slippage_months", 0.0) or feats.get("completion_delay_months", 0.0)
    if prev_record is not None:
        prev_slip = F.slippage_months(prev_record) or 0.0
        pushed = cur_slip - prev_slip
        if pushed > 0:
            ev.append(dict(type="MILESTONE_DELAYED", severity="Medium",
                           message=f"revised completion date pushed back {pushed:.0f} more month(s) since the last update"))
        elif _ok(feats.get("_remaining_duration_months")) and feats["_remaining_duration_months"] < 0:
            ev.append(dict(type="MILESTONE_DELAYED", severity="Low",
                           message="revised completion date is already in the past"))
    elif cur_slip > 0:
        ev.append(dict(type="MILESTONE_DELAYED", severity="Medium",
                       message=f"completion date already deferred by {cur_slip:.0f} month(s) from original sanctioned target"))

    vel = feats.get("progress_velocity_pct_per_month")
    if _ok(vel) and vel <= stall_velocity and feats.get("physical_progress_pct", 0) < 95:
        ev.append(dict(type="PROGRESS_STALLED", severity="Medium",
                       message=f"physical progress moved only {vel:.1f} pts/month since the last update"))

    gap = feats.get("progress_expenditure_gap_pct")
    if _ok(gap) and gap > gap_threshold:
        ev.append(dict(type="COST_PROGRESS_MISMATCH", severity="Medium",
                       message=f"spending is ahead of physical progress by {gap:.0f} points"))

    return ev


def worth_investigating(events: list[dict], feats: Optional[dict] = None, res: Optional[dict] = None) -> bool:
    """Intelligent decision engine on which event patterns warrant activating the investigator agent.

    Triggers on:
      1. Critical single events: THRESHOLD_CROSSED, RISK_ACCELERATING
      2. Compound events: 2 or more concurrent events (e.g. PROGRESS_STALLED + COST_PROGRESS_MISMATCH)
      3. Severe single anomalies:
         - Severe cost/progress mismatch (spending ahead by >= 20 pts)
         - Stalled progress on a project with substantial work remaining (<80% done, velocity <= 0.2)
         - Severe milestone delay (pushed back >= 6 months)
      4. High financial exposure: mega-project (>= Rs 1,000 cr) with ANY active event
    """
    if not events:
        return False

    types = {e["type"] for e in events}

    # 1. Critical boundary crossing or rapid escalation
    if any(t in ("THRESHOLD_CROSSED", "RISK_ACCELERATING") for t in types):
        return True

    # 2. Compound events (two or more concurrent anomalies)
    if len(events) >= 2:
        return True

    # 3. High financial exposure: mega-project with any operational event
    if feats and feats.get("is_mega_project"):
        return True

    # 4. Severe single anomalies
    if feats:
        gap = feats.get("progress_expenditure_gap_pct")
        if _ok(gap) and gap >= 15.0:
            return True
        vel = feats.get("progress_velocity_pct_per_month")
        prog = feats.get("physical_progress_pct", 0)
        ratio = feats.get("age_to_planned_ratio")
        if _ok(vel) and vel <= 0.2 and prog < 80.0:
            return True
        if _ok(ratio) and ratio > 0.8 and prog < 25.0:
            return True

    for e in events:
        msg = e.get("message", "")
        if e["type"] == "MILESTONE_DELAYED":
            m_push = re.search(r"(\d+)\s+month", msg)
            if m_push and int(m_push.group(1)) >= 6:
                return True

    return False
