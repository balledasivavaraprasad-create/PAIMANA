"""Cohort Refinement & Action Recommendation Engine (CI-09).

Combines quality, heterogeneity, subgroup detection, fragmentation, and stability findings
to recommend an actionable cohort decision: ACCEPT, ACCEPT_WITH_WARNINGS, SPLIT_INTO_SUBGROUPS, REFINE, INSUFFICIENT, or REJECT.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from .schemas import (
    CohortQualityAssessment,
    CohortQualityLevel,
    CohortRefinementAction,
    FragmentationReport,
    HeterogeneityReport,
    SubgroupDetectionReport,
)


class CohortRefinementEngine:
    """Recommends actionable cohort directives based on consolidated intelligence."""

    def determine_recommendation(
        self,
        quality: CohortQualityAssessment,
        heterogeneity: HeterogeneityReport,
        subgroups: SubgroupDetectionReport,
        fragmentation: Optional[FragmentationReport],
        stability_score: float,
    ) -> Tuple[CohortRefinementAction, List[str]]:
        """Synthesizes cohort analysis into a structured refinement decision and warning list."""
        warnings: List[str] = []

        # 1. Critical Rejection
        if quality.overall_quality == CohortQualityLevel.UNRELIABLE:
            return CohortRefinementAction.REJECT, ["Cohort contains critical data unreliability or corruption."]

        # 2. Insufficient Peers
        if quality.overall_quality == CohortQualityLevel.INSUFFICIENT:
            return CohortRefinementAction.INSUFFICIENT, ["Insufficient eligible peer sample size for comparative analysis."]

        # 3. Subgroup Partitioning
        if subgroups.subgroups_detected and len(subgroups.subgroups) >= 2:
            warnings.append(
                f"Cohort cleanly divides into {len(subgroups.subgroups)} subgroups. Subgroup benchmarking recommended."
            )
            return CohortRefinementAction.SPLIT_INTO_SUBGROUPS, warnings

        # 4. Refinement Needed (Fragmentation or High Heterogeneity without clear domain subgroup)
        if fragmentation and fragmentation.fragmentation_detected and len(fragmentation.isolated_peers) > 0:
            warnings.append(f"Cohort contains {len(fragmentation.isolated_peers)} isolated peer(s); refinement recommended.")
            return CohortRefinementAction.REFINE, warnings

        if heterogeneity.overall_level == "HIGH" and stability_score < 0.60:
            warnings.append("High heterogeneity combined with fragile selection stability; cohort refinement recommended.")
            return CohortRefinementAction.REFINE, warnings

        # 5. Accept with Warnings
        if heterogeneity.overall_level in ("HIGH", "MODERATE") or quality.overall_quality == CohortQualityLevel.LOW:
            if heterogeneity.overall_level == "HIGH":
                warnings.append("High cross-member heterogeneity; benchmark distributions will exhibit higher variance.")
            if quality.overall_quality == CohortQualityLevel.LOW:
                warnings.append("Marginal cohort quality score; interpret deviations with caution.")
            return CohortRefinementAction.ACCEPT_WITH_WARNINGS, warnings

        # 6. Clean Accept
        return CohortRefinementAction.ACCEPT, []
