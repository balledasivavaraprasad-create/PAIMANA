"""Causal Engine and Mechanism Verification Pipeline.

Evaluates competing causal explanations against evidence, verifies intermediate
mechanism transmission links, enforces temporal precedence, checks falsification
criteria, and assigns strict Causal Claim Levels (Level 0 - 5).
"""
from __future__ import annotations
import time
from typing import Any, Optional
from .models import (
    CausalClaim, CausalMechanism, CausalClaimLevel, CausalClaimStatus,
    CausalConclusionStatus, CausalGraph, CausalGraphNode, CausalGraphEdge,
    TemporalRelation, Confounder
)
from .ontology import CausalOntology
from .temporal_reasoner import TemporalReasoner
from .confounder_detector import ConfounderDetector
from .counterfactual import CounterfactualAnalyzer


class CausalEngine:
    """Core analytical pipeline for testing competing causal mechanisms."""

    @classmethod
    def evaluate_mechanism_links(
        cls,
        mechanism: CausalMechanism,
        observations: dict[str, Any],
        facts_text: str
    ) -> float:
        """Verifies whether intermediate variables in the transmission chain have observational support."""
        text_lower = (facts_text + " " + str(observations)).lower()
        verified_count = 0
        total_links = max(1, len(mechanism.intermediate_variables))

        for var in mechanism.intermediate_variables:
            var_terms = var.replace("_", " ").split()
            # If at least half the terms of an intermediate variable are observed
            matches = sum(1 for t in var_terms if t in text_lower)
            is_verified = (matches >= max(1, len(var_terms) // 2))
            mechanism.links_verified[var] = is_verified
            if is_verified:
                verified_count += 1

        score = verified_count / total_links
        mechanism.is_validated = (score >= 0.60)
        return round(score, 3)

    GENERIC_STOP_WORDS = {
        "progress", "financial", "project", "contractor", "site", "report",
        "reports", "audit", "schedule", "cost", "data", "portal", "work"
    }

    @classmethod
    def check_falsification_criteria(
        cls,
        mechanism: CausalMechanism,
        facts_text: str,
        observations: dict[str, Any]
    ) -> tuple[bool, list[str]]:
        """Checks if any explicit falsifying observations are present."""
        text_lower = (facts_text + " " + str(observations)).lower()
        active_falsifiers = []

        for falsifier in mechanism.falsifying_observations:
            terms = [
                w.strip(".,;:()") for w in falsifier.lower().split()
                if len(w.strip(".,;:()")) > 3 and w.strip(".,;:()") not in cls.GENERIC_STOP_WORDS
            ]
            if not terms:
                terms = [w.strip(".,;:()") for w in falsifier.lower().split() if len(w.strip(".,;:()")) > 3]
            match_count = sum(1 for t in terms if t in text_lower)
            needed = max(3, int(len(terms) * 0.6))
            if match_count >= needed:
                active_falsifiers.append(falsifier)

        has_falsification = len(active_falsifiers) > 0
        return has_falsification, active_falsifiers

    @classmethod
    def evaluate_causal_claim(
        cls,
        claim_id: str,
        proposed_cause: str,
        observed_effect: str,
        observations: dict[str, Any],
        evidence_items: list[dict],
        cause_timestamp: Optional[float] = None,
        effect_timestamp: Optional[float] = None,
        intermediate_timestamps: Optional[list[tuple[str, float]]] = None,
        peer_data: Optional[dict[str, Any]] = None,
        is_intervention_verified: bool = False,
        hypothesis_id: Optional[str] = None
    ) -> CausalClaim:
        """Evaluates a candidate cause against temporal order, mechanisms, confounders, and falsifiers."""
        # 1. Mechanism Lookup & Instantiation
        mechanism = CausalOntology.match_mechanism_for_cause(proposed_cause)
        mech_id = mechanism.id if mechanism else None

        # Build combined facts text
        facts_text = " ".join([
            str(e.get("claim", "")) or str(e.get("statement", "")) or str(e)
            for e in evidence_items
        ])

        # 2. Mechanistic Verification
        if mechanism:
            mech_support = cls.evaluate_mechanism_links(mechanism, observations, facts_text)
            has_falsification, active_falsifiers = cls.check_falsification_criteria(mechanism, facts_text, observations)
        else:
            mech_support = 0.35  # Unsupported novel mechanism
            has_falsification, active_falsifiers = False, []

        # 3. Temporal Precedence Validation
        temporal_rel = TemporalReasoner.evaluate_temporal_order(
            cause_event=proposed_cause,
            effect_event=observed_effect,
            cause_timestamp=cause_timestamp,
            effect_timestamp=effect_timestamp,
            intermediate_events=intermediate_timestamps
        )
        temporal_support = TemporalReasoner.calculate_temporal_support(temporal_rel)

        # 4. Confounder Detection
        confounders = ConfounderDetector.detect_confounders(
            proposed_cause=proposed_cause,
            observed_effect=observed_effect,
            observations=observations,
            evidence_claims=[str(e.get("claim", "")) for e in evidence_items]
        )
        confounder_penalty = ConfounderDetector.calculate_confounder_penalty(confounders)
        unresolved_conf_names = [c.variable for c in confounders if not c.resolved]

        # 5. Counterfactual Analysis
        cf_proxy = CounterfactualAnalyzer.evaluate_counterfactual(
            proposed_cause=proposed_cause,
            observed_effect=observed_effect,
            project_data=observations,
            peer_data=peer_data
        )
        cf_support = 0.85 if cf_proxy.supports_causality else 0.40

        # 6. Independent Evidence Scoring
        unique_groups = set()
        for e in evidence_items:
            gid = e.get("independence_group_id") or e.get("independence_group") or e.get("source_id")
            if gid:
                unique_groups.add(str(gid))
        n_groups = len(unique_groups)
        independent_ev_score = min(1.0, 0.40 + 0.20 * n_groups)

        # 7. Contradiction Penalty
        contra_penalty = 0.50 if has_falsification or not temporal_rel.temporal_consistency else 0.0

        # 8. Composite Causal Support Calculation
        raw_support = (
            0.30 * temporal_support +
            0.30 * mech_support +
            0.25 * independent_ev_score +
            0.15 * cf_support
        )
        if is_intervention_verified:
            # Empirical intervention closing the loop provides strong real-world confirmation
            raw_support = min(1.0, raw_support + 0.15)

        composite = max(0.05, raw_support - confounder_penalty - contra_penalty)

        # 9. Strict Causal Claim Level Assignment
        # RULE 1: Never convert correlation into causal language if support < Level 4!
        # RULE 2: SHAP ≠ causality (model-derived evidence alone cannot exceed Level 1)
        has_empirical_evidence = any(
            e.get("evidence_type") not in ("MODEL_DERIVED", "model_attribution") and
            "shap" not in str(e.get("source_tool", "")).lower() and
            "shap" not in str(e.get("claim", "")).lower()
            for e in evidence_items
        ) if evidence_items else False
        only_shap = bool(evidence_items) and not has_empirical_evidence

        falsification_notes = list(active_falsifiers)
        if not temporal_rel.temporal_consistency and temporal_rel.inconsistency_reason:
            falsification_notes.append(temporal_rel.inconsistency_reason)

        if only_shap:
            level: CausalClaimLevel = "LEVEL_1_ASSOCIATION"
            status: CausalClaimStatus = "CANDIDATE"
            bracket = "LOW"
            composite = min(0.40, composite)
            falsification_notes.append("SHAP attribution reflects ML model feature sensitivity and does not constitute ground-truth physical causality.")
        elif not temporal_rel.temporal_consistency or has_falsification:
            level = "LEVEL_1_ASSOCIATION"
            status = "REJECTED" if not temporal_rel.temporal_consistency else "WEAKENED"
            bracket = "INSUFFICIENT"
        elif is_intervention_verified and composite >= 0.70:
            level = "LEVEL_5_INTERVENTION_SUPPORTED"
            status = "SUPPORTED"
            bracket = "STRONG"
        elif composite >= 0.75 and n_groups >= 2 and mech_support >= 0.60 and not unresolved_conf_names:
            level = "LEVEL_4_STRONG_CAUSAL_SUPPORT"
            status = "SUPPORTED"
            bracket = "STRONG"
        elif composite >= 0.55 and mech_support >= 0.50 and temporal_support >= 0.50:
            level = "LEVEL_3_MECHANISTIC_SUPPORT"
            status = "PLAUSIBLE"
            bracket = "MODERATE"
        elif temporal_support >= 0.70:
            level = "LEVEL_2_TEMPORAL_ASSOCIATION"
            status = "PLAUSIBLE"
            bracket = "MODERATE"
        elif composite >= 0.35:
            level = "LEVEL_1_ASSOCIATION"
            status = "CANDIDATE"
            bracket = "LOW"
        else:
            level = "LEVEL_0_OBSERVATION"
            status = "UNRESOLVED"
            bracket = "INSUFFICIENT"

        actionable_node = mechanism.actionable_node if mechanism else None
        responsible_auth = mechanism.actionable_stakeholder if mechanism else None

        counterfactual_notes = [cf_proxy.notes] if cf_proxy.notes else []
        if observations.get("memory_retrieval", {}).get("successful_precedents"):
            counterfactual_notes.append("Historical precedent retrieved for cross-project transferability; does not substitute for empirical site verification on current project.")

        return CausalClaim(
            id=claim_id,
            effect=observed_effect,
            proposed_cause=proposed_cause,
            mechanism_id=mech_id,
            mechanism=mechanism,
            evidence_for_ids=[str(e.get("id", i)) for i, e in enumerate(evidence_items)],
            evidence_against_ids=[],
            temporal_support=temporal_support,
            mechanistic_support=mech_support,
            independent_evidence_score=independent_ev_score,
            alternative_cause_penalty=0.0,
            confounder_penalty=confounder_penalty,
            contradiction_penalty=contra_penalty,
            causal_support_score=round(composite, 3),
            causal_level=level,
            causal_support_bracket=bracket,
            status=status,
            unresolved_confounders=unresolved_conf_names,
            falsification_notes=falsification_notes,
            actionable_intervention=actionable_node,
            responsible_authority=responsible_auth,
            counterfactual_notes=counterfactual_notes,
            hypothesis_id=hypothesis_id
        )

    @classmethod
    def compare_competing_explanations(
        cls,
        claims: list[CausalClaim]
    ) -> tuple[Optional[CausalClaim], list[CausalClaim], CausalConclusionStatus, str]:
        """Compares multiple competing causal claims and determines the qualified conclusion."""
        if not claims:
            return None, [], "INSUFFICIENT_CAUSAL_EVIDENCE", "No causal candidate claims available for evaluation."

        # Filter active candidates
        active_claims = [c for c in claims if c.status not in {"REJECTED"}]
        if not active_claims:
            return None, [], "INSUFFICIENT_CAUSAL_EVIDENCE", "All candidate causal explanations were disproved or rejected."

        # Sort by causal support score descending
        active_claims.sort(key=lambda c: c.causal_support_score, reverse=True)
        top = active_claims[0]
        alternatives = active_claims[1:]

        # Check for unresolved conflict (top two are too close)
        if len(active_claims) >= 2:
            runner_up = active_claims[1]
            margin = top.causal_support_score - runner_up.causal_support_score

            # Penalize alternative causes
            top.alternative_cause_penalty = round(max(0.0, 0.30 - margin), 3)

            if margin < 0.15 and top.causal_support_score < 0.80:
                conclusion_status: CausalConclusionStatus = "UNRESOLVED_CAUSAL_CONFLICT"
                summary = (
                    f"Unresolved Causal Conflict: Competing explanations '{top.proposed_cause}' (score={top.causal_support_score}) "
                    f"and '{runner_up.proposed_cause}' (score={runner_up.causal_support_score}) are closely matched. "
                    f"Current observations cannot distinguish between them. Both must be retained as active alternatives."
                )
                return top, alternatives, conclusion_status, summary

        # Check if top claim has sufficient support
        if top.causal_support_score < 0.40 or top.causal_level in {"LEVEL_0_OBSERVATION", "LEVEL_1_ASSOCIATION"}:
            conclusion_status = "INSUFFICIENT_CAUSAL_EVIDENCE"
            summary = (
                f"Insufficient Causal Evidence: Leading association '{top.proposed_cause}' achieved only {top.causal_level} "
                f"(support={top.causal_support_score}). Causality cannot be claimed without intermediate verification."
            )
            return top, alternatives, conclusion_status, summary

        # Legitimate leading causal explanation
        conclusion_status = "PRIMARY_CAUSAL_EXPLANATION"
        alt_names = [a.proposed_cause for a in alternatives[:2]]
        summary = (
            f"Leading Causal Explanation: '{top.proposed_cause}' [{top.causal_level}, support={top.causal_support_score}]. "
            f"Mechanistic support={top.mechanistic_support}, temporal support={top.temporal_support}. "
            f"Retained alternatives: {alt_names if alt_names else 'None'}."
        )
        return top, alternatives, conclusion_status, summary
