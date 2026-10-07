"""[LEGACY ADAPTER] Recommendation Validator for enforcing safety and governance rules.

NOTE: This is a legacy compatibility module. The canonical candidate validator
is `CandidateValidator` in `paimana_agent.recommendations.candidate_validator`.
"""
from __future__ import annotations
from typing import Any, Optional
from ..state import RecommendationCandidate


class RecommendationValidator:
    """[LEGACY ADAPTER] Validates candidate interventions against empirical precedents and statutory authority rules.
    
    Replaced by CandidateValidator in candidate_validator.py.
    """

    def validate_candidates(
        self,
        candidates: list[RecommendationCandidate],
        unsuccessful_precedents: list[dict],
        is_mega_project: bool,
        causal_level: Optional[str] = None
    ) -> list[RecommendationCandidate]:
        """Filters and validates candidates. Returns list of approved candidates."""
        validated: list[RecommendationCandidate] = []

        for cand in candidates:
            passed = True
            reasons = []

            # Rule 1: Must cite supporting evidence
            if not cand.supporting_evidence:
                passed = False
                reasons.append("Rejected: Candidate lacks supporting evidence from facts or inferences.")

            # Rule 2: Cannot repeat known failed action
            for bad in unsuccessful_precedents:
                if isinstance(bad, dict):
                    bad_act = bad.get("action", "").lower()
                    bad_proj = bad.get("project_code", "historical precedent")
                    bad_out = bad.get("outcome", "")
                else:
                    int_dict = getattr(bad, "intervention", {}) or {}
                    bad_act = (int_dict.get("action", "") or getattr(bad, "title", "")).lower()
                    bad_proj = getattr(bad, "source_project_id", "historical precedent")
                    bad_out = str(getattr(bad, "observed_outcome", {}).get("notes", ""))

                if bad_act:
                    bad_clean = bad_act.strip().rstrip(".").lower()
                    cand_clean = cand.action.strip().rstrip(".").lower()
                    if bad_clean in cand_clean or cand_clean in bad_clean:
                        passed = False
                        reasons.append(f"Rejected: Action previously failed on project {bad_proj} with outcome '{bad_out}'.")

            # Rule 3: Mega-project critical actions require Chief Engineer / Ministry level
            if is_mega_project and cand.urgency == "CRITICAL":
                auth = cand.responsible_stakeholder
                if not any(title in auth for title in ["Ministry", "Chief", "Director", "Advisor"]):
                    passed = False
                    reasons.append("Rejected: Critical mega-project action must be assigned to Ministry or Chief Engineer level authority.")

            # Rule 4: Causal Support Calibration (Punitive escalation requires Level 4+ Causal Support)
            if causal_level is not None:
                is_punitive = any(w in cand.action.lower() for w in ["liquidated damages", "contract termination", "forfeit bank guarantee", "penalize contractor", "blacklisting"])
                if is_punitive and causal_level in ["LEVEL_0_OBSERVATION", "LEVEL_1_ASSOCIATION", "LEVEL_2_TEMPORAL_ASSOCIATION"]:
                    passed = False
                    reasons.append(f"Rejected: Punitive contractual escalation requires Level 4 Strong Causal Support; current evidence only established {causal_level}.")

            cand.validated = passed
            cand.validation_reasons = reasons
            if passed:
                validated.append(cand)

        return validated
