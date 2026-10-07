"""Explanatory Coverage Evaluator.

Checks whether current active hypotheses sufficiently explain all observed material evidence,
classifying each material evidence item into EXPLAINED, PARTIALLY_EXPLAINED, UNEXPLAINED, or CONTRADICTORY.
"""
from __future__ import annotations
import logging
from typing import Any
from .model import Evidence

logger = logging.getLogger("paimana_agent.evidence.coverage")


class ExplanatoryCoverageEvaluator:
    """Evaluates how well a set of active hypotheses accounts for observed evidence."""

    def evaluate_coverage(self, evidence_items: list[Evidence], hypotheses: list[Any]) -> dict:
        """Evaluates coverage of each material evidence item against active hypotheses.
        
        Returns:
            dict containing:
                - coverage_ratio (float): fraction of material evidence explained
                - unexplained_evidence (list[Evidence]): evidence with no explanatory hypothesis
                - partially_explained_evidence (list[Evidence])
                - contradicted_evidence (list[Evidence])
                - coverage_by_evidence_id (dict[str, str])
        """
        active_hypotheses = [h for h in hypotheses if getattr(h, "status", "").lower() in ["active", "supported", "primary", "competing"]]
        material_items = [e for e in evidence_items if e.is_material]

        unexplained: list[Evidence] = []
        partially_explained: list[Evidence] = []
        contradicted: list[Evidence] = []
        explained_count = 0
        coverage_map: dict[str, str] = {}

        for ev in material_items:
            # Check which active hypotheses support, contradict, or mention this evidence
            supporting_h = [h for h in active_hypotheses if ev.id in getattr(h, "support_evidence_ids", getattr(h, "supporting_evidence_ids", [])) or getattr(h, "id", getattr(h, "name", "")) in ev.supports_hypotheses]
            contradicting_h = [h for h in active_hypotheses if ev.id in getattr(h, "contradiction_evidence_ids", getattr(h, "contradicting_evidence_ids", [])) or getattr(h, "id", getattr(h, "name", "")) in ev.contradicts_hypotheses]

            # Domain keyword match for predicted observations
            if not supporting_h:
                claim_lower = ev.claim.lower()
                for h in active_hypotheses:
                    preds = getattr(h, "predicted_observations", [])
                    mech = getattr(h, "mechanism", "").lower()
                    stmt = getattr(h, "statement", getattr(h, "hypothesis", "")).lower()
                    
                    # Direct check if statement or mechanism predicts this evidence
                    if any(p.lower() in claim_lower or claim_lower in p.lower() for p in preds):
                        supporting_h.append(h)
                    elif ("spend" in claim_lower or "gap" in claim_lower or "disburs" in claim_lower) and ("billing" in stmt or "spend" in stmt or "decoupling" in stmt):
                        supporting_h.append(h)
                    elif ("slip" in claim_lower or "delay" in claim_lower or "months" in claim_lower) and ("delay" in stmt or "schedule" in stmt or "bottleneck" in stmt):
                        supporting_h.append(h)
                    elif ("clearance" in claim_lower or "row" in claim_lower or "approval" in claim_lower) and ("clearance" in stmt or "regulatory" in stmt or "land" in stmt):
                        supporting_h.append(h)
                    elif ("lag" in claim_lower or "mpr" in claim_lower or "inconsistency" in claim_lower) and ("reporting" in stmt or "discrepancy" in stmt):
                        supporting_h.append(h)

            if contradicting_h and not supporting_h:
                status = "CONTRADICTORY"
                contradicted.append(ev)
            elif len(supporting_h) >= 1:
                status = "EXPLAINED"
                explained_count += 1
            elif any(word in ev.claim.lower() for word in ["precedent", "cohort", "benchmark", "history"]):
                status = "PARTIALLY_EXPLAINED"
                partially_explained.append(ev)
                explained_count += 0.5
            else:
                status = "UNEXPLAINED"
                unexplained.append(ev)

            ev.coverage_status = status
            coverage_map[ev.id] = status

        total_mat = len(material_items)
        ratio = (explained_count / total_mat) if total_mat > 0 else 1.0

        return {
            "coverage_ratio": round(min(1.0, ratio), 3),
            "total_material_evidence": total_mat,
            "explained_count": int(explained_count),
            "unexplained_evidence": unexplained,
            "partially_explained_evidence": partially_explained,
            "contradicted_evidence": contradicted,
            "coverage_by_evidence_id": coverage_map,
            "is_coverage_complete": len(unexplained) == 0 and len(contradicted) == 0,
        }
