"""Deterministic & Explainable Similarity Engine for PAIMANA Projects.

Computes multi-dimensional similarity between a target project and candidate peers:
- Sector (exact match requirement for genuine infrastructure comparability)
- Implementing Agency (procurement & institutional comparability)
- State / Geography (terrain, land acquisition, and statutory context)
- Cost Band (log-scale capital expenditure comparability)
- Progress Stage (early, mid, late execution alignment)
- Planned Duration (schedule baseline scale)
- Project Age (elapsed duration alignment)

Exposes full audit lineage: matching dimensions, differing dimensions,
missing dimensions, and human-readable inclusion/exclusion explanations.
"""
from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple

from .schemas import SimilarityBreakdown

# Weights for multi-dimensional similarity (sum to 1.0)
DEFAULT_WEIGHTS = {
    "implementing_agency": 0.25,
    "cost_band": 0.20,
    "progress_stage": 0.20,
    "state": 0.15,
    "planned_duration": 0.10,
    "project_age": 0.10,
}


def get_cost_band(cost_cr: Optional[float]) -> str:
    """Categorizes project into standardized MoSPI IPMD cost bands."""
    if cost_cr is None or math.isnan(cost_cr) or cost_cr <= 0:
        return "Unknown"
    if cost_cr >= 1000.0:
        return "Mega (>1000Cr)"
    if cost_cr >= 500.0:
        return "Major (500-1000Cr)"
    return "Medium (150-500Cr)"


def get_progress_stage(progress_pct: Optional[float]) -> str:
    """Categorizes project into standardized execution stage brackets."""
    if progress_pct is None or math.isnan(progress_pct):
        return "Unknown"
    if progress_pct < 25.0:
        return "Early (<25%)"
    if progress_pct <= 75.0:
        return "Mid (25-75%)"
    return "Late (>75%)"


class ExplainableSimilarityEngine:
    """Deterministic, explainable similarity scoring between infrastructure projects."""

    def __init__(self, weights: Optional[Dict[str, float]] = None):
        self.weights = weights or DEFAULT_WEIGHTS
        # Normalize weights so they always sum to 1.0
        tot = sum(self.weights.values())
        self.weights = {k: v / tot for k, v in self.weights.items()}

    def compute_similarity(self, target: Dict[str, Any], candidate: Dict[str, Any]) -> SimilarityBreakdown:
        peer_code = str(candidate.get("project_code", "UNKNOWN")).strip()
        peer_name = str(candidate.get("project_name", "Unknown Project")).strip()

        matching_dims: List[str] = []
        differing_dims: List[str] = []
        missing_dims: List[str] = []
        dim_scores: Dict[str, float] = {}
        inclusion_reasons: List[str] = []
        exclusion_reasons: List[str] = []

        # 1. Sector Check (Hard Requirement for Infrastructure Monitoring)
        t_sector = str(target.get("sector") or "").strip().lower()
        c_sector = str(candidate.get("sector") or "").strip().lower()

        if not t_sector or not c_sector:
            missing_dims.append("sector")
            exclusion_reasons.append("Missing sector information")
            return SimilarityBreakdown(
                peer_code=peer_code, peer_name=peer_name, overall_similarity=0.0,
                dimension_scores={"sector": 0.0}, matching_dimensions=[],
                differing_dimensions=["sector"], missing_dimensions=missing_dims,
                inclusion_reasons=[], exclusion_reasons=exclusion_reasons,
                raw_attributes=candidate
            )

        if t_sector != c_sector:
            differing_dims.append("sector")
            exclusion_reasons.append(f"Sector mismatch: Target is '{target.get('sector')}', candidate is '{candidate.get('sector')}'")
            return SimilarityBreakdown(
                peer_code=peer_code, peer_name=peer_name, overall_similarity=0.0,
                dimension_scores={"sector": 0.0}, matching_dimensions=[],
                differing_dimensions=["sector"], missing_dimensions=missing_dims,
                inclusion_reasons=[], exclusion_reasons=exclusion_reasons,
                raw_attributes=candidate
            )

        matching_dims.append("sector")
        inclusion_reasons.append(f"Matching infrastructure sector: {target.get('sector')}")

        # 2. Implementing Agency Comparison
        t_agency = str(target.get("implementing_agency") or "").strip().lower()
        c_agency = str(candidate.get("implementing_agency") or "").strip().lower()
        if not t_agency or not c_agency:
            missing_dims.append("implementing_agency")
            dim_scores["implementing_agency"] = 0.5  # Neutral when missing
        elif t_agency == c_agency:
            dim_scores["implementing_agency"] = 1.0
            matching_dims.append("implementing_agency")
            inclusion_reasons.append(f"Identical implementing agency: {target.get('implementing_agency')}")
        elif t_agency in c_agency or c_agency in t_agency:
            dim_scores["implementing_agency"] = 0.8
            matching_dims.append("implementing_agency")
            inclusion_reasons.append(f"Related implementing agency: {candidate.get('implementing_agency')}")
        else:
            dim_scores["implementing_agency"] = 0.0
            differing_dims.append("implementing_agency")

        # 3. State / Regional Geography Comparison
        t_state = str(target.get("state") or "").strip().lower()
        c_state = str(candidate.get("state") or "").strip().lower()
        if not t_state or not c_state or t_state in ("nan", "none", "(-)", "multi-state", "multi state"):
            missing_dims.append("state")
            dim_scores["state"] = 0.5
        elif t_state == c_state:
            dim_scores["state"] = 1.0
            matching_dims.append("state")
            inclusion_reasons.append(f"Same state/geography: {target.get('state')}")
        else:
            dim_scores["state"] = 0.0
            differing_dims.append("state")

        # 4. Cost Band Comparison (Log-scale Ratio)
        t_cost = _safe_float(target.get("original_cost_cr") or target.get("revised_cost_cr"))
        c_cost = _safe_float(candidate.get("original_cost_cr") or candidate.get("revised_cost_cr"))
        if t_cost is None or c_cost is None or t_cost <= 0 or c_cost <= 0:
            missing_dims.append("cost_band")
            dim_scores["cost_band"] = 0.5
        else:
            t_band = get_cost_band(t_cost)
            c_band = get_cost_band(c_cost)
            ratio = min(t_cost, c_cost) / max(t_cost, c_cost)
            # Logarithmic proximity
            log_dist = abs(math.log10(t_cost) - math.log10(c_cost))
            cost_sim = max(0.0, 1.0 - (log_dist / 1.5))
            dim_scores["cost_band"] = cost_sim
            if t_band == c_band:
                matching_dims.append("cost_band")
                inclusion_reasons.append(f"Same cost band: {t_band} (Rs. {c_cost:.1f} Cr vs Rs. {t_cost:.1f} Cr)")
            else:
                differing_dims.append("cost_band")

        # 5. Progress Stage Comparison
        t_prog = _safe_float(target.get("physical_progress_pct"))
        c_prog = _safe_float(candidate.get("physical_progress_pct"))
        if t_prog is None or c_prog is None:
            missing_dims.append("progress_stage")
            dim_scores["progress_stage"] = 0.5
        else:
            t_stage = get_progress_stage(t_prog)
            c_stage = get_progress_stage(c_prog)
            prog_diff = abs(t_prog - c_prog)
            stage_sim = max(0.0, 1.0 - (prog_diff / 100.0))
            dim_scores["progress_stage"] = stage_sim
            if t_stage == c_stage:
                matching_dims.append("progress_stage")
                inclusion_reasons.append(f"Aligned execution stage: {t_stage} ({c_prog:.1f}% vs {t_prog:.1f}%)")
            else:
                differing_dims.append("progress_stage")

        # 6. Planned Duration Comparison
        t_dur = _safe_float(target.get("planned_duration_months"))
        c_dur = _safe_float(candidate.get("planned_duration_months"))
        if t_dur is None or c_dur is None or t_dur <= 0 or c_dur <= 0:
            missing_dims.append("planned_duration")
            dim_scores["planned_duration"] = 0.5
        else:
            dur_diff = abs(t_dur - c_dur)
            max_dur = max(t_dur, c_dur, 12.0)
            dur_sim = max(0.0, 1.0 - (dur_diff / max_dur))
            dim_scores["planned_duration"] = dur_sim
            if dur_sim >= 0.75:
                matching_dims.append("planned_duration")
                inclusion_reasons.append(f"Comparable planned duration: {c_dur:.0f} mo vs {t_dur:.0f} mo")
            else:
                differing_dims.append("planned_duration")

        # 7. Project Age Comparison
        t_age = _safe_float(target.get("project_age_months"))
        c_age = _safe_float(candidate.get("project_age_months"))
        if t_age is None or c_age is None or t_age < 0 or c_age < 0:
            missing_dims.append("project_age")
            dim_scores["project_age"] = 0.5
        else:
            age_diff = abs(t_age - c_age)
            max_age = max(t_age, c_age, 12.0)
            age_sim = max(0.0, 1.0 - (age_diff / max_age))
            dim_scores["project_age"] = age_sim
            if age_sim >= 0.75:
                matching_dims.append("project_age")
            else:
                differing_dims.append("project_age")

        # Calculate weighted overall similarity
        total_sim = 0.0
        for dim, w in self.weights.items():
            total_sim += dim_scores.get(dim, 0.5) * w

        overall_sim = float(max(0.0, min(1.0, total_sim)))

        return SimilarityBreakdown(
            peer_code=peer_code,
            peer_name=peer_name,
            overall_similarity=overall_sim,
            dimension_scores=dim_scores,
            matching_dimensions=matching_dims,
            differing_dimensions=differing_dims,
            missing_dimensions=missing_dims,
            inclusion_reasons=inclusion_reasons,
            exclusion_reasons=exclusion_reasons,
            raw_attributes=candidate,
        )


def _safe_float(val: Any) -> Optional[float]:
    if val is None or val == "" or str(val).strip() in ("(-)", "-", "nan", "None"):
        return None
    try:
        f = float(val)
        return None if math.isnan(f) else f
    except (TypeError, ValueError):
        return None
