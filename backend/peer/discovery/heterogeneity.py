"""Cohort Heterogeneity & Subgroup Detection Engine for Peer Discovery.

Detects multimodal distributions, scale disparities, and distinct clusters within a peer cohort.
Recommends homogeneous analytical sub-cohorts when pooling creates statistical distortion.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ..schemas import SimilarityBreakdown


@dataclass
class CohortSubgroup:
    """Distinct cluster or subgroup identified within a peer cohort."""
    subgroup_id: str
    peer_codes: List[str]
    size: int
    mean_cost: float
    mean_progress: float
    is_target_cluster: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            "subgroup_id": self.subgroup_id,
            "peer_codes": self.peer_codes,
            "size": self.size,
            "mean_cost": round(self.mean_cost, 2),
            "mean_progress": round(self.mean_progress, 2),
            "is_target_cluster": self.is_target_cluster,
        }


@dataclass
class HeterogeneityAnalysisResult:
    """Outcome of cohort heterogeneity and modality analysis."""
    is_heterogeneous: bool
    heterogeneity_level: str  # LOW, MODERATE, HIGH
    detected_modality: str    # UNIMODAL, BIMODAL, MULTIMODAL
    subgroups: List[CohortSubgroup] = field(default_factory=list)
    recommended_peer_codes: List[str] = field(default_factory=list)
    explanation: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_heterogeneous": self.is_heterogeneous,
            "heterogeneity_level": self.heterogeneity_level,
            "detected_modality": self.detected_modality,
            "subgroups": [s.to_dict() for s in self.subgroups],
            "recommended_peer_codes": self.recommended_peer_codes,
            "explanation": self.explanation,
        }


class CohortHeterogeneityDetector:
    """Detects scale disparities and multimodal clusters across selected peers."""

    def analyze(
        self,
        target_project: Dict[str, Any],
        peers: List[SimilarityBreakdown],
    ) -> HeterogeneityAnalysisResult:
        """Analyzes peers for bimodal scale clustering and returns recommended cohort."""
        if len(peers) < 4:
            return HeterogeneityAnalysisResult(
                is_heterogeneous=False,
                heterogeneity_level="LOW",
                detected_modality="UNIMODAL",
                recommended_peer_codes=[p.peer_code for p in peers],
                explanation="Cohort too small (< 4 peers) for meaningful clustering; treated as unified baseline.",
            )

        costs: List[tuple[str, float, float]] = []
        for p in peers:
            cost = _extract_cost(p.raw_attributes)
            prog = _extract_progress(p.raw_attributes)
            if cost is not None and cost > 0:
                costs.append((p.peer_code, cost, prog or 0.0))

        if len(costs) < 4:
            return HeterogeneityAnalysisResult(
                is_heterogeneous=False,
                heterogeneity_level="LOW",
                detected_modality="UNIMODAL",
                recommended_peer_codes=[p.peer_code for p in peers],
                explanation="Insufficient cost data across peers for clustering.",
            )

        # Sort by cost
        costs.sort(key=lambda x: x[1])
        min_cost = costs[0][1]
        max_cost = costs[-1][1]

        # Check scale ratio (if max is > 4x min, test bimodal clustering)
        scale_ratio = max_cost / min_cost if min_cost > 0 else 1.0

        if scale_ratio < 3.5:
            return HeterogeneityAnalysisResult(
                is_heterogeneous=False,
                heterogeneity_level="LOW",
                detected_modality="UNIMODAL",
                recommended_peer_codes=[p.peer_code for p in peers],
                explanation=f"Cohort scale is homogeneous (max-to-min cost ratio: {round(scale_ratio, 2)}x).",
            )

        # 2-Cluster 1D K-Means approximation on log(cost)
        log_costs = [math.log(c[1]) for c in costs]
        # Seed centroids at min and max
        c1, c2 = log_costs[0], log_costs[-1]

        for _ in range(10):
            g1, g2 = [], []
            for i, lc in enumerate(log_costs):
                if abs(lc - c1) <= abs(lc - c2):
                    g1.append(i)
                else:
                    g2.append(i)
            if not g1 or not g2:
                break
            c1 = sum(log_costs[i] for i in g1) / len(g1)
            c2 = sum(log_costs[i] for i in g2) / len(g2)

        # If both groups have at least 2 members and centroid difference is substantial
        if len(g1) >= 2 and len(g2) >= 2 and abs(c1 - c2) > math.log(2.5):
            sub1_codes = [costs[i][0] for i in g1]
            sub1_cost = sum(costs[i][1] for i in g1) / len(g1)
            sub1_prog = sum(costs[i][2] for i in g1) / len(g1)

            sub2_codes = [costs[i][0] for i in g2]
            sub2_cost = sum(costs[i][1] for i in g2) / len(g2)
            sub2_prog = sum(costs[i][2] for i in g2) / len(g2)

            t_cost = _extract_cost(target_project) or sub1_cost
            t_log = math.log(t_cost) if t_cost > 0 else c1

            target_in_sub1 = abs(t_log - c1) <= abs(t_log - c2)
            recommended = sub1_codes if target_in_sub1 else sub2_codes

            s1 = CohortSubgroup(
                subgroup_id="CLUSTER_A_LOWER_SCALE",
                peer_codes=sub1_codes,
                size=len(sub1_codes),
                mean_cost=sub1_cost,
                mean_progress=sub1_prog,
                is_target_cluster=target_in_sub1,
            )
            s2 = CohortSubgroup(
                subgroup_id="CLUSTER_B_HIGHER_SCALE",
                peer_codes=sub2_codes,
                size=len(sub2_codes),
                mean_cost=sub2_cost,
                mean_progress=sub2_prog,
                is_target_cluster=not target_in_sub1,
            )

            rec_cluster = "Cluster A" if target_in_sub1 else "Cluster B"
            explanation = (
                f"Bimodal scale detected (scale ratio {round(scale_ratio, 1)}x). "
                f"Cluster A (mean ₹{round(sub1_cost, 1)}cr, {len(sub1_codes)} peers), "
                f"Cluster B (mean ₹{round(sub2_cost, 1)}cr, {len(sub2_codes)} peers). "
                f"Target aligns with {rec_cluster}; recommending {len(recommended)} comparable peers."
            )

            return HeterogeneityAnalysisResult(
                is_heterogeneous=True,
                heterogeneity_level="HIGH" if scale_ratio > 5.0 else "MODERATE",
                detected_modality="BIMODAL",
                subgroups=[s1, s2],
                recommended_peer_codes=recommended,
                explanation=explanation,
            )

        return HeterogeneityAnalysisResult(
            is_heterogeneous=False,
            heterogeneity_level="LOW",
            detected_modality="UNIMODAL",
            recommended_peer_codes=[p.peer_code for p in peers],
            explanation="Continuous distribution across peer scale; no clear bimodal separation.",
        )


def _extract_cost(rec: Dict[str, Any]) -> Optional[float]:
    val = rec.get("original_cost_cr") or rec.get("original_cost") or rec.get("cost") or rec.get("sanctioned_cost")
    if val is not None:
        try:
            return float(val)
        except (ValueError, TypeError):
            pass
    return None


def _extract_progress(rec: Dict[str, Any]) -> Optional[float]:
    val = rec.get("physical_progress_pct") or rec.get("physical_progress") or rec.get("progress")
    if val is not None:
        try:
            return float(val)
        except (ValueError, TypeError):
            pass
    return None
