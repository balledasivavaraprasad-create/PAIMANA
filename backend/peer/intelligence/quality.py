"""Multidimensional Cohort Quality Assessment Engine (CI-01, CI-2).

Evaluates 9 orthogonal quality dimensions independently before computing
a calibrated overall quality tier (HIGH, MEDIUM, LOW, INSUFFICIENT, UNRELIABLE).
"""
from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple

from ..schemas import SimilarityBreakdown
from .schemas import (
    CohortQualityAssessment,
    CohortQualityLevel,
    QualityDimensionAssessment,
)


class CohortQualityAssessor:
    """Computes comprehensive multidimensional quality metrics for a peer cohort."""

    DIMENSION_WEIGHTS: Dict[str, float] = {
        "cohort_size": 0.20,
        "similarity_quality": 0.20,
        "similarity_consistency": 0.15,
        "completeness": 0.15,
        "temporal_coverage": 0.10,
        "homogeneity": 0.10,
        "source_reliability": 0.05,
        "metric_compatibility": 0.05,
    }

    def assess_quality(
        self,
        peers: List[SimilarityBreakdown],
        target_project: Dict[str, Any],
        required_metrics: Optional[List[str]] = None,
    ) -> CohortQualityAssessment:
        """Evaluates all 9 dimensions and assigns an overall quality tier."""
        dim_details: Dict[str, QualityDimensionAssessment] = {}
        dim_scores: Dict[str, float] = {}
        quality_reasons: List[str] = []

        n_peers = len(peers)

        # 1. Cohort Size Score
        if n_peers >= 10:
            size_score, size_status = 1.0, "EXCELLENT"
        elif n_peers >= 5:
            size_score, size_status = 0.75, "ADEQUATE"
        elif n_peers >= 3:
            size_score, size_status = 0.50, "MARGINAL"
        else:
            size_score, size_status = 0.20, "DEFICIENT"
        dim_details["cohort_size"] = QualityDimensionAssessment(
            "cohort_size", size_score, size_status, f"{n_peers} peers in cohort."
        )
        dim_scores["cohort_size"] = size_score

        if n_peers < 3:
            quality_reasons.append(f"Cohort size ({n_peers}) is below minimum statistical threshold of 3.")

        # 2. Similarity Quality
        sims = [p.overall_similarity for p in peers]
        avg_sim = (sum(sims) / n_peers) if n_peers > 0 else 0.0
        if avg_sim >= 0.80:
            sim_score, sim_status = 1.0, "EXCELLENT"
        elif avg_sim >= 0.65:
            sim_score, sim_status = 0.80, "ADEQUATE"
        elif avg_sim >= 0.50:
            sim_score, sim_status = 0.60, "MARGINAL"
        else:
            sim_score, sim_status = 0.30, "DEFICIENT"
        dim_details["similarity_quality"] = QualityDimensionAssessment(
            "similarity_quality", sim_score, sim_status, f"Mean similarity is {round(avg_sim, 2)}."
        )
        dim_scores["similarity_quality"] = sim_score

        # 3. Similarity Consistency (std_dev of similarity)
        if n_peers > 1:
            variance = sum((s - avg_sim) ** 2 for s in sims) / (n_peers - 1)
            std_dev = math.sqrt(variance)
        else:
            std_dev = 0.0

        if std_dev <= 0.08:
            cons_score, cons_status = 1.0, "EXCELLENT"
        elif std_dev <= 0.15:
            cons_score, cons_status = 0.75, "ADEQUATE"
        else:
            cons_score, cons_status = 0.45, "MARGINAL"
        dim_details["similarity_consistency"] = QualityDimensionAssessment(
            "similarity_consistency", cons_score, cons_status, f"Similarity std dev is {round(std_dev, 3)}."
        )
        dim_scores["similarity_consistency"] = cons_score

        # 4. Data Completeness
        req_fields = ["original_cost", "physical_progress", "implementing_agency"]
        total_cells = max(1, n_peers * len(req_fields))
        present_cells = 0
        for p in peers:
            for f in req_fields:
                if p.raw_attributes.get(f) is not None:
                    present_cells += 1
        comp_ratio = present_cells / total_cells
        comp_score = max(0.2, min(1.0, comp_ratio))
        comp_status = "EXCELLENT" if comp_score >= 0.90 else ("ADEQUATE" if comp_score >= 0.70 else "DEFICIENT")
        dim_details["completeness"] = QualityDimensionAssessment(
            "completeness", comp_score, comp_status, f"{round(comp_ratio * 100, 1)}% core fields populated."
        )
        dim_scores["completeness"] = comp_score

        # 5. Temporal Coverage
        # Check if snapshots or date information exists
        has_dates = sum(1 for p in peers if p.raw_attributes.get("snapshot_date") or p.raw_attributes.get("observation_date"))
        temp_ratio = has_dates / max(1, n_peers)
        temp_score = 1.0 if temp_ratio >= 0.80 else (0.70 if temp_ratio >= 0.50 else 0.40)
        temp_status = "EXCELLENT" if temp_score >= 0.90 else "ADEQUATE"
        dim_details["temporal_coverage"] = QualityDimensionAssessment(
            "temporal_coverage", temp_score, temp_status, f"{round(temp_ratio * 100, 1)}% peers have dated snapshots."
        )
        dim_scores["temporal_coverage"] = temp_score

        # 6. Homogeneity
        # Check scale variation (max cost / min cost)
        costs = [float(p.raw_attributes.get("original_cost") or p.raw_attributes.get("cost") or 0) for p in peers]
        costs = [c for c in costs if c > 0]
        if len(costs) >= 2:
            cost_ratio = max(costs) / min(costs) if min(costs) > 0 else 1.0
            homo_score = 1.0 if cost_ratio <= 2.5 else (0.70 if cost_ratio <= 5.0 else 0.40)
        else:
            homo_score = 0.80
        homo_status = "EXCELLENT" if homo_score >= 0.90 else ("ADEQUATE" if homo_score >= 0.65 else "MARGINAL")
        dim_details["homogeneity"] = QualityDimensionAssessment(
            "homogeneity", homo_score, homo_status, f"Scale ratio across peers is {round(cost_ratio if len(costs)>=2 else 1.0, 2)}x."
        )
        dim_scores["homogeneity"] = homo_score

        # 7. Source Reliability & Integrity
        # Check if any peer has corrupted or negative values
        has_corrupt = any(
            (float(p.raw_attributes.get("original_cost", 0) or 0) < 0) or
            (float(p.raw_attributes.get("physical_progress", 0) or 0) > 150)
            for p in peers
        )
        rel_score = 0.30 if has_corrupt else 1.0
        rel_status = "DEFICIENT" if has_corrupt else "EXCELLENT"
        dim_details["source_reliability"] = QualityDimensionAssessment(
            "source_reliability", rel_score, rel_status, "Corrupted peer attributes detected." if has_corrupt else "All peer records mathematically sound."
        )
        dim_scores["source_reliability"] = rel_score

        # 8. Metric Compatibility
        metrics = required_metrics or ["cost_overrun_pct", "physical_progress"]
        usable_count = 0
        for m in metrics:
            pop = sum(1 for p in peers if p.raw_attributes.get(m) is not None)
            if pop >= max(2, int(n_peers * 0.5)):
                usable_count += 1
        metric_compat_ratio = usable_count / len(metrics) if metrics else 1.0
        metric_score = max(0.2, min(1.0, metric_compat_ratio))
        dim_details["metric_compatibility"] = QualityDimensionAssessment(
            "metric_compatibility", metric_score, "ADEQUATE" if metric_score >= 0.50 else "DEFICIENT",
            f"{usable_count}/{len(metrics)} required metrics supported by cohort."
        )
        dim_scores["metric_compatibility"] = metric_score

        # Compute Overall Score
        overall_score = sum(dim_scores[d] * self.DIMENSION_WEIGHTS.get(d, 0.1) for d in dim_scores)

        # Quality Tier Classification
        if rel_score < 0.50 or comp_score < 0.40 or metric_score < 0.40:
            quality = CohortQualityLevel.UNRELIABLE
            quality_reasons.append("Cohort flagged as UNRELIABLE due to data integrity or completeness deficits.")
        elif n_peers < 3 or overall_score < 0.45:
            quality = CohortQualityLevel.INSUFFICIENT
            quality_reasons.append("Cohort is INSUFFICIENT for statistically sound comparative benchmarking.")
        elif n_peers < 5 or overall_score < 0.60:
            quality = CohortQualityLevel.LOW
            quality_reasons.append(f"Marginal cohort quality ({round(overall_score, 2)}); use conclusions with caution.")
        elif n_peers >= 10 and overall_score >= 0.75 and cons_score >= 0.70:
            quality = CohortQualityLevel.HIGH
            quality_reasons.append(f"High quality cohort with {n_peers} consistent, high-similarity peers.")
        else:
            quality = CohortQualityLevel.MEDIUM
            quality_reasons.append(f"Adequate cohort with {n_peers} peers (quality score: {round(overall_score, 2)}).")

        return CohortQualityAssessment(
            overall_quality=quality,
            overall_score=overall_score,
            dimension_scores=dim_scores,
            dimension_details=dim_details,
            quality_reasons=quality_reasons,
        )
