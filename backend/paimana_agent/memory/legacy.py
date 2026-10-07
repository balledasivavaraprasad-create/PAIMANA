"""[LEGACY MEMORY PATH] Legacy Memory Interface for Backward Compatibility.

NOTE: This is a legacy compatibility module. The canonical institutional memory engine
is `PrecedentMemoryStore` in `paimana_agent.memory.precedent_memory` and `MemoryConsolidator`
in `paimana_agent.memory.memory_consolidator`, using the canonical `Precedent` model.
"""
from __future__ import annotations
import time
from typing import Optional, Any
from ..store import Store


def _month_label(ts: float) -> str:
    import datetime
    return datetime.datetime.fromtimestamp(ts, datetime.timezone.utc).strftime("%Y-%m")


def record_issue(store: Store, code: str, issue: str):
    store.add_issue(code, issue)


def record_intervention(store: Store, code: str, action: str) -> int:
    """Call when a human acts on an investigation's recommendation."""
    return store.add_intervention(code, action)


def record_outcome(store: Store, intervention_id: int, outcome: str):
    store.record_outcome(intervention_id, outcome)


def project_memory(store: Store, code: str) -> dict:
    """Assemble the full PROJECT MEMORY view."""
    hist = store.prediction_history(code, limit=24)
    risk_history = [{"month": _month_label(h["ts"]), "tier": h["tier"], "risk_score": round(h["risk_score"])}
                    for h in hist]
    issues = [i["issue"] for i in store.list_issues(code, limit=20)]
    interventions = [{"action": iv["action"], "outcome": iv.get("outcome"),
                      "ts": _month_label(iv["ts"])} for iv in store.list_interventions(code, limit=20)]
    return {"project_code": code, "risk_history": risk_history, "detected_issues": issues,
            "past_interventions": interventions}


def similar_past_pattern(store: Store, code: str) -> Optional[str]:
    """Cheap check for earlier score acceleration in this project's own history."""
    hist = store.prediction_history(code, limit=24)
    if len(hist) < 3:
        return None
    jumps = [(hist[i]["risk_score"] - hist[i - 1]["risk_score"]) for i in range(1, len(hist) - 1)]
    if any(j >= 8 for j in jumps):
        return ("this project has accelerated in risk score before and the trend later "
                "reversed" if hist[-1]["risk_score"] < max(h["risk_score"] for h in hist[:-1])
                else "this project has had at least one earlier period of fast-rising risk")
    return None


def _parse_outcome(raw_outcome: str) -> tuple[str, str, Optional[float]]:
    """Parse raw outcome string (JSON or prose) into (status, notes, risk_delta)."""
    import json
    if not raw_outcome:
        return "inconclusive", "", None
    try:
        data = json.loads(raw_outcome)
        if isinstance(data, dict):
            status = data.get("status", "inconclusive").lower()
            notes = data.get("notes") or data.get("action") or str(data)
            risk_delta = data.get("risk_delta")
            if risk_delta is not None:
                risk_delta = float(risk_delta)
                if status == "inconclusive":
                    status = "positive" if risk_delta < 0 else "negative" if risk_delta > 0 else "neutral"
            return status, notes, risk_delta
    except Exception:
        pass

    txt = raw_outcome.lower()
    pos_terms = ("progress resumed", "risk reduced", "recovered", "resolved", "completed successfully",
                 "bills frozen, progress resumed", "milestone achieved", "approved and on-track")
    neg_terms = ("failed", "stalled again", "unresolved", "remains stalled", "worsened",
                 "penalized", "breached", "did not prevent", "delay increased", "cost escalated further")

    if any(t in txt for t in pos_terms):
        return "positive", raw_outcome, -5.0
    elif any(t in txt for t in neg_terms):
        return "negative", raw_outcome, +5.0
    return "inconclusive", raw_outcome, None


def learn_from_interventions(store: Store, code: str, issue_types: Optional[list[str]] = None) -> dict:
    """Active learning loop evaluating past interventions and recorded outcomes."""
    prec = store.find_precedents(code=code, limit=10)
    peer_prec = store.find_precedents(code=None, limit=20)

    successful = []
    unsuccessful = []
    inconclusive = []

    all_records = prec + [p for p in peer_prec if p["project_code"] != code]
    for r in all_records:
        raw_out = r.get("outcome") or ""
        status, notes, risk_delta = _parse_outcome(raw_out)
        action = r.get("action") or ""
        is_same = (r.get("project_code") == code)
        summary = {
            "action": action,
            "outcome": raw_out,
            "status": status,
            "risk_delta": risk_delta,
            "is_same_project": is_same,
            "project_code": r.get("project_code")
        }
        if status == "positive":
            successful.append(summary)
        elif status == "negative":
            unsuccessful.append(summary)
        else:
            inconclusive.append(summary)

    guidance = None
    confidence_boost = 0
    if successful:
        top = successful[0]
        prefix = "On this project" if top["is_same_project"] else f"In peer project {top['project_code']}"
        guidance = f"{prefix}, past intervention '{top['action'][:70]}' had a positive outcome: '{top['outcome']}'."
        confidence_boost = 1
    elif unsuccessful:
        top = unsuccessful[0]
        prefix = "On this project" if top["is_same_project"] else f"In peer project {top['project_code']}"
        guidance = f"{prefix}, past intervention '{top['action'][:70]}' was followed by '{top['outcome']}'; recommend escalating to stronger administrative oversight."

    return {
        "n_precedents_evaluated": len(all_records),
        "successful_precedents": successful[:5],
        "unsuccessful_precedents": unsuccessful[:5],
        "inconclusive_precedents": inconclusive[:5],
        "confidence_boost": confidence_boost,
        "has_repeated_failure": bool(len(unsuccessful) >= 1 and not successful),
        "guidance": guidance
    }
