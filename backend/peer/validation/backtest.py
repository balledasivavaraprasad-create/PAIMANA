"""Empirical Backtesting Engine for Peer Selection.

Evaluates and proves quantitatively that Peer Intelligence cohort selection
outperforms unconditioned Global and Sector baselines on infrastructure forecasting:
1. Global Baseline: All projects across all sectors and stages.
2. Sector Baseline: Naive sector average, ignoring scale and progress stage.
3. Peer Intelligence Cohort: Multi-dimensional similarity matching.

Computes MAE, RMSE, IQR Coverage, and Error Reduction to produce empirical evidence.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

from ..repository import ProjectRepository
from ..service import PeerIntelligenceService


@dataclass
class BacktestMetricResult:
    """Error metrics for a specific target KPI across baseline methods."""
    metric_name: str
    samples_evaluated: int
    mae_global: float
    mae_sector: float
    mae_peer_cohort: float
    rmse_global: float
    rmse_sector: float
    rmse_peer_cohort: float
    improvement_vs_global_pct: float
    improvement_vs_sector_pct: float
    iqr_coverage_peer_pct: float
    is_peer_superior: bool
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metric_name": self.metric_name,
            "samples_evaluated": self.samples_evaluated,
            "mae_global": round(self.mae_global, 4),
            "mae_sector": round(self.mae_sector, 4),
            "mae_peer_cohort": round(self.mae_peer_cohort, 4),
            "rmse_global": round(self.rmse_global, 4),
            "rmse_sector": round(self.rmse_sector, 4),
            "rmse_peer_cohort": round(self.rmse_peer_cohort, 4),
            "improvement_vs_global_pct": round(self.improvement_vs_global_pct, 2),
            "improvement_vs_sector_pct": round(self.improvement_vs_sector_pct, 2),
            "iqr_coverage_peer_pct": round(self.iqr_coverage_peer_pct, 2),
            "is_peer_superior": self.is_peer_superior,
            "notes": self.notes,
        }


@dataclass
class PeerBacktestReport:
    """Consolidated empirical backtesting report proving peer cohort efficacy."""
    total_projects_evaluated: int
    metrics_evaluated: List[str]
    metric_results: Dict[str, BacktestMetricResult]
    overall_mean_error_reduction_vs_global_pct: float
    overall_mean_error_reduction_vs_sector_pct: float
    empirical_proof_established: bool
    summary: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_projects_evaluated": self.total_projects_evaluated,
            "metrics_evaluated": self.metrics_evaluated,
            "metric_results": {k: v.to_dict() for k, v in self.metric_results.items()},
            "overall_mean_error_reduction_vs_global_pct": round(self.overall_mean_error_reduction_vs_global_pct, 2),
            "overall_mean_error_reduction_vs_sector_pct": round(self.overall_mean_error_reduction_vs_sector_pct, 2),
            "empirical_proof_established": self.empirical_proof_established,
            "summary": self.summary,
        }


class PeerBacktestEngine:
    """Executes empirical backtests comparing peer cohorts against naive baselines."""

    def __init__(self, service: PeerIntelligenceService):
        self.service = service
        self.repository = service.repository

    def run_backtest(
        self,
        test_projects: List[Dict[str, Any]],
        metrics: Optional[List[str]] = None,
    ) -> PeerBacktestReport:
        target_metrics = metrics or [
            "cost_overrun_pct",
            "schedule_slippage_months",
            "physical_progress_pct",
        ]

        # Retrieve universe for global baseline
        all_candidates = self.repository.get_candidates(sector=None)
        
        # Precompute global medians
        global_medians: Dict[str, float] = {}
        for m in target_metrics:
            vals = [_extract_numeric(c, m) for c in all_candidates if _extract_numeric(c, m) is not None]
            global_medians[m] = float(np.median(vals)) if vals else 0.0

        # Sector candidates map
        sector_candidates: Dict[str, List[Dict[str, Any]]] = {}
        for c in all_candidates:
            s = str(c.get("sector", "")).strip().lower()
            if s:
                sector_candidates.setdefault(s, []).append(c)

        # Precompute sector medians
        sector_medians: Dict[Tuple[str, str], float] = {}
        for s, cands in sector_candidates.items():
            for m in target_metrics:
                vals = [_extract_numeric(c, m) for c in cands if _extract_numeric(c, m) is not None]
                sector_medians[(s, m)] = float(np.median(vals)) if vals else global_medians.get(m, 0.0)

        results: Dict[str, BacktestMetricResult] = {}
        error_reductions_vs_sector: List[float] = []
        error_reductions_vs_global: List[float] = []

        for m in target_metrics:
            peer_errors: List[float] = []
            sector_errors: List[float] = []
            global_errors: List[float] = []
            iqr_hits: int = 0
            n_eval = 0

            for target in test_projects:
                actual_val = _extract_numeric(target, m)
                if actual_val is None:
                    continue

                t_sector = str(target.get("sector", "")).strip().lower()

                # 1. Global prediction
                pred_global = global_medians.get(m, 0.0)
                err_global = abs(actual_val - pred_global)

                # 2. Sector prediction
                pred_sector = sector_medians.get((t_sector, m), pred_global)
                err_sector = abs(actual_val - pred_sector)

                # 3. Peer cohort prediction
                bench_res = self.service.peer_benchmark(target, metrics=[m])
                if not bench_res.is_sufficient or m not in bench_res.distributions:
                    continue

                dist = bench_res.distributions[m]
                pred_peer = dist.median
                err_peer = abs(actual_val - pred_peer)

                # Check IQR coverage
                if dist.p25 <= actual_val <= dist.p75:
                    iqr_hits += 1

                peer_errors.append(err_peer)
                sector_errors.append(err_sector)
                global_errors.append(err_global)
                n_eval += 1

            if n_eval < 2:
                continue

            mae_p = float(np.mean(peer_errors))
            mae_s = float(np.mean(sector_errors))
            mae_g = float(np.mean(global_errors))

            rmse_p = float(np.sqrt(np.mean([e**2 for e in peer_errors])))
            rmse_s = float(np.sqrt(np.mean([e**2 for e in sector_errors])))
            rmse_g = float(np.sqrt(np.mean([e**2 for e in global_errors])))

            impr_g = ((mae_g - mae_p) / mae_g * 100.0) if mae_g > 0 else 0.0
            impr_s = ((mae_s - mae_p) / mae_s * 100.0) if mae_s > 0 else 0.0
            iqr_cov = (iqr_hits / n_eval * 100.0) if n_eval > 0 else 0.0

            is_superior = mae_p <= mae_s and mae_p <= mae_g
            error_reductions_vs_global.append(impr_g)
            error_reductions_vs_sector.append(impr_s)

            notes = [
                f"Peer MAE: {mae_p:.2f} vs Sector MAE: {mae_s:.2f} (reduction: {impr_s:.1f}%)",
                f"Peer RMSE: {rmse_p:.2f} vs Sector RMSE: {rmse_s:.2f}",
                f"Cohort IQR coverage: {iqr_cov:.1f}% of actual targets fell within [Q1, Q3]",
            ]

            results[m] = BacktestMetricResult(
                metric_name=m,
                samples_evaluated=n_eval,
                mae_global=mae_g,
                mae_sector=mae_s,
                mae_peer_cohort=mae_p,
                rmse_global=rmse_g,
                rmse_sector=rmse_s,
                rmse_peer_cohort=rmse_p,
                improvement_vs_global_pct=impr_g,
                improvement_vs_sector_pct=impr_s,
                iqr_coverage_peer_pct=iqr_cov,
                is_peer_superior=is_superior,
                notes=notes,
            )

        mean_impr_g = float(np.mean(error_reductions_vs_global)) if error_reductions_vs_global else 0.0
        mean_impr_s = float(np.mean(error_reductions_vs_sector)) if error_reductions_vs_sector else 0.0
        proof_established = mean_impr_s > 0.0 and any(r.is_peer_superior for r in results.values())

        summary = (
            f"Empirical Backtest: Peer cohort selection reduced forecasting error by "
            f"{mean_impr_s:.1f}% vs naive sector baselines and {mean_impr_g:.1f}% vs global unconditioned baselines "
            f"across {len(test_projects)} projects. "
            f"Empirical superiority established: {proof_established}."
        )

        return PeerBacktestReport(
            total_projects_evaluated=len(test_projects),
            metrics_evaluated=list(results.keys()),
            metric_results=results,
            overall_mean_error_reduction_vs_global_pct=mean_impr_g,
            overall_mean_error_reduction_vs_sector_pct=mean_impr_s,
            empirical_proof_established=proof_established,
            summary=summary,
        )


def _extract_numeric(rec: Dict[str, Any], key: str) -> Optional[float]:
    v = rec.get(key)
    if v is None or v == "" or str(v).strip() in ("(-)", "-", "nan", "None"):
        return None
    try:
        f = float(v)
        return None if math.isnan(f) else f
    except (TypeError, ValueError):
        return None
