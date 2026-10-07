"""Modular Feature-Specific Similarity Engine for Peer Discovery.

Implements feature-specific distance metrics:
- Log-scale distance for project cost (scale-invariant relative differences)
- Normalized numerical distance for project duration
- Stage-aware distance for physical execution progress
- Taxonomy and categorical compatibility for agency, project type, and state
- Strategy-conditioned dimension weighting and calibrated scoring
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from ..schemas import SimilarityBreakdown
from .strategy_registry import PeerStrategyDefinition


class ModularSimilarityEngine:
    """Computes explainable, calibrated similarity between target and candidate projects."""

    # Region clusters for Indian states
    STATE_REGIONS: Dict[str, str] = {
        "delhi": "NORTH", "haryana": "NORTH", "punjab": "NORTH", "himachal pradesh": "NORTH",
        "uttarakhand": "NORTH", "uttar pradesh": "NORTH", "rajasthan": "NORTH", "jammu & kashmir": "NORTH",
        "maharashtra": "WEST", "gujarat": "WEST", "goa": "WEST",
        "tamil nadu": "SOUTH", "karnataka": "SOUTH", "kerala": "SOUTH", "andhra pradesh": "SOUTH", "telangana": "SOUTH",
        "west bengal": "EAST", "odisha": "EAST", "bihar": "EAST", "jharkhand": "EAST",
        "assam": "NORTHEAST", "meghalaya": "NORTHEAST", "arunachal pradesh": "NORTHEAST",
        "madhya pradesh": "CENTRAL", "chhattisgarh": "CENTRAL",
    }

    def compute_similarity(
        self,
        target_project: Dict[str, Any],
        candidate: Dict[str, Any],
        strategy: PeerStrategyDefinition,
    ) -> SimilarityBreakdown:
        """Computes multi-dimensional similarity conditioned on the investigation strategy."""
        dimension_scores: Dict[str, float] = {}
        matching_dimensions: List[str] = []
        differing_dimensions: List[str] = []
        missing_dimensions: List[str] = []
        inclusion_reasons: List[str] = []
        exclusion_reasons: List[str] = []

        total_weight_evaluated = 0.0
        weighted_sum = 0.0

        for dim, weight in strategy.dimension_weights.items():
            score, reason = self._compute_dimension_score(target_project, candidate, dim)
            if score is None:
                missing_dimensions.append(dim)
                # Fallback to neutral 0.50 score with penalty
                score = 0.50
                reason = f"Missing attribute '{dim}' (neutral fallback applied)"

            dimension_scores[dim] = round(score, 4)
            weighted_sum += score * weight
            total_weight_evaluated += weight

            if score >= 0.75:
                matching_dimensions.append(dim)
                inclusion_reasons.append(reason)
            else:
                differing_dimensions.append(dim)
                exclusion_reasons.append(reason)

        overall_score = weighted_sum / total_weight_evaluated if total_weight_evaluated > 0 else 0.50

        cand_code = str(candidate.get("project_code") or candidate.get("canonical_project_id", "")).strip()
        cand_name = str(candidate.get("project_name", "")).strip()

        return SimilarityBreakdown(
            peer_code=cand_code,
            peer_name=cand_name,
            overall_similarity=round(overall_score, 4),
            dimension_scores=dimension_scores,
            matching_dimensions=matching_dimensions,
            differing_dimensions=differing_dimensions,
            missing_dimensions=missing_dimensions,
            inclusion_reasons=inclusion_reasons,
            exclusion_reasons=exclusion_reasons,
            raw_attributes=dict(candidate),
        )

    def _compute_dimension_score(
        self,
        target: Dict[str, Any],
        candidate: Dict[str, Any],
        dimension: str,
    ) -> Tuple[Optional[float], str]:
        """Computes similarity for an individual dimension using specialized formulas."""
        if dimension == "original_cost":
            t_cost = _to_float(target.get("original_cost_cr") or target.get("original_cost") or target.get("cost"))
            c_cost = _to_float(candidate.get("original_cost_cr") or candidate.get("original_cost") or candidate.get("cost"))
            if t_cost is None or c_cost is None or t_cost <= 0 or c_cost <= 0:
                return None, "Cost data unavailable"
            # Log-scale distance: 1.0 - min(1.0, |ln(t) - ln(c)| / ln(10))
            # Ratio of 2.0 gives ~0.70 similarity; ratio of 10.0 gives ~0.0
            log_dist = abs(math.log(t_cost) - math.log(c_cost))
            sim = max(0.0, 1.0 - (log_dist / math.log(10.0)))
            return sim, f"Cost similarity: target {t_cost} vs candidate {c_cost} (score: {round(sim, 2)})"

        elif dimension == "execution_stage":
            t_prog = _to_float(target.get("physical_progress_pct") or target.get("physical_progress") or target.get("progress"))
            c_prog = _to_float(candidate.get("physical_progress_pct") or candidate.get("physical_progress") or candidate.get("progress"))
            if t_prog is not None and c_prog is not None:
                # Stage-aware progress distance: |prog_t - prog_c| / 100.0
                diff = abs(t_prog - c_prog)
                sim = max(0.0, 1.0 - (diff / 60.0))  # within 60% gap
                return sim, f"Progress stage gap: {round(diff, 1)}% (score: {round(sim, 2)})"
            # Categorical stage fallback
            t_st = str(target.get("execution_stage") or target.get("status", "")).strip().lower()
            c_st = str(candidate.get("execution_stage") or candidate.get("status", "")).strip().lower()
            if t_st and c_st:
                return (1.0, "Identical execution stage") if t_st == c_st else (0.5, "Different execution stage")
            return None, "Stage data unavailable"

        elif dimension == "implementing_agency":
            t_ag = str(target.get("implementing_agency") or target.get("agency", "")).strip().lower()
            c_ag = str(candidate.get("implementing_agency") or candidate.get("agency", "")).strip().lower()
            if not t_ag or not c_ag:
                return None, "Agency data unavailable"
            if t_ag == c_ag:
                return 1.0, f"Exact agency match: {t_ag.upper()}"
            # Check prefix / acronym match (e.g. NHAI vs NHIDCL)
            if any(token in c_ag for token in t_ag.split()) or any(token in t_ag for token in c_ag.split()):
                return 0.70, f"Related agency structure: {t_ag.upper()} and {c_ag.upper()}"
            return 0.30, f"Different agency: {t_ag.upper()} vs {c_ag.upper()}"

        elif dimension == "project_type":
            t_type = str(target.get("project_type") or target.get("subsector", "")).strip().lower()
            c_type = str(candidate.get("project_type") or candidate.get("subsector", "")).strip().lower()
            if not t_type or not c_type:
                return None, "Project type unavailable"
            if t_type == c_type:
                return 1.0, f"Exact project type match: {t_type}"
            if t_type in c_type or c_type in t_type:
                return 0.75, f"Sub-type overlap: {t_type} and {c_type}"
            return 0.25, f"Different project type: {t_type} vs {c_type}"

        elif dimension == "state":
            t_state = str(target.get("state") or target.get("location", "")).strip().lower()
            c_state = str(candidate.get("state") or candidate.get("location", "")).strip().lower()
            if not t_state or not c_state:
                return None, "State data unavailable"
            if t_state == c_state:
                return 1.0, f"Same state: {t_state.title()}"
            # Check regional proximity
            t_reg = self.STATE_REGIONS.get(t_state)
            c_reg = self.STATE_REGIONS.get(c_state)
            if t_reg and c_reg and t_reg == c_reg:
                return 0.70, f"Same geographic region ({t_reg}): {t_state.title()} & {c_state.title()}"
            return 0.30, f"Different regions: {t_state.title()} vs {c_state.title()}"

        elif dimension == "planned_duration":
            t_dur = _to_float(target.get("planned_duration_months") or target.get("planned_duration") or target.get("duration_months"))
            c_dur = _to_float(candidate.get("planned_duration_months") or candidate.get("planned_duration") or candidate.get("duration_months"))
            if t_dur is None or c_dur is None or t_dur <= 0 or c_dur <= 0:
                return None, "Duration data unavailable"
            diff = abs(t_dur - c_dur)
            sim = max(0.0, 1.0 - (diff / max(t_dur, 24.0)))
            return sim, f"Duration gap: {round(diff, 1)} months (score: {round(sim, 2)})"

        return None, f"Unknown dimension {dimension}"


def _to_float(val: Any) -> Optional[float]:
    if val is None:
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None
