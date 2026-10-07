"""Candidate Validator enforcing hard governance, evidence validity, authority, and safety boundaries."""
from __future__ import annotations
from typing import Any, Optional
from .candidate import RecommendationCandidate


class CandidateValidator:
    """Enforces pre-scoring validation gates across evidence, hypothesis alignment, authority, and policy."""

    def validate_candidate(
        self,
        candidate: RecommendationCandidate,
        state: Any,
        unsuccessful_precedents: list[dict],
        is_mega_project: bool = False
    ) -> bool:
        """Validates a single candidate. Sets validation_status and validation_reasons."""
        reasons: list[str] = []
        status = "VALID"

        # --------------------------------------------------------------------
        # Gate 1: Evidence Validity
        # --------------------------------------------------------------------
        # Candidate must cite some evidence or rationale
        if not candidate.evidence_ids and not candidate.supporting_evidence:
            if status == "VALID":
                status = "INSUFFICIENT_EVIDENCE"
            reasons.append("Rejected: Candidate lacks supporting evidence citations.")

        # Check for hallucinated / non-existent evidence IDs
        state_ev_items = getattr(state, "evidence_items", [])
        if state_ev_items:
            state_ev_ids = {e.id for e in state_ev_items}
            cited_ids = candidate.evidence_ids

            # If explicit formal IDs (e.g. E1, ev_...) are cited, verify they exist in state
            invalid_eids = [eid for eid in cited_ids if eid.startswith(("E", "ev_")) and eid not in state_ev_ids]
            if invalid_eids:
                if status == "VALID":
                    status = "REJECTED"
                reasons.append(f"Rejected: Cites non-existent or hallucinated evidence ID(s): {', '.join(invalid_eids)}.")

        # --------------------------------------------------------------------
        # Gate 2: Hypothesis Alignment
        # --------------------------------------------------------------------
        # If the candidate targets specific hypotheses, check they exist and are not rejected/falsified
        state_hypotheses = getattr(state, "hypotheses", [])
        if state_hypotheses and candidate.hypothesis_ids:
            active_hypo_ids = {h.id for h in state_hypotheses if getattr(h, "status", "").lower() not in ["rejected", "falsified", "disproven"]}
            matching_hypos = [hid for hid in candidate.hypothesis_ids if hid in active_hypo_ids]
            if not matching_hypos and candidate.action_type not in ["DATA_REFRESH", "BASELINE_REVIEW", "FORENSIC_AUDIT"]:
                if status == "VALID":
                    status = "REJECTED"
                reasons.append(f"Rejected: Misaligned with active hypotheses. Targeted hypotheses ({', '.join(candidate.hypothesis_ids)}) are rejected or inactive.")

        # --------------------------------------------------------------------
        # Gate 3: Policy & Precedent History Check
        # --------------------------------------------------------------------
        for bad in unsuccessful_precedents:
            bad_dict = bad if isinstance(bad, dict) else (bad.to_dict() if hasattr(bad, "to_dict") else {})
            bad_act = (bad_dict.get("action", "") or bad_dict.get("intervention", {}).get("action", "") or bad_dict.get("title", "")).lower()
            p_code = bad_dict.get("project_code") or bad_dict.get("source_project_id") or bad_dict.get("id", "HIST-PRE")
            p_out = bad_dict.get("outcome") or bad_dict.get("observed_outcome", {}).get("notes") or bad_dict.get("attribution_class", "FAILED")
            if bad_act and (bad_act in candidate.title.lower() or bad_act in candidate.rationale.lower()):
                status = "POLICY_VIOLATION"
                reasons.append(f"Rejected: Action previously failed on project {p_code} with outcome '{p_out}'.")
            elif any(term in candidate.title.lower() and term in bad_act for term in ["penalty", "show-cause", "liquidated damages", "freeze escrow"]):
                status = "POLICY_VIOLATION"
                reasons.append(f"Rejected: Action '{candidate.title}' matches known failure pattern from project {p_code} ({p_out}).")

        # --------------------------------------------------------------------
        # Gate 4: Authority & Mega-Project Governance Rules
        # --------------------------------------------------------------------
        auth = candidate.responsible_stakeholder
        if is_mega_project and candidate.urgency == "CRITICAL":
            if not any(title in auth for title in ["Ministry", "Chief", "Director", "Advisor", "Secretary"]):
                if status == "VALID":
                    status = "REQUIRES_HIGHER_AUTHORITY"
                reasons.append("Rejected: Critical mega-project action must be assigned to Ministry or Chief Engineer level authority.")

        if candidate.approval_class == "statutory" and not any(k in auth.lower() for k in ["secretary", "apex", "ministry", "cabinet"]):
            if status == "VALID":
                status = "REQUIRES_HIGHER_AUTHORITY"
            reasons.append("Rejected: Statutory approval action must be assigned to State Chief Secretary or Apex Committee.")

        # --------------------------------------------------------------------
        # Gate 5: Implementation Risk Cap
        # --------------------------------------------------------------------
        if candidate.implementation_risk > 0.85:
            if status == "VALID":
                status = "HIGH_RISK_ACTION"
            reasons.append(f"Rejected: Implementation risk ({candidate.implementation_risk:.2f}) exceeds safety ceiling (0.85).")

        # --------------------------------------------------------------------
        # Gate 6: Causal Support Calibration (Action Aggressiveness Bounded by Causal Support)
        # --------------------------------------------------------------------
        leading_causal = getattr(state, "leading_causal_claim", None)
        is_punitive = any(w in candidate.title.lower() or w in candidate.rationale.lower()
                          for w in ["liquidated damages", "contract termination", "forfeit bank guarantee", "penalize contractor", "blacklisting"])
        if is_punitive:
            if leading_causal:
                if isinstance(leading_causal, dict):
                    causal_level = leading_causal.get("causal_level", "LEVEL_0_OBSERVATION")
                    causal_score = float(leading_causal.get("causal_support_score", 0.0))
                else:
                    causal_level = getattr(leading_causal, "causal_level", "LEVEL_0_OBSERVATION")
                    causal_score = float(getattr(leading_causal, "causal_support_score", 0.0))
            else:
                causal_level = "LEVEL_0_OBSERVATION"
                causal_score = 0.0

            if causal_level in ["LEVEL_0_OBSERVATION", "LEVEL_1_ASSOCIATION", "LEVEL_2_TEMPORAL_ASSOCIATION"] or causal_score < 0.60:
                if status == "VALID":
                    status = "PREMATURE_ESCALATION"
                reasons.append(f"Rejected: Punitive contractual escalation requires Level 4 Strong Causal Support; current evidence only established {causal_level} (support={causal_score:.2f}).")

        candidate.validation_status = status
        candidate.validation_reasons = reasons
        candidate.validated = (status == "VALID")
        return candidate.validated

    def validate_all(
        self,
        candidates: list[RecommendationCandidate],
        state: Any,
        unsuccessful_precedents: list[dict],
        is_mega_project: bool = False
    ) -> list[RecommendationCandidate]:
        """Validates all candidates and returns only those that pass hard gates."""
        validated: list[RecommendationCandidate] = []
        for cand in candidates:
            if self.validate_candidate(cand, state, unsuccessful_precedents, is_mega_project):
                validated.append(cand)
        return validated

    def validate_candidates(
        self,
        candidates: list[RecommendationCandidate],
        unsuccessful_precedents: list[dict],
        is_mega_project: bool,
        state: Any = None
    ) -> list[RecommendationCandidate]:
        """Backward-compatible alias for validate_all."""
        return self.validate_all(candidates, state, unsuccessful_precedents, is_mega_project)
