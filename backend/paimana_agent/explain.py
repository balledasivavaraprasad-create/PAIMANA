"""Explain WHY a project is flagged.

Deterministic rule-based drivers are always produced (auditable, no hallucination).
An optional local open-source LLM (Ollama) only rewrites those facts into a short
briefing; if it is off/unreachable we fall back to the template.
"""
from __future__ import annotations
import json, logging, math, urllib.request

log = logging.getLogger(__name__)


def _ok(x):
    return x is not None and not (isinstance(x, float) and math.isnan(x))


def drivers(p: dict, f: dict, pred: dict) -> list[str]:
    d = []
    if _ok(f.get("age_to_planned_ratio")) and f["age_to_planned_ratio"] > 1.0:
        d.append(f"project is at {f['age_to_planned_ratio']*100:.0f}% of its planned duration "
                 f"({f['project_age_months']:.0f} of {f['planned_duration_months']:.0f} months)")
    if f["progress_expenditure_gap_pct"] > 15:
        d.append(f"spending is ahead of physical progress by {f['progress_expenditure_gap_pct']:.0f} points "
                 f"({f['physical_progress_pct']:.0f}% built vs {f['expenditure_original_cost_pct']:.0f}% of original cost spent)")
    if f["expenditure_original_cost_pct"] > 100:
        d.append(f"expenditure already exceeds original cost ({f['expenditure_original_cost_pct']:.0f}%)")
    if f["schedule_slippage_months"] > 0:
        d.append(f"completion date already pushed {f['schedule_slippage_months']:.0f} months")
    if f["cost_overrun_pct"] > 0:
        d.append(f"cost already revised up by {f['cost_overrun_pct']:.0f}%")
    if _ok(f.get("_remaining_duration_months")) and f["_remaining_duration_months"] < 0:
        d.append(f"revised completion date is {abs(f['_remaining_duration_months']):.0f} months in the past")
    if _ok(f.get("progress_velocity_pct_per_month")) and f["progress_velocity_pct_per_month"] <= 0.05 and f["physical_progress_pct"] < 95:
        d.append("physical progress has stalled since the last update")
    if f["is_mega_project"]:
        d.append("mega project (>= Rs 1,000 cr): small percentage slips carry large rupee impact")
    return d[:5]


def template_summary(p, pred, ds):
    head = (f"{p['project_name']} ({p['project_code']}, {p.get('ministry','')}) is rated {pred['tier'].upper()} risk "
            f"with a score of {pred['risk_score']:.0f}/100. Model estimates: cost overrun {pred['cost_overrun_pct']:+.1f}% "
            f"and schedule slip of {pred['slippage_months']:.0f} months.")
    body = ("Main signals: " + "; ".join(ds) + ".") if ds else "No single dominant signal in the CUF fields; score is driven by the overall pattern."
    return head + " " + body


def llm_summary(cfg: dict, p, pred, ds, fallback: str) -> str:
    """Optional: local Ollama model rewrites the facts. Never invents numbers (facts are in the prompt)."""
    if not cfg.get("enabled"):
        return fallback
    prompt = ("You are an infrastructure project-monitoring analyst. Write a 3-sentence alert briefing for a ministry "
              "administrator using ONLY these facts. Do not add numbers.\n" + json.dumps(
                  {"project": p["project_name"], "ministry": p.get("ministry"), "tier": pred["tier"],
                   "risk_score": round(pred["risk_score"]), "cost_overrun_pct": round(pred["cost_overrun_pct"], 1),
                   "slippage_months": round(pred["slippage_months"]), "drivers": ds}))
    try:
        req = urllib.request.Request(cfg.get("url", "http://localhost:11434/api/generate"),
                                     data=json.dumps({"model": cfg.get("model", "llama3.1:8b"), "prompt": prompt, "stream": False}).encode(),
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=cfg.get("timeout", 20)) as r:
            txt = json.loads(r.read())["response"].strip()
        return txt or fallback
    except Exception as ex:
        log.info("LLM summary unavailable (%s); using template", ex)
        return fallback
