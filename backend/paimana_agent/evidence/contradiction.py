"""Evidence Contradiction Detector.

Identifies explicit empirical contradictions across evidence records from distinct independence groups.
"""
from __future__ import annotations
from typing import Optional
from .model import Evidence


class ContradictionDetector:
    """Detects cross-source data discrepancies across evidence items."""

    def detect_contradictions(self, evidence_items: list[Evidence], project: dict) -> list[dict]:
        contradictions = []

        # Find schedule evidence vs physical execution
        sched_ev = next((e for e in evidence_items if e.source_tool in ["cuf_milestone_schedule", "milestone_audit"]), None)
        phys_ev = next((e for e in evidence_items if e.source_tool in ["cuf_monthly_progress_report"]), None)

        if sched_ev and phys_ev:
            prog = float(project.get("physical_progress_pct", 0.0))
            orig_d = project.get("original_completion_date")
            rev_d = project.get("revised_completion_date")
            # If dates unchanged but progress is severely stalled (<20%) on a project well into duration
            if (not rev_d or rev_d == orig_d) and prog < 20.0 and project.get("project_age_months", 0) > 30:
                contradictions.append({
                    "metric_or_claim": "schedule_progress_alignment",
                    "source_a": "Milestone Schedule (reported 0 slippage)",
                    "value_a": "0 months delay",
                    "source_b": "Physical Progress MPR (stalled at <20% on aged project)",
                    "value_b": f"{prog}% progress",
                    "impact": "Milestone dates appear unrevised despite severe on-site construction delays",
                    "evidence_ids": [sched_ev.id, phys_ev.id]
                })

        return contradictions
