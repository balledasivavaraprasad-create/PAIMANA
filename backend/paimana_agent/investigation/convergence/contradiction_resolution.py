"""Contradiction Resolution Evaluator.

Classifies contradictions by severity (LOW, MEDIUM, HIGH, CRITICAL) and evaluates
whether unresolved discrepancies block investigation termination or trigger CONTRADICTORY status.
"""
from __future__ import annotations
from typing import Any


class ContradictionResolutionEvaluator:
    """Evaluates contradiction resolution and detects blocking discrepancies."""

    SEVERITY_WEIGHTS = {
        "CRITICAL": 4.0,
        "HIGH": 3.0,
        "MEDIUM": 2.0,
        "LOW": 1.0,
    }

    @classmethod
    def evaluate_contradictions(cls, contradictions: list[Any]) -> dict[str, Any]:
        """Calculates contradiction resolution score and identifies blocking contradictions."""
        if not contradictions:
            return {
                "contradiction_resolution": 1.0,
                "total_contradictions": 0,
                "resolved_count": 0,
                "unresolved_count": 0,
                "unresolved_critical": 0,
                "unresolved_high": 0,
                "has_blocking_contradictions": False,
                "resolution_notes": "No contradictions present.",
            }

        total_weight = 0.0
        resolved_weight = 0.0
        material_weight = 0.0
        resolved_material_weight = 0.0
        unresolved_crit = 0
        unresolved_high = 0
        unresolved_med = 0
        unresolved_low = 0

        for c in contradictions:
            sev = getattr(c, "severity", "MEDIUM").upper()
            w = cls.SEVERITY_WEIGHTS.get(sev, 2.0)
            total_weight += w

            is_res = getattr(c, "resolved", False)
            if is_res:
                resolved_weight += w

            if sev in ("CRITICAL", "HIGH", "MEDIUM"):
                material_weight += w
                if is_res:
                    resolved_material_weight += w
            else:
                if not is_res:
                    unresolved_low += 1

            if not is_res:
                if sev == "CRITICAL":
                    unresolved_crit += 1
                elif sev == "HIGH":
                    unresolved_high += 1
                elif sev == "MEDIUM":
                    unresolved_med += 1

        if material_weight > 0:
            mat_score = resolved_material_weight / material_weight
        else:
            mat_score = 1.0

        # Unresolved low-severity discrepancies apply only a modest noise deduction (0.05 each, max 0.15)
        low_penalty = min(0.15, unresolved_low * 0.05)
        resolution_score = max(0.0, mat_score - low_penalty)

        # High or Critical unresolved contradictions strictly block convergence!
        has_blocking = (unresolved_crit > 0) or (unresolved_high > 0)

        notes = []
        if unresolved_crit > 0:
            notes.append(f"{unresolved_crit} critical unresolved contradiction(s) active")
        if unresolved_high > 0:
            notes.append(f"{unresolved_high} high unresolved contradiction(s) active")
        if unresolved_med > 0:
            notes.append(f"{unresolved_med} medium discrepancy active")
        if unresolved_low > 0:
            notes.append(f"{unresolved_low} minor discrepancy (non-blocking)")

        return {
            "contradiction_resolution": round(resolution_score, 3),
            "total_contradictions": len(contradictions),
            "resolved_count": sum(1 for c in contradictions if getattr(c, "resolved", False)),
            "unresolved_count": sum(1 for c in contradictions if not getattr(c, "resolved", False)),
            "unresolved_critical": unresolved_crit,
            "unresolved_high": unresolved_high,
            "has_blocking_contradictions": has_blocking,
            "resolution_notes": "; ".join(notes) if notes else "All contradictions resolved.",
        }
