"""Domain-Specific Peer Normalization Engine (DSI-12).

Calculates domain adjustment multipliers for peer comparability across terrain difficulties,
structural configurations (elevated vs underground), and commercial execution models.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .schemas import (
    DomainNormalizationAdjustment,
    ExecutionModel,
    InfrastructureCategory,
    InfrastructureSector,
    ProjectDomainProfile,
    TerrainType,
)


class DomainNormalizationEngine:
    """Computes transparent domain adjustments for peer metric comparisons."""

    def compute_normalizations(
        self,
        profile: ProjectDomainProfile,
        target_metrics: Dict[str, float],
    ) -> List[DomainNormalizationAdjustment]:
        adjustments: List[DomainNormalizationAdjustment] = []

        # Merge target_metrics with profile attributes fallback
        metrics = dict(target_metrics or {})
        for k in ["cost_overrun_pct", "time_overrun_pct", "cost_per_km_cr", "physical_progress_pct", "financial_progress_pct"]:
            if k not in metrics and k in profile.attributes and profile.attributes[k] is not None:
                try:
                    metrics[k] = float(profile.attributes[k])
                except (ValueError, TypeError):
                    pass

        # 1. Terrain Normalization for Cost & Schedule
        terrain_factors = {
            TerrainType.PLAIN: 1.0,
            TerrainType.ROLLING: 1.10,
            TerrainType.COASTAL: 1.15,
            TerrainType.RIVERINE: 1.25,
            TerrainType.URBAN_CONGESTED: 1.35,
            TerrainType.HILLY: 1.45,
            TerrainType.MOUNTAINOUS: 1.85,
        }
        t_mult = terrain_factors.get(profile.terrain, 1.0)

        if profile.terrain in (TerrainType.HILLY, TerrainType.MOUNTAINOUS, TerrainType.URBAN_CONGESTED):
            if "time_overrun_pct" in metrics:
                raw_time = metrics["time_overrun_pct"]
                # In difficult terrain, natural schedule friction is higher
                adj_time = raw_time / t_mult
                adjustments.append(
                    DomainNormalizationAdjustment(
                        metric_name="time_overrun_pct",
                        raw_target_value=raw_time,
                        normalized_target_value=adj_time,
                        adjustment_factor=1.0 / t_mult,
                        adjustment_rationale=(
                            f"Normalized for {profile.terrain.value} topography (factor {t_mult:.2f}x). "
                            f"Difficult terrain inherently imposes slope stabilization, limited working seasons, and slower cycle times."
                        ),
                    )
                )

            if "cost_per_km_cr" in metrics:
                raw_cost_km = metrics["cost_per_km_cr"]
                adj_cost_km = raw_cost_km / t_mult
                adjustments.append(
                    DomainNormalizationAdjustment(
                        metric_name="cost_per_km_cr",
                        raw_target_value=raw_cost_km,
                        normalized_target_value=adj_cost_km,
                        adjustment_factor=1.0 / t_mult,
                        adjustment_rationale=(
                            f"Normalized cost per km for {profile.terrain.value} terrain against generic plain baseline."
                        ),
                    )
                )

        # 2. Structural Complexity Normalization (Underground / Tunneling vs Elevated)
        ug_ratio = profile.underground_ratio or 0.0
        el_ratio = profile.elevated_ratio or 0.0

        if ug_ratio > 0.0 and profile.sector == InfrastructureSector.URBAN_METRO:
            # Underground metro is typically ~2.8x more expensive per km than at-grade / elevated
            structural_cost_factor = 1.0 + (ug_ratio * 1.8)
            raw_cost = metrics.get("cost_overrun_pct", 0.0)
            adj_cost = raw_cost / structural_cost_factor
            adjustments.append(
                DomainNormalizationAdjustment(
                    metric_name="cost_overrun_pct",
                    raw_target_value=raw_cost,
                    normalized_target_value=adj_cost,
                    adjustment_factor=1.0 / structural_cost_factor,
                    adjustment_rationale=(
                        f"Underground tunneling proportion is {ug_ratio * 100.0:.1f}%. "
                        f"Civil underground excavation carries higher geological unpredictability and baseline capex."
                    ),
                )
            )

        # 3. Execution Model Normalization (EPC vs HAM vs Item Rate)
        if profile.execution_model == ExecutionModel.ITEM_RATE:
            # Item Rate contracts transfer quantity and variation risks to owner
            if "cost_overrun_pct" in target_metrics:
                raw_c = target_metrics["cost_overrun_pct"]
                adjustments.append(
                    DomainNormalizationAdjustment(
                        metric_name="cost_overrun_pct",
                        raw_target_value=raw_c,
                        normalized_target_value=raw_c * 0.90,
                        adjustment_factor=0.90,
                        adjustment_rationale=(
                            "Item Rate contract structure naturally subjects the project to bill of quantities (BoQ) "
                            "remeasurement variations compared to lump-sum turnkey EPC benchmarks."
                        ),
                    )
                )
        elif profile.execution_model == ExecutionModel.HAM:
            # HAM contracts feature strict milestone-based payment tranches (40% construction / 60% annuity)
            adjustments.append(
                DomainNormalizationAdjustment(
                    metric_name="financial_progress_pct",
                    raw_target_value=target_metrics.get("financial_progress_pct", 0.0),
                    normalized_target_value=target_metrics.get("financial_progress_pct", 0.0),
                    adjustment_factor=1.0,
                    adjustment_rationale=(
                        "HAM (Hybrid Annuity Model) aligns commercial payments strictly to 5 physical milestone gates (20% each); "
                        "discrepancies reflect milestone certification rules rather than invoice delays."
                    ),
                )
            )

        return adjustments
