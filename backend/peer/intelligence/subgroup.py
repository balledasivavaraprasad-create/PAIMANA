"""Domain-Driven Subgroup Detection Engine (CI-04, CI-5).

Identifies structurally distinct subgroups within peer cohorts based on
interpretable domain boundaries (procurement model, execution stage, scale band, project type).
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from ..schemas import SimilarityBreakdown
from .schemas import CohortSubgroupRecord, SubgroupDetectionReport


class SubgroupDetector:
    """Detects explainable domain-driven subgroups within a peer cohort."""

    DEFAULT_GROUPING_DIMENSIONS = [
        "procurement_type",
        "project_type",
        "execution_stage",
        "cost_band",
    ]

    def detect_subgroups(
        self,
        peers: List[SimilarityBreakdown],
        target_project: Dict[str, Any],
        preferred_dimension: Optional[str] = None,
    ) -> SubgroupDetectionReport:
        """Detects meaningful partitions within the cohort across domain dimensions."""
        if len(peers) < 4:
            return SubgroupDetectionReport(
                subgroups_detected=False,
                detection_method="DOMAIN_DRIVEN",
                subgroups=[],
                recommendation="Cohort too small (< 4 peers) for meaningful subgroup division; retain unified cohort.",
            )

        candidate_dims = [preferred_dimension] if preferred_dimension else self.DEFAULT_GROUPING_DIMENSIONS

        for dim in candidate_dims:
            if not dim:
                continue
            groups = self._partition_by_dimension(peers, dim)
            # A valid subgroup partition must have at least 2 groups with >= 2 members each
            valid_groups = [g for g in groups.values() if len(g) >= 2]
            if len(valid_groups) >= 2:
                # Subgroups found!
                t_val = self._extract_dim_value(target_project, dim)
                subgroup_records: List[CohortSubgroupRecord] = []
                target_subgroup_id: Optional[str] = None

                for idx, (grp_key, grp_peers) in enumerate(groups.items(), start=1):
                    sub_id = f"SUBGRP-{dim.upper()}-{idx}"
                    is_target = str(grp_key).lower() == str(t_val).lower() if t_val is not None else False
                    if is_target:
                        target_subgroup_id = sub_id

                    sims = [p.overall_similarity for p in grp_peers]
                    mean_sim = sum(sims) / len(sims)

                    costs = [float(p.raw_attributes.get("original_cost") or p.raw_attributes.get("cost") or 0) for p in grp_peers]
                    costs = [c for c in costs if c > 0]
                    avg_cost = sum(costs) / len(costs) if costs else 0.0

                    progs = [float(p.raw_attributes.get("physical_progress") or p.raw_attributes.get("progress") or 0) for p in grp_peers]
                    avg_prog = sum(progs) / len(progs) if progs else 0.0

                    record = CohortSubgroupRecord(
                        subgroup_id=sub_id,
                        name=f"{dim.title()} Group: {str(grp_key).title()}",
                        grouping_dimension=dim,
                        group_value=grp_key,
                        peer_codes=[p.peer_code for p in grp_peers],
                        size=len(grp_peers),
                        mean_similarity=mean_sim,
                        key_characteristics={
                            "average_cost": round(avg_cost, 2),
                            "average_progress": round(avg_prog, 2),
                        },
                        target_matches=is_target,
                    )
                    subgroup_records.append(record)

                rec_text = (
                    f"Cohort cleanly divides into {len(valid_groups)} subgroups by '{dim}'. "
                    f"Target project aligns with '{target_subgroup_id or 'NONE'}'. "
                    f"Recommend running subgroup-specific benchmarking for targeted comparative analysis."
                )

                return SubgroupDetectionReport(
                    subgroups_detected=True,
                    detection_method="DOMAIN_DRIVEN",
                    subgroups=subgroup_records,
                    target_subgroup_id=target_subgroup_id,
                    between_group_divergence=0.45,
                    recommendation=rec_text,
                )

        return SubgroupDetectionReport(
            subgroups_detected=False,
            detection_method="DOMAIN_DRIVEN",
            subgroups=[],
            recommendation="No significant domain-driven cluster separation detected; cohort is sufficiently uniform.",
        )

    def _partition_by_dimension(
        self,
        peers: List[SimilarityBreakdown],
        dimension: str,
    ) -> Dict[str, List[SimilarityBreakdown]]:
        """Partitions peers into bins by dimension value."""
        groups: Dict[str, List[SimilarityBreakdown]] = {}
        for p in peers:
            val = self._extract_dim_value(p.raw_attributes, dimension)
            if val is not None:
                groups.setdefault(str(val).strip().title(), []).append(p)
        return groups

    def _extract_dim_value(self, rec: Dict[str, Any], dimension: str) -> Optional[str]:
        if dimension == "cost_band":
            c = float(rec.get("original_cost") or rec.get("cost") or 0)
            if c <= 0:
                return None
            if c < 500:
                return "Small (< 500 Cr)"
            elif c <= 2500:
                return "Medium (500 - 2500 Cr)"
            else:
                return "Mega (> 2500 Cr)"
        elif dimension == "execution_stage":
            prog = rec.get("physical_progress") or rec.get("progress")
            if prog is not None:
                p_val = float(prog)
                if p_val < 30.0:
                    return "Early Stage (< 30%)"
                elif p_val <= 75.0:
                    return "Mid Stage (30-75%)"
                else:
                    return "Late Stage (> 75%)"
            return str(rec.get("execution_stage") or rec.get("status", "")).strip() or None
        else:
            v = rec.get(dimension)
            return str(v).strip() if v else None
