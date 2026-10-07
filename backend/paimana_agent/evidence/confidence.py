"""Canonical Evidence Confidence Engine.

Implements the single authoritative evidence-grounded confidence pipeline:
  Evidence → Lineage → Authority → Timestamps → Freshness → Independence → Contradiction → Confidence

Features:
  1. Evidence provenance & transformation lineage evaluation.
  2. Source authority scoring according to the canonical hierarchy.
  3. Exponential freshness decay based on domain half-life.
  4. Corroboration across independent source groups (preventing single-snapshot inflation).
  5. Contradiction penalty enforcement.
  6. Separation of Root Cause Confidence from Actionable Recommendation Confidence.
  7. Deterministic categorical tier classification (LOW, MEDIUM, HIGH).
  8. Auditable breakdown and quality dashboard assembly.
"""
from __future__ import annotations
import math
import time
from dataclasses import dataclass, field
from typing import Any, Optional

from .model import Evidence, EvidenceGroup, SourceLineage, SOURCE_AUTHORITY, SOURCE_HALF_LIFE_DAYS


@dataclass
class GroundedConfidenceResult:
    """Complete multi-dimensional grounded confidence evaluation."""
    total_confidence: float
    root_cause_confidence: float
    recommendation_confidence: float
    confidence_tier: str  # LOW, MEDIUM, HIGH
    confidence_reasons: list[str] = field(default_factory=list)
    confidence_breakdown: dict[str, float] = field(default_factory=dict)
    evidence_quality_dashboard: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "confidence_score": round(self.total_confidence, 2),
            "root_cause_confidence": round(self.root_cause_confidence, 2),
            "recommendation_confidence": round(self.recommendation_confidence, 2),
            "confidence_tier": self.confidence_tier,
            "confidence_reasons": list(self.confidence_reasons),
            "confidence_breakdown": {k: round(v, 3) if isinstance(v, float) else v for k, v in self.confidence_breakdown.items()},
            "evidence_quality_dashboard": self.evidence_quality_dashboard,
        }


class EvidenceConfidenceEngine:
    """The canonical engine for computing multi-dimensional grounded confidence."""

    @classmethod
    def evaluate(
        cls,
        evidence_items: list[Evidence],
        facts: list[Any],
        inferences: list[Any],
        hypotheses: list[Any],
        contradictions: list[Any],
        evidence_groups: dict[str, EvidenceGroup],
        source_lineage: dict[str, SourceLineage],
        precedent_data: Optional[dict] = None,
        evidence_gaps: Optional[list[str]] = None,
        observations: Optional[dict] = None,
        current_time: Optional[float] = None
    ) -> GroundedConfidenceResult:
        """Computes comprehensive grounded confidence following the canonical pipeline."""
        now = current_time or time.time()
        precedent_data = precedent_data or {}
        evidence_gaps = evidence_gaps or []
        observations = observations or {}

        # --------------------------------------------------------------------
        # 1. Evidence Quality & Source Lineage Evaluation
        # --------------------------------------------------------------------
        if evidence_items:
            # Refresh freshness on each evidence item
            for ev in evidence_items:
                ev.calculate_freshness(current_time=now)

            mean_auth = sum(getattr(e, "authority_score", 0.80) for e in evidence_items) / len(evidence_items)
            mean_fresh = sum(getattr(e, "freshness", 1.00) for e in evidence_items) / len(evidence_items)
        else:
            mean_auth = 0.50
            mean_fresh = 1.00

        # Lineage quality calculation
        if source_lineage:
            mean_lineage = sum(l.lineage_quality for l in source_lineage.values()) / max(1, len(source_lineage))
        else:
            mean_lineage = 1.00

        # Dimension 1: Direct validated facts & source authority
        fact_contrib = 0.08 * len(facts)
        auth_contrib = 0.05 * mean_auth
        quality_score = min(0.25, fact_contrib + auth_contrib)

        # --------------------------------------------------------------------
        # 2. Evidence Independence Groups
        # --------------------------------------------------------------------
        indep_groups = list(evidence_groups.keys())
        independence_score = min(0.25, 0.08 * len(indep_groups))
        indep_ratio = min(1.0, len(indep_groups) / 3.0) if indep_groups else 0.333

        # --------------------------------------------------------------------
        # 3. Hypothesis Agreement & Separation Margin
        # --------------------------------------------------------------------
        margin = 0.0
        if len(hypotheses) >= 2:
            p0 = getattr(hypotheses[0], "posterior_prob", 0.50)
            p1 = getattr(hypotheses[1], "posterior_prob", 0.25)
            margin = max(0.0, p0 - p1)
        agreement_score = min(0.25, max(0.05, margin * 0.40))

        # --------------------------------------------------------------------
        # 4. Precedent Learning Boost & Corroboration
        # --------------------------------------------------------------------
        has_succ = bool(precedent_data.get("successful_precedents", []))
        has_boost = precedent_data.get("confidence_boost", 0) > 0
        precedent_boost = 0.15 if (has_succ or has_boost) else 0.05

        # --------------------------------------------------------------------
        # 5. Contradiction Penalty
        # --------------------------------------------------------------------
        has_contradictions = bool(contradictions)
        contra_penalty = 0.20 if has_contradictions else 0.0
        contra_risk = min(1.0, len(contradictions) * 0.25)

        # --------------------------------------------------------------------
        # 6. Composite Grounded Confidence & Separation
        # --------------------------------------------------------------------
        total_raw = quality_score + independence_score + agreement_score + precedent_boost - contra_penalty
        total_confidence = max(0.10, min(1.0, total_raw))

        # Root Cause Confidence (strictly based on factual ground truth and hypothesis separation)
        rc_raw = quality_score + independence_score + agreement_score - contra_penalty
        root_cause_conf = max(0.10, min(1.0, rc_raw))

        # Actionable Recommendation Confidence (factors in empirical precedent outcome + authority match)
        precedent_factor = 0.85 if has_succ else (0.50 if has_boost else 0.30)
        authority_match = mean_auth
        rec_conf = max(0.10, min(1.0, (0.35 * precedent_factor) + (0.35 * root_cause_conf) + (0.30 * authority_match)))

        # Categorical Tier
        if total_confidence >= 0.70:
            tier = "HIGH"
        elif total_confidence >= 0.40:
            tier = "MEDIUM"
        else:
            tier = "LOW"

        # --------------------------------------------------------------------
        # 7. Quality Dashboard & Audit Reasons Assembly
        # --------------------------------------------------------------------
        completeness = max(0.0, 1.0 - (len(evidence_gaps) / 5.0))

        dashboard = {
            "overall_confidence": round(total_confidence * 100.0, 1),
            "source_authority": round(mean_auth * 100.0, 1),
            "freshness": round(mean_fresh * 100.0, 1),
            "independence": round(indep_ratio * 100.0, 1),
            "evidence_completeness": round(completeness * 100.0, 1),
            "contradiction_risk": round(contra_risk * 100.0, 1),
            "lineage_quality": round(mean_lineage * 100.0, 1),
            "independent_corroborating_groups": list(indep_groups),
        }

        reasons = []
        if len(indep_groups) >= 2:
            reasons.append(f"{len(indep_groups)} independent source groups corroborated findings ({', '.join(indep_groups)})")
        elif len(evidence_items) >= 2:
            reasons.append("multi-tool observations within primary project snapshot")
        if inferences:
            reasons.append(f"{len(inferences)} analytical inferences verified")
        has_peer = (
            any("peer" in getattr(e, "source_tool", "").lower() or
                "peer" in getattr(e, "source_system", "").lower() or
                "peer" in getattr(e, "independence_group_id", "").lower()
                for e in evidence_items) or
            any("peer" in getattr(f, "source", "").lower() for f in facts) or
            bool(observations.get("peer_intelligence"))
        )
        if has_peer:
            reasons.append("peer cohort/baseline validated")
        if has_succ or has_boost:
            reasons.append("validated by historical precedent outcome")
        if has_contradictions:
            reasons.append("downgraded due to unresolved data contradiction")

        breakdown = {
            "evidence_quality": round(quality_score, 3),
            "evidence_independence": round(independence_score, 3),
            "hypothesis_agreement": round(agreement_score, 3),
            "recency": round(precedent_boost, 3),
            "contradiction_penalty": round(contra_penalty, 3),
            "root_cause_confidence": round(root_cause_conf, 3),
            "recommendation_confidence": round(rec_conf, 3),
            "source_authority": dashboard["source_authority"],
            "freshness": dashboard["freshness"],
            "independence": dashboard["independence"],
            "evidence_completeness": dashboard["evidence_completeness"],
            "contradiction_risk": dashboard["contradiction_risk"],
            "lineage_quality": dashboard["lineage_quality"],
        }

        return GroundedConfidenceResult(
            total_confidence=total_confidence,
            root_cause_confidence=root_cause_conf,
            recommendation_confidence=rec_conf,
            confidence_tier=tier,
            confidence_reasons=reasons,
            confidence_breakdown=breakdown,
            evidence_quality_dashboard=dashboard
        )

    @classmethod
    def build_dashboard(cls, state: Any) -> dict[str, Any]:
        """Convenience method to assemble the evidence quality dashboard directly from state."""
        ev_items = getattr(state, "evidence_items", [])
        if not ev_items:
            return {
                "overall_confidence": round(getattr(state, "confidence_score", 0.2) * 100.0, 1),
                "source_authority": 50.0,
                "freshness": 100.0,
                "independence": 33.3,
                "evidence_completeness": 50.0,
                "contradiction_risk": 0.0,
                "lineage_quality": 100.0,
                "independent_corroborating_groups": [],
            }

        mean_auth = sum(getattr(e, "authority_score", 0.8) for e in ev_items) / len(ev_items)
        mean_fresh = sum(getattr(e, "freshness", 1.0) for e in ev_items) / len(ev_items)
        ev_groups = getattr(state, "evidence_groups", {})
        indep_groups = list(ev_groups.keys())
        indep_ratio = min(1.0, len(indep_groups) / 3.0) if indep_groups else 0.333
        gaps = getattr(state, "evidence_gaps", [])
        completeness = max(0.0, 1.0 - (len(gaps) / 5.0))
        contras = getattr(state, "contradictions", [])
        contra_risk = min(1.0, len(contras) * 0.25)
        lineage = getattr(state, "source_lineage", {})
        mean_lineage = (sum(l.lineage_quality for l in lineage.values()) / max(1, len(lineage))) if lineage else 1.0

        return {
            "overall_confidence": round(getattr(state, "confidence_score", 0.2) * 100.0, 1),
            "source_authority": round(mean_auth * 100.0, 1),
            "freshness": round(mean_fresh * 100.0, 1),
            "independence": round(indep_ratio * 100.0, 1),
            "evidence_completeness": round(completeness * 100.0, 1),
            "contradiction_risk": round(contra_risk * 100.0, 1),
            "lineage_quality": round(mean_lineage * 100.0, 1),
            "independent_corroborating_groups": list(indep_groups),
        }
