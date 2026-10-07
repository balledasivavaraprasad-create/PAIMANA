"""Evidence Coverage Evaluator.

Calculates weighted empirical coverage against declared EvidenceNeeds and
factors in source independence groups rather than simple record counts.
"""
from __future__ import annotations
from typing import Any, Optional


class EvidenceCoverageEvaluator:
    """Evaluates how thoroughly the necessary empirical evidence has been acquired."""

    @classmethod
    def evaluate_coverage(
        cls,
        state: Any,
        open_needs: Optional[list[Any]] = None,
        total_needs: Optional[list[Any]] = None
    ) -> dict[str, Any]:
        """Calculates weighted evidence coverage respecting independent source corroboration."""
        evidence_items = getattr(state, "evidence_items", [])
        evidence_groups = getattr(state, "evidence_groups", {})
        evidence_gaps = getattr(state, "evidence_gaps", [])

        # 1. Base Coverage from declared needs
        if open_needs is not None:
            if not total_needs:
                # If only open needs supplied, assess relative to tools used
                tools_used = getattr(state, "tools_used", [])
                total_count = len(open_needs) + len(tools_used)
                satisfied_count = len(tools_used)
                raw_coverage = satisfied_count / max(1, total_count)
            else:
                total_weight = sum(getattr(n, "priority", 1.0) for n in total_needs)
                open_weight = sum(getattr(n, "priority", 1.0) for n in open_needs)
                raw_coverage = max(0.0, 1.0 - (open_weight / max(0.001, total_weight)))
        elif evidence_gaps:
            # Baseline estimation from evidence gaps
            raw_coverage = max(0.10, 1.0 - (len(evidence_gaps) * 0.18))
        else:
            raw_coverage = 0.85 if len(evidence_items) >= 3 else 0.50

        # 2. Independent Group Corroboration Factor
        # High coverage demands independent corroboration, not multiple tools on the same snapshot
        tools_used = getattr(state, "tools_used", [])
        if evidence_groups:
            n_indep = len(evidence_groups)
        elif evidence_items:
            n_indep = 1
        elif tools_used:
            n_indep = min(3, len(tools_used))
        else:
            n_indep = 0

        if n_indep == 0:
            indep_mult = 0.30
        elif n_indep == 1:
            indep_mult = 0.80
        elif n_indep >= 3:
            indep_mult = 1.00
        else:
            indep_mult = 0.95

        final_coverage = min(1.0, max(0.0, raw_coverage * indep_mult))

        # 3. Facet Breakdown
        facets_present = set()
        for ev in evidence_items:
            f = getattr(ev, "facet", None) or getattr(ev, "source_system", "general")
            facets_present.add(str(f).lower())

        return {
            "evidence_coverage": round(final_coverage, 3),
            "raw_coverage": round(raw_coverage, 3),
            "independence_factor": round(indep_mult, 3),
            "independent_groups_count": n_indep,
            "evidence_count": len(evidence_items),
            "open_gaps_count": len(evidence_gaps),
            "facets_covered": list(facets_present),
            "is_sufficient": final_coverage >= 0.70,
        }
