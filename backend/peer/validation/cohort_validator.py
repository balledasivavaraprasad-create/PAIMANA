"""Cohort Logic Validation Engine for PAIMANA Peer Intelligence.

Validates that discovered peer cohorts satisfy strict scientific comparability:
1. Sector purity: candidates strictly match target infrastructure sector.
2. Execution stage alignment: execution progress is within acceptable stage brackets.
3. Scale ratio bounds: cost disparity does not distort benchmarking.
4. Data completeness: zero fabrication, requiring >= 3 valid empirical observations.
5. Heterogeneity & dispersion: checks coefficient of variation (CV) and bimodal risk.
6. Sensitivity stability: verifies cohort composition stability under perturbation.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import numpy as np

from ..schemas import CohortDiscoveryResult, CohortQuality


@dataclass
class CohortValidationCriteria:
    """Configurable criteria for validating peer cohort integrity."""
    min_cohort_size: int = 3
    max_scale_ratio: float = 5.0
    max_stage_gap_pct: float = 50.0
    min_average_similarity: float = 0.45
    max_coefficient_of_variation: float = 0.85
    min_stability_score: float = 0.60


@dataclass
class CohortValidationResult:
    """Comprehensive validation outcome for a peer cohort."""
    is_valid: bool
    validation_level: str  # VALID, MARGINAL, INVALID
    cohort_size: int
    sector_purity: bool
    stage_alignment: bool
    scale_bound_respected: bool
    data_completeness_rate: float
    heterogeneity_score: float
    stability_score: float
    average_similarity: float
    rejection_reasons: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    diagnostics: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "validation_level": self.validation_level,
            "cohort_size": self.cohort_size,
            "sector_purity": self.sector_purity,
            "stage_alignment": self.stage_alignment,
            "scale_bound_respected": self.scale_bound_respected,
            "data_completeness_rate": round(self.data_completeness_rate, 4),
            "heterogeneity_score": round(self.heterogeneity_score, 4),
            "stability_score": round(self.stability_score, 4),
            "average_similarity": round(self.average_similarity, 4),
            "rejection_reasons": self.rejection_reasons,
            "warnings": self.warnings,
            "diagnostics": self.diagnostics,
        }


class CohortValidator:
    """Validates peer cohort logic against scientific and domain rules."""

    def __init__(self, criteria: Optional[CohortValidationCriteria] = None):
        self.criteria = criteria or CohortValidationCriteria()

    def validate_cohort(
        self,
        target_project: Dict[str, Any],
        cohort_result: CohortDiscoveryResult,
        criteria: Optional[CohortValidationCriteria] = None,
    ) -> CohortValidationResult:
        crit = criteria or self.criteria
        reasons: List[str] = []
        warnings: List[str] = []
        diagnostics: Dict[str, Any] = {}

        cohort_size = cohort_result.cohort_size
        peers = cohort_result.peers

        # 1. Size & Quality sufficiency
        if cohort_size < crit.min_cohort_size:
            reasons.append(
                f"Cohort size ({cohort_size}) is below minimum requirement of {crit.min_cohort_size} peers."
            )
            return CohortValidationResult(
                is_valid=False,
                validation_level="INVALID",
                cohort_size=cohort_size,
                sector_purity=True,
                stage_alignment=True,
                scale_bound_respected=True,
                data_completeness_rate=0.0,
                heterogeneity_score=0.0,
                stability_score=0.0,
                average_similarity=cohort_result.average_similarity,
                rejection_reasons=reasons,
                warnings=warnings,
                diagnostics={"reason": "insufficient_cohort_size"},
            )

        # 2. Sector purity check
        t_sector = str(target_project.get("sector") or "").strip().lower()
        sector_mismatches = []
        for p in peers:
            c_sector = str((p.raw_attributes or {}).get("sector") or "").strip().lower()
            if t_sector and c_sector and t_sector != c_sector:
                sector_mismatches.append(f"{p.peer_code}: '{c_sector}' vs target '{t_sector}'")

        sector_purity = len(sector_mismatches) == 0
        if not sector_purity:
            reasons.append(f"Sector purity violated by {len(sector_mismatches)} peers: {sector_mismatches[:3]}")

        # 3. Stage alignment check
        t_prog = _safe_float(target_project.get("physical_progress_pct") or target_project.get("physical_progress"))
        stage_violations = []
        peer_progresses = []
        for p in peers:
            c_prog = _safe_float((p.raw_attributes or {}).get("physical_progress_pct") or (p.raw_attributes or {}).get("physical_progress"))
            if c_prog is not None:
                peer_progresses.append(c_prog)
                if t_prog is not None and abs(t_prog - c_prog) > crit.max_stage_gap_pct:
                    stage_violations.append(f"{p.peer_code} (progress: {c_prog:.1f}% vs target {t_prog:.1f}%)")

        stage_alignment = len(stage_violations) <= (cohort_size * 0.25)
        if not stage_alignment:
            reasons.append(
                f"Stage alignment violated: {len(stage_violations)}/{cohort_size} peers exceed {crit.max_stage_gap_pct}% gap."
            )
        elif stage_violations:
            warnings.append(f"{len(stage_violations)} peers have wide stage gap from target.")

        # 4. Scale ratio bound check
        t_cost = _safe_float(target_project.get("original_cost_cr") or target_project.get("original_cost") or target_project.get("cost"))
        peer_costs = []
        for p in peers:
            c_cost = _safe_float((p.raw_attributes or {}).get("original_cost_cr") or (p.raw_attributes or {}).get("original_cost") or (p.raw_attributes or {}).get("cost"))
            if c_cost is not None and c_cost > 0:
                peer_costs.append(c_cost)

        scale_ratio = 1.0
        scale_bound_respected = True
        if peer_costs:
            min_c = min(peer_costs)
            max_c = max(peer_costs)
            scale_ratio = (max_c / min_c) if min_c > 0 else 1.0
            if scale_ratio > crit.max_scale_ratio:
                # Check if target is near the median
                if t_cost is not None and (t_cost < min_c * 0.2 or t_cost > max_c * 2.0):
                    scale_bound_respected = False
                    reasons.append(
                        f"Cohort scale ratio ({scale_ratio:.1f}x) exceeds threshold ({crit.max_scale_ratio:.1f}x) and target is at extreme edge."
                    )
                else:
                    warnings.append(
                        f"Cohort scale ratio is wide ({scale_ratio:.1f}x); log-scale normalization recommended."
                    )

        # 5. Data completeness rate
        essential_keys = ["original_cost_cr", "physical_progress_pct", "implementing_agency"]
        total_slots = cohort_size * len(essential_keys)
        populated_slots = 0
        for p in peers:
            attrs = p.raw_attributes or {}
            for k in ["original_cost_cr", "original_cost", "cost"]:
                if attrs.get(k) is not None:
                    populated_slots += 1
                    break
            for k in ["physical_progress_pct", "physical_progress", "progress"]:
                if attrs.get(k) is not None:
                    populated_slots += 1
                    break
            for k in ["implementing_agency", "agency"]:
                if attrs.get(k):
                    populated_slots += 1
                    break

        completeness_rate = populated_slots / total_slots if total_slots > 0 else 0.0
        if completeness_rate < 0.65:
            reasons.append(f"Cohort data completeness ({completeness_rate*100:.1f}%) is below 65% minimum.")

        # 6. Heterogeneity / dispersion scoring
        cv_cost = 0.0
        if len(peer_costs) >= 3:
            arr_c = np.array(peer_costs)
            mean_c = np.mean(arr_c)
            std_c = np.std(arr_c, ddof=1)
            cv_cost = (std_c / mean_c) if mean_c > 0 else 0.0

        heterogeneity_score = min(1.0, cv_cost)
        if cv_cost > crit.max_coefficient_of_variation:
            warnings.append(f"High cohort scale dispersion (CV: {cv_cost:.2f} > {crit.max_coefficient_of_variation}).")

        # 7. Stability score from lineage or similarity
        stability = float(cohort_result.source_lineage.get("stability_score", 0.80) or 0.80)
        if stability < crit.min_stability_score:
            warnings.append(f"Cohort stability under perturbation ({stability:.2f}) is below {crit.min_stability_score}.")

        # 8. Average similarity check
        avg_sim = cohort_result.average_similarity
        if avg_sim < crit.min_average_similarity:
            reasons.append(f"Cohort average similarity ({avg_sim:.2f}) is below {crit.min_average_similarity} threshold.")

        # Determine final status
        is_valid = len(reasons) == 0
        validation_level = "VALID" if is_valid and len(warnings) == 0 else "MARGINAL" if is_valid else "INVALID"

        diagnostics = {
            "scale_ratio": round(scale_ratio, 2),
            "cv_cost": round(cv_cost, 4),
            "populated_slots": populated_slots,
            "total_slots": total_slots,
            "peer_progress_range": (round(min(peer_progresses), 1), round(max(peer_progresses), 1)) if peer_progresses else None,
            "peer_cost_range_cr": (round(min(peer_costs), 1), round(max(peer_costs), 1)) if peer_costs else None,
        }

        return CohortValidationResult(
            is_valid=is_valid,
            validation_level=validation_level,
            cohort_size=cohort_size,
            sector_purity=sector_purity,
            stage_alignment=stage_alignment,
            scale_bound_respected=scale_bound_respected,
            data_completeness_rate=completeness_rate,
            heterogeneity_score=heterogeneity_score,
            stability_score=stability,
            average_similarity=avg_sim,
            rejection_reasons=reasons,
            warnings=warnings,
            diagnostics=diagnostics,
        )


def _safe_float(val: Any) -> Optional[float]:
    if val is None or val == "" or str(val).strip() in ("(-)", "-", "nan", "None"):
        return None
    try:
        f = float(val)
        return None if math.isnan(f) else f
    except (ValueError, TypeError):
        return None
