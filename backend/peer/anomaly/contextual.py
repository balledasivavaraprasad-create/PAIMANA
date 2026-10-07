"""Context-Aware Anomaly Detection Engine (DO-06).

Adjusts anomaly screening thresholds and evaluates contextual deviations
conditioned on project sector, stage-bracket, cost band, and contract structure.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class ContextualThresholdProfile:
    """Configured threshold parameters adapted for a specific project context."""
    metric_name: str
    stage_bracket: str  # EARLY, MID, LATE
    sector: str
    modified_z_threshold: float = 3.5
    iqr_multiplier: float = 1.5
    percentile_threshold: float = 90.0
    practical_threshold_high: float = 20.0
    practical_threshold_critical: float = 35.0


class ContextualDetector:
    """Adjusts detection parameters based on operational project context."""

    @classmethod
    def resolve_stage_bracket(cls, physical_progress_pct: Optional[float]) -> str:
        """Categorize execution progress into operational stage bracket."""
        if physical_progress_pct is None:
            return "MID"
        if physical_progress_pct < 25.0:
            return "EARLY"
        if physical_progress_pct > 75.0:
            return "LATE"
        return "MID"

    @classmethod
    def get_contextual_profile(
        cls,
        metric_name: str,
        target_project: Dict[str, Any],
    ) -> ContextualThresholdProfile:
        """Derive customized threshold profile based on target project context."""
        prog = target_project.get("physical_progress_pct")
        stage = cls.resolve_stage_bracket(prog)
        sector = str(target_project.get("sector") or "General")

        mod_z = 3.5
        iqr_mult = 1.5
        pct_thresh = 90.0
        prac_high = 20.0
        prac_crit = 35.0

        # Adjust for stage sensitivity
        if stage == "EARLY":
            # Early projects exhibit natural volatility in initial milestones
            if metric_name in ("schedule_slippage_months", "time_slippage_months"):
                mod_z = 4.0
                iqr_mult = 2.0
                pct_thresh = 92.0
            elif metric_name in ("progress_expenditure_gap_pct", "expenditure_pct"):
                # Mobilization advances can create early apparent gaps
                prac_high = 25.0
                prac_crit = 45.0
        elif stage == "LATE":
            # Late stage projects have less room to absorb further slippage or cost escalation
            if metric_name in ("cost_overrun_pct", "progress_expenditure_gap_pct"):
                mod_z = 3.0
                pct_thresh = 85.0
                prac_high = 15.0
                prac_crit = 25.0

        return ContextualThresholdProfile(
            metric_name=metric_name,
            stage_bracket=stage,
            sector=sector,
            modified_z_threshold=mod_z,
            iqr_multiplier=iqr_mult,
            percentile_threshold=pct_thresh,
            practical_threshold_high=prac_high,
            practical_threshold_critical=prac_crit,
        )
