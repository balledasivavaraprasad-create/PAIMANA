"""Multi-Dimensional Evidence Reliability Profiling Engine (ESS-03).

Evaluates evidence across five structured dimensions:
  1. Source Quality (Authoritative official record vs model prediction vs heuristic)
  2. Freshness (Temporal currency relative to reporting as-of date)
  3. Provenance Completeness (Presence of snapshot IDs, hashes, methodology)
  4. Methodological Quality (Mathematical formula vs ML proxy vs inference)
  5. Corroboration (Single-source vs multi-source corroboration)
Assigning categorical ReliabilityTiers: CONFIRMED, SUPPORTED, CORROBORATED, CONTEXTUAL, UNVERIFIED.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .schemas import EvidenceProvenance, EvidenceReliability, ReliabilityTier


SOURCE_QUALITY_SCORES = {
    "CUF Financial Ledger": 1.0,
    "Official Gazette": 1.0,
    "Signed Contract": 1.0,
    "Monthly Progress Report": 0.90,
    "Milestone Schedule": 0.90,
    "financial_velocity": 0.90,
    "milestone_audit": 0.90,
    "statistical_benchmark": 0.85,
    "trajectory_analysis": 0.85,
    "peer_intelligence": 0.80,
    "peer_deviation": 0.80,
    "analyze_domain_context": 0.80,
    "shap_attribution": 0.70,
    "ml_risk_model": 0.70,
    "memory_retrieval": 0.60,
    "llm_inference": 0.35,
    "user_hypothesis": 0.30,
}


class ReliabilityEvaluator:
    """Evaluates multi-dimensional evidence reliability and assigns canonical tiers."""

    @staticmethod
    def evaluate(
        source_name: str = "general",
        provenance: Optional[EvidenceProvenance] = None,
        is_corroborated: bool = False,
        methodology: str = "",
        is_stale: bool = False,
        source_quality: Optional[str] = None,
        freshness: Optional[str] = None,
        provenance_completeness: Optional[str] = None,
        methodological_quality: Optional[str] = None,
        corroboration: Optional[str] = None,
        source_category: Optional[str] = None,
        **kwargs,
    ) -> EvidenceReliability:
        # 1. Source Quality
        matched_quality = 0.50
        matched_label = source_quality or "MEDIUM"

        if source_quality:
            sq_map = {"HIGH": 0.95, "MEDIUM": 0.75, "LOW": 0.50, "MODEL_DERIVED": 0.70, "UNVERIFIED": 0.30}
            matched_quality = sq_map.get(source_quality.upper(), 0.50)
            matched_label = source_quality.upper()
        else:
            for s_key, q_score in SOURCE_QUALITY_SCORES.items():
                if s_key.lower() in source_name.lower():
                    matched_quality = q_score
                    if q_score >= 0.90:
                        matched_label = "HIGH"
                    elif q_score >= 0.70:
                        matched_label = "MEDIUM"
                    elif "ml" in s_key or "shap" in s_key:
                        matched_label = "MODEL_DERIVED"
                    else:
                        matched_label = "UNVERIFIED"
                    break

        # 2. Freshness
        if freshness:
            freshness_label = freshness.upper()
            freshness_mult = 1.0 if freshness_label == "CURRENT" else (0.90 if freshness_label == "RECENT" else 0.80)
        else:
            freshness_label = "STALE" if is_stale else "CURRENT"
            freshness_mult = 0.80 if is_stale else 1.0

        # 3. Provenance Completeness
        if provenance_completeness:
            prov_status = provenance_completeness.upper()
            prov_mult = 1.0 if prov_status == "COMPLETE" else (0.85 if prov_status == "PARTIAL" else 0.60)
        else:
            prov_status = "COMPLETE"
            prov_mult = 1.0
            if not provenance or not provenance.input_hash:
                prov_status = "PARTIAL"
                prov_mult = 0.85

        # 4. Methodological Quality
        if methodological_quality:
            meth_status = methodological_quality.upper()
            meth_mult = 1.0 if meth_status == "HIGH" else (0.85 if meth_status == "ESTIMATED" else 0.75)
        else:
            meth_status = "HIGH"
            meth_mult = 1.0
            if "heuristic" in methodology.lower() or "proxy" in methodology.lower():
                meth_status = "HEURISTIC"
                meth_mult = 0.75
            elif "ml" in methodology.lower() or "model" in methodology.lower():
                meth_status = "ESTIMATED"
                meth_mult = 0.85

        # 5. Corroboration
        if corroboration:
            corrob_status = corroboration.upper()
            corrob_mult = 1.10 if corrob_status in ("MULTI_SOURCE", "CORROBORATED") else 1.0
            is_corroborated = corrob_status in ("MULTI_SOURCE", "CORROBORATED")
        else:
            corrob_status = "CORROBORATED" if is_corroborated else "SINGLE_SOURCE"
            corrob_mult = 1.10 if is_corroborated else 1.0

        # Compute aggregate reliability score (clamped between 0.1 and 1.0)
        raw_score = matched_quality * freshness_mult * prov_mult * meth_mult * corrob_mult
        final_score = max(0.10, min(1.0, raw_score))

        # Assign Categorical Tier
        if source_category == "PEER_INTELLIGENCE":
            tier = ReliabilityTier.CONTEXTUAL
        elif matched_quality >= 0.90 and prov_status == "COMPLETE" and freshness_label == "CURRENT" and is_corroborated:
            tier = ReliabilityTier.CONFIRMED
        elif matched_quality >= 0.90 and prov_status == "COMPLETE" and freshness_label == "CURRENT":
            tier = ReliabilityTier.CONFIRMED if raw_score >= 0.90 else ReliabilityTier.SUPPORTED
        elif is_corroborated:
            tier = ReliabilityTier.CORROBORATED
        elif final_score >= 0.75:
            tier = ReliabilityTier.SUPPORTED
        elif final_score >= 0.50:
            tier = ReliabilityTier.CONTEXTUAL
        else:
            tier = ReliabilityTier.UNVERIFIED

        return EvidenceReliability(
            source_quality=matched_label,
            freshness=freshness_label,
            provenance_completeness=prov_status,
            methodological_quality=meth_status,
            corroboration=corrob_status,
            overall_tier=tier,
            reliability_score=round(final_score, 2),
        )
