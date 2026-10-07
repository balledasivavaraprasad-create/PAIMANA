"""Turn a raw project record (CUF fields) into the model feature row.

Formulas were verified against Paimana.csv (max error ~0.1 month, from the
portal's fractional-month rounding). Where the training data behaves in a way
that looks like leakage, we reproduce it on purpose so inputs match training,
and document it in `LEAKY_FIELDS`.
"""
from __future__ import annotations
import math, re
from datetime import date
from typing import Optional
import numpy as np

REQUIRED = ["project_code", "project_name", "ministry", "sector", "implementing_agency",
            "original_cost_cr", "cumulative_expenditure_cr", "physical_progress_pct",
            "original_completion_date"]
DATE_FIELDS = ["approval_date", "start_date", "original_completion_date", "revised_completion_date"]
_MMYYYY = re.compile(r"^(0?[1-9]|1[0-2])/(\d{4})$")
_YYYYMM = re.compile(r"^(\d{4})-(0?[1-9]|1[0-2])(-\d{2})?$")

# Fields whose value depends on the *outcome* being predicted (see README).
LEAKY_FIELDS = {
    "time model / risk model": "remaining_work_rate uses remaining_duration_months, which with age and planned duration algebraically encodes slippage",
    "cost model": "progress_expenditure_gap_pct uses expenditure vs REVISED cost when a revision exists",
}


class ValidationError(ValueError):
    pass


def month_index(s: Optional[str]) -> Optional[int]:
    """'MM/YYYY' or 'YYYY-MM-DD' -> absolute month number. '(-)' / '' / None -> None."""
    if s is None:
        return None
    s = str(s).strip()
    if s in ("", "(-)", "-", "nan", "None"):
        return None
    m = _MMYYYY.match(s)
    if m:
        return int(m.group(2)) * 12 + int(m.group(1))
    m2 = _YYYYMM.match(s)
    if m2:
        return int(m2.group(1)) * 12 + int(m2.group(2))
    raise ValidationError(f"date '{s}' must be MM/YYYY or YYYY-MM-DD")


def report_index(report_month: Optional[str]) -> int:
    """'YYYY-MM' (default: today) -> absolute month number."""
    if not report_month:
        t = date.today()
        return t.year * 12 + t.month
    m = re.match(r"^(\d{4})-(\d{2})$", str(report_month))
    if not m:
        raise ValidationError("report_month must be YYYY-MM")
    return int(m.group(1)) * 12 + int(m.group(2))


def _num(v, name, required=False):
    if v is None or (isinstance(v, str) and v.strip() in ("", "(-)")) or (isinstance(v, float) and math.isnan(v)):
        if required:
            raise ValidationError(f"{name} is required")
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        raise ValidationError(f"{name} must be a number, got {v!r}")


def validate(p: dict) -> dict:
    """Validate/normalise a project record. Returns a cleaned copy; raises ValidationError."""
    errs = []
    for k in REQUIRED:
        if p.get(k) in (None, ""):
            errs.append(f"{k} is required")
    if errs:
        raise ValidationError("; ".join(errs))
    q = dict(p)
    try:
        for k in ("original_cost_cr", "cumulative_expenditure_cr", "physical_progress_pct"):
            q[k] = _num(p.get(k), k, required=True)
        q["revised_cost_cr"] = _num(p.get("revised_cost_cr"), "revised_cost_cr")
        for k in DATE_FIELDS:
            month_index(p.get(k))
    except ValidationError as e:
        raise
    if q["original_cost_cr"] <= 0:
        errs.append("original_cost_cr must be > 0")
    if q["cumulative_expenditure_cr"] < 0:
        errs.append("cumulative_expenditure_cr must be >= 0")
    if not 0 <= q["physical_progress_pct"] <= 100:
        errs.append("physical_progress_pct must be between 0 and 100")
    if q["revised_cost_cr"] is not None and q["revised_cost_cr"] <= 0:
        errs.append("revised_cost_cr must be > 0 when given")
    if errs:
        raise ValidationError("; ".join(errs))
    return q


def cost_overrun_pct(p: dict) -> float:
    rc, oc = p.get("revised_cost_cr"), p["original_cost_cr"]
    return 0.0 if rc is None else (rc - oc) / oc * 100.0


def slippage_months(p: dict) -> Optional[float]:
    r, o = month_index(p.get("revised_completion_date")), month_index(p.get("original_completion_date"))
    return None if r is None or o is None else float(r - o)


def build_features(p: dict, ref: dict, prev: Optional[dict] = None, report_month: Optional[str] = None) -> dict:
    """Return every engineered feature any of the three models may ask for.

    `prev` is the project's most recent snapshot from an EARLIER report month
    (same record shape) used for the monthly-change features; None -> NaN.
    """
    nan = float("nan")
    R = report_index(report_month or p.get("report_month"))
    S, O = month_index(p.get("start_date")), month_index(p.get("original_completion_date"))
    V = month_index(p.get("revised_completion_date"))

    oc, exp, prog = p["original_cost_cr"], p["cumulative_expenditure_cr"], p["physical_progress_pct"]
    rc = p.get("revised_cost_cr")

    age = float(R - S) if S is not None else nan
    planned = float(O - S) if (S is not None and O is not None) else nan
    remaining_dur = float(V - R) if V is not None else nan
    slip = slippage_months(p)
    slip_filled = 0.0 if slip is None else slip
    co = cost_overrun_pct(p)

    exp_orig_pct = exp / oc * 100.0
    # Reproduces the portal/training definition: uses revised cost once revised.
    exp_base_pct = (exp / rc * 100.0) if rc else exp_orig_pct
    gap = exp_base_pct - prog
    remaining_prog = 100.0 - prog

    # monthly change features (need an earlier-month snapshot)
    d_prog = d_exp = vel = exp_growth = nan
    if prev is not None and prev.get("report_index") is not None and prev["report_index"] < R:
        months = R - prev["report_index"]
        d_prog = prog - prev["physical_progress_pct"]
        d_exp = exp - prev["cumulative_expenditure_cr"]
        vel = d_prog / months
        if prev["cumulative_expenditure_cr"] > 0:
            exp_growth = d_exp / prev["cumulative_expenditure_cr"] * 100.0

    f = {
        "original_cost_cr": oc, "cumulative_expenditure_cr": exp, "physical_progress_pct": prog,
        "expenditure_original_cost_pct": exp_orig_pct, "project_age_months": age,
        "planned_duration_months": planned,
        "monthly_progress_change_pct": d_prog, "monthly_expenditure_change_cr": d_exp,
        "progress_velocity_pct_per_month": vel, "expenditure_growth_pct": exp_growth,
        "progress_expenditure_gap_pct": gap, "remaining_progress_pct": remaining_prog,
        "state_freq": ref["state_freq"].get(p.get("state"), 0.0),
        "agency_freq": ref["agency_freq"].get(p.get("implementing_agency"), 0.0),
        "ministry": p.get("ministry") or "Unknown", "sector": p.get("sector") or "Unknown",
        "schedule_slippage_months": slip_filled, "cost_overrun_pct": co,
        "has_time_slippage": float(slip_filled > 0), "has_cost_overrun": float(co > 0),
    }
    f["age_to_planned_ratio"] = float(np.clip(age / (planned + 1), -5, 20)) if not math.isnan(age + planned) else nan
    f["burn_rate_ratio"] = float(np.clip(exp_orig_pct / (prog + 1), -5, 50))
    f["is_mega_project"] = float(oc >= 1000)
    f["log_orig_cost"] = float(np.log1p(max(oc, 0)))
    f["log_expenditure"] = float(np.log1p(max(exp, 0)))
    f["cost_per_pct_progress"] = float(np.clip(exp / (prog + 1), 0, 10000))
    rd = max(remaining_dur, 1.0) if not math.isnan(remaining_dur) else nan
    f["remaining_work_rate"] = float(np.clip(remaining_prog / (rd + 1), 0, 100)) if not math.isnan(rd) else nan
    f["_remaining_duration_months"] = remaining_dur   # diagnostics only, not a model input
    return f
