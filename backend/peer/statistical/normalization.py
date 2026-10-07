"""Standardized Metric Normalization and Derivation Engine (SB-01).

Extracts and standardizes raw and derived metrics from project records
without modifying source project data.
"""
from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple

from .metric_registry import MetricRegistry, MetricDefinition


class MetricNormalizer:
    """Normalizes and derives infrastructure monitoring metrics."""

    def __init__(self, registry: Optional[MetricRegistry] = None):
        self.registry = registry or MetricRegistry()

    def extract_metric(self, project: Dict[str, Any], metric_id: str) -> Optional[float]:
        """Extract or derive a validated single metric value from a project dict."""
        defn = self.registry.get_metric(metric_id)
        raw_val = None

        if metric_id == "cost_overrun_pct":
            raw_val = self._extract_cost_overrun(project)
        elif metric_id == "time_slippage_months":
            raw_val = self._extract_time_slippage(project)
        elif metric_id == "physical_progress_pct":
            raw_val = self._extract_physical_progress(project)
        elif metric_id == "expenditure_pct":
            raw_val = self._extract_expenditure_pct(project)
        elif metric_id == "progress_expenditure_gap_pct":
            raw_val = self._extract_progress_expenditure_gap(project)
        elif metric_id == "progress_velocity_pct_per_month":
            raw_val = self._extract_progress_velocity(project)
        else:
            # Fallback for generic or custom registered metrics
            if defn:
                for field_name in defn.source_fields:
                    if field_name in project and project[field_name] is not None:
                        try:
                            raw_val = float(project[field_name])
                            break
                        except (ValueError, TypeError):
                            continue

        if raw_val is None:
            return None

        if math.isnan(raw_val) or math.isinf(raw_val):
            return None

        # Validate against allowed range if defined
        if defn and defn.allowed_range:
            min_val, max_val = defn.allowed_range
            if min_val is not None and raw_val < min_val:
                return None
            if max_val is not None and raw_val > max_val:
                return None

        return round(float(raw_val), 4)

    def extract_cohort_series(
        self,
        cohort: List[Dict[str, Any]],
        metric_id: str
    ) -> Tuple[List[float], Dict[str, int]]:
        """Extract a clean list of float metric values from a peer cohort.

        Returns (valid_values, stats_dict).
        """
        valid_values: List[float] = []
        missing_count = 0
        out_of_bounds_count = 0

        for p in cohort:
            val = self.extract_metric(p, metric_id)
            if val is not None:
                valid_values.append(val)
            else:
                missing_count += 1

        stats = {
            "total_candidates": len(cohort),
            "valid_count": len(valid_values),
            "missing_count": missing_count,
        }
        return valid_values, stats

    def _extract_cost_overrun(self, p: Dict[str, Any]) -> Optional[float]:
        for k in ("cost_overrun_pct", "cost_escalation_pct", "cost_overrun"):
            if k in p and p[k] is not None:
                try:
                    return float(p[k])
                except (ValueError, TypeError):
                    pass

        # Derivation from revised and original cost
        orig = p.get("original_cost") if p.get("original_cost") is not None else p.get("original_cost_cr")
        rev = p.get("revised_cost") if p.get("revised_cost") is not None else p.get("revised_cost_cr")
        if orig is not None and rev is not None:
            try:
                orig_f = float(orig)
                rev_f = float(rev)
                if orig_f > 0:
                    return ((rev_f - orig_f) / orig_f) * 100.0
            except (ValueError, TypeError):
                pass
        return None

    def _extract_time_slippage(self, p: Dict[str, Any]) -> Optional[float]:
        for k in ("schedule_slippage_months", "schedule_delay_months", "time_slippage_months", "delay_months"):
            if k in p and p[k] is not None:
                try:
                    val = float(p[k])
                    return max(0.0, val)
                except (ValueError, TypeError):
                    pass

        # Derivation from revised duration vs planned duration
        planned = p.get("planned_duration_months")
        revised = p.get("revised_duration_months")
        if planned is not None and revised is not None:
            try:
                p_f = float(planned)
                r_f = float(revised)
                return max(0.0, r_f - p_f)
            except (ValueError, TypeError):
                pass
        return None

    def _extract_physical_progress(self, p: Dict[str, Any]) -> Optional[float]:
        for k in ("physical_progress_pct", "physical_progress", "progress_pct"):
            if k in p and p[k] is not None:
                try:
                    val = float(p[k])
                    if 0.0 < val <= 1.0:
                        val = val * 100.0
                    return val
                except (ValueError, TypeError):
                    pass
        return None

    def _extract_expenditure_pct(self, p: Dict[str, Any]) -> Optional[float]:
        for k in ("expenditure_pct", "financial_progress_pct", "financial_progress"):
            if k in p and p[k] is not None:
                try:
                    val = float(p[k])
                    if 0.0 < val <= 1.0:
                        val = val * 100.0
                    return val
                except (ValueError, TypeError):
                    pass

        exp = p.get("cumulative_expenditure") if p.get("cumulative_expenditure") is not None else p.get("cumulative_expenditure_cr")
        orig = p.get("original_cost") if p.get("original_cost") is not None else p.get("original_cost_cr")
        if exp is not None and orig is not None:
            try:
                exp_f = float(exp)
                orig_f = float(orig)
                if orig_f > 0:
                    return (exp_f / orig_f) * 100.0
            except (ValueError, TypeError):
                pass
        return None

    def _extract_progress_expenditure_gap(self, p: Dict[str, Any]) -> Optional[float]:
        for k in ("progress_expenditure_gap_pct", "expenditure_progress_gap"):
            if k in p and p[k] is not None:
                try:
                    return float(p[k])
                except (ValueError, TypeError):
                    pass

        exp_pct = self._extract_expenditure_pct(p)
        prog_pct = self._extract_physical_progress(p)
        if exp_pct is not None and prog_pct is not None:
            # Positive gap indicates expenditure leads physical progress (front-loading / risk signal)
            return exp_pct - prog_pct
        return None

    def _extract_progress_velocity(self, p: Dict[str, Any]) -> Optional[float]:
        for k in ("progress_velocity_pct_per_month", "velocity_pct_per_month"):
            if k in p and p[k] is not None:
                try:
                    return float(p[k])
                except (ValueError, TypeError):
                    pass

        prog = self._extract_physical_progress(p)
        age = p.get("project_age_months") or p.get("actual_duration_months")
        if prog is not None and age is not None:
            try:
                age_f = float(age)
                if age_f > 0:
                    return prog / age_f
            except (ValueError, TypeError):
                pass
        return None
