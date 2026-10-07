"""Multi-Snapshot Historical Trajectory Comparison Engine for PAIMANA Projects.

Compares chronological rates of change between target project and peer cohort:
- Monthly physical progress velocity (d_prog / dt)
- Monthly expenditure burn rate (d_exp / dt)
- Risk score acceleration (d_risk / dt)
- Explicit data-insufficient state when history < 2 snapshots
- Zero fabrication of synthetic trends
"""
from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from ..benchmark import _extract_numeric
from ..repository import ProjectRepository
from ..schemas import (
    CohortDiscoveryResult,
    DeviationDirection,
    PeerTrajectoryResult,
    TrajectoryMetricComparison,
)


class PeerTrajectoryEngine:
    """Compares the multi-snapshot evolutionary trajectory of a target against its peer cohort."""

    def __init__(self, repository: ProjectRepository):
        self.repository = repository

    def analyze_trajectory(
        self,
        target_project_code: str,
        cohort: CohortDiscoveryResult,
        window_snapshots: int = 6,
    ) -> PeerTrajectoryResult:
        t_code = target_project_code.strip()

        # 1. Fetch Target History
        t_history = self.repository.get_history(t_code, limit=window_snapshots)

        if len(t_history) < 2:
            return PeerTrajectoryResult(
                target_project_code=t_code,
                snapshots_analyzed=len(t_history),
                is_sufficient_history=False,
                comparisons={},
                summary=f"Project {t_code} has {len(t_history)} snapshot(s); at least 2 chronological snapshots are required for trajectory analysis.",
                source_lineage={"target_code": t_code, "snapshots_available": len(t_history)},
            )

        # 2. Compute Target Velocity
        t_deltas = self._calculate_history_deltas(t_history)

        # 3. Compute Peer Cohort Historical Velocities
        peer_deltas_pool: Dict[str, List[float]] = {
            "physical_progress_pct": [],
            "cumulative_expenditure_cr": [],
            "risk_score": [],
        }

        for peer in cohort.peers:
            p_code = peer.peer_code
            p_history = self.repository.get_history(p_code, limit=window_snapshots)
            if len(p_history) >= 2:
                p_deltas = self._calculate_history_deltas(p_history)
                for metric, rate in p_deltas.items():
                    if rate is not None:
                        peer_deltas_pool[metric].append(rate)

        # 4. Compare Target Trajectory vs Peer Medians
        comparisons: Dict[str, TrajectoryMetricComparison] = {}
        summary_lines: List[str] = []

        for metric in ["physical_progress_pct", "cumulative_expenditure_cr", "risk_score"]:
            t_rate = t_deltas.get(metric)
            peer_rates = peer_deltas_pool.get(metric, [])

            if t_rate is None or len(peer_rates) < 2:
                comparisons[metric] = TrajectoryMetricComparison(
                    metric_name=metric,
                    target_delta_per_month=t_rate,
                    peer_median_delta_per_month=float(np.median(peer_rates)) if peer_rates else None,
                    trajectory_gap=None,
                    direction=DeviationDirection.INCONCLUSIVE,
                    status="DATA_INSUFFICIENT",
                    summary=f"Insufficient peer historical snapshots to establish a trajectory baseline for '{metric}'.",
                )
                continue

            peer_median = float(np.median(peer_rates))
            gap = t_rate - peer_median

            # Direction & Interpretation
            direction, msg = self._interpret_trajectory(metric, t_rate, peer_median, gap)

            comparisons[metric] = TrajectoryMetricComparison(
                metric_name=metric,
                target_delta_per_month=t_rate,
                peer_median_delta_per_month=peer_median,
                trajectory_gap=gap,
                direction=direction,
                status="OK",
                summary=msg,
            )
            summary_lines.append(msg)

        summary = (
            "; ".join(summary_lines)
            if summary_lines
            else "Target project trajectories align with peer cohort velocity baselines."
        )

        source_lineage = {
            "target_code": t_code,
            "target_snapshots_used": len(t_history),
            "peers_with_history": len([c for c in peer_deltas_pool["physical_progress_pct"]]),
            "window_snapshots": window_snapshots,
        }

        return PeerTrajectoryResult(
            target_project_code=t_code,
            snapshots_analyzed=len(t_history),
            is_sufficient_history=True,
            comparisons=comparisons,
            summary=summary,
            source_lineage=source_lineage,
        )

    def _calculate_history_deltas(self, history: List[Dict[str, Any]]) -> Dict[str, Optional[float]]:
        """Computes average per-month change rates across consecutive historical snapshots."""
        if len(history) < 2:
            return {}

        oldest = history[0]
        latest = history[-1]

        # Determine elapsed time in months
        dt = float(len(history) - 1)
        r_old = oldest.get("report_index")
        r_new = latest.get("report_index")
        if r_old is not None and r_new is not None and r_new > r_old:
            dt = float(r_new - r_old)

        dt = max(dt, 1.0)

        deltas: Dict[str, Optional[float]] = {}
        for m in ["physical_progress_pct", "cumulative_expenditure_cr", "risk_score"]:
            v_old = _extract_numeric(oldest, m)
            v_new = _extract_numeric(latest, m)
            if v_old is not None and v_new is not None:
                deltas[m] = (v_new - v_old) / dt
            else:
                deltas[m] = None

        return deltas

    def _interpret_trajectory(
        self, metric: str, t_rate: float, p_rate: float, gap: float
    ) -> Tuple[DeviationDirection, str]:
        if metric == "physical_progress_pct":
            if gap < -0.5:
                return (
                    DeviationDirection.LAGGING_PEERS,
                    f"Physical progress advancing slower than peers (+{t_rate:.1f}%/mo vs peer median +{p_rate:.1f}%/mo; gap {gap:.1f} pts/mo)",
                )
            if gap > 0.5:
                return (
                    DeviationDirection.AHEAD_OF_PEERS,
                    f"Physical progress advancing faster than peers (+{t_rate:.1f}%/mo vs peer median +{p_rate:.1f}%/mo)",
                )
            return (
                DeviationDirection.ALIGNED_WITH_PEERS,
                f"Physical progress velocity aligned with peers (+{t_rate:.1f}%/mo vs +{p_rate:.1f}%/mo)",
            )

        if metric == "cumulative_expenditure_cr":
            if gap > 10.0:
                return (
                    DeviationDirection.SIGNIFICANTLY_ABOVE_PEERS,
                    f"Expenditure accelerating significantly faster than peers (+Rs. {t_rate:.1f} Cr/mo vs peer median +Rs. {p_rate:.1f} Cr/mo)",
                )
            return (
                DeviationDirection.ALIGNED_WITH_PEERS,
                f"Expenditure velocity comparable to peer median (+Rs. {t_rate:.1f} Cr/mo vs +Rs. {p_rate:.1f} Cr/mo)",
            )

        if metric == "risk_score":
            if gap > 2.0:
                return (
                    DeviationDirection.SIGNIFICANTLY_ABOVE_PEERS,
                    f"Risk score escalating faster than peers (+{t_rate:.1f} pts/mo vs peer median {p_rate:.1f} pts/mo)",
                )
            return (
                DeviationDirection.ALIGNED_WITH_PEERS,
                f"Risk score trajectory aligned with peers ({t_rate:.1f} pts/mo vs {p_rate:.1f} pts/mo)",
            )

        return DeviationDirection.ALIGNED_WITH_PEERS, "Trajectory aligned with cohort baselines."
