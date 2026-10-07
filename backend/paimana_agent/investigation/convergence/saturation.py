"""Evidence Saturation Detector.

Detects when additional observations come from the same underlying data lineage
or source independence group without altering hypothesis support scores,
indicating that the available information channel has reached saturation.
"""
from __future__ import annotations
from typing import Any


class EvidenceSaturationDetector:
    """Detects information saturation where additional tools duplicate existing evidence."""

    @classmethod
    def detect_saturation(
        cls,
        state: Any,
        recent_tool_executions: list[Any],
        delta_threshold: float = 0.03
    ) -> dict[str, Any]:
        """Examines recent tool outputs and hypothesis delta to detect saturation."""
        evidence_items = getattr(state, "evidence_items", [])
        evidence_groups = getattr(state, "evidence_groups", {})

        if len(recent_tool_executions) < 2:
            return {
                "is_saturated": False,
                "saturation_rationale": "Insufficient execution history to evaluate saturation.",
                "redundant_groups": [],
            }

        # Check independence group diversity in recent tools
        recent_groups = set()
        for ev in evidence_items[-6:]:
            gid = getattr(ev, "independence_group_id", getattr(ev, "independence_group", None))
            if gid:
                recent_groups.add(str(gid))

        # Check hypothesis delta trajectory if available in state
        conf_history = getattr(state, "confidence_history", [])
        recent_deltas = []
        if len(conf_history) >= 2:
            for i in range(max(0, len(conf_history) - 3), len(conf_history)):
                upd = conf_history[i]
                d = abs(getattr(upd, "delta", getattr(upd, "support_delta", 0.0)))
                recent_deltas.append(d)

        mean_delta = (sum(recent_deltas) / len(recent_deltas)) if recent_deltas else 0.50

        # Saturation condition: >= 3 tools executed, but <= 1 distinct new independence group added
        # and hypothesis delta is negligible (< 0.03)
        tools_used = getattr(state, "tools_used", [])
        is_saturated = (len(tools_used) >= 3 and len(recent_groups) <= 1 and mean_delta <= delta_threshold)

        rationale = ""
        if is_saturated:
            rationale = (
                f"Evidence channel saturated: last {len(tools_used)} tools produced no distinct "
                f"independent sources and hypothesis delta remained negligible ({mean_delta:.3f} <= {delta_threshold})."
            )

        return {
            "is_saturated": is_saturated,
            "saturation_rationale": rationale,
            "recent_groups_count": len(recent_groups),
            "mean_recent_delta": round(mean_delta, 3),
        }
