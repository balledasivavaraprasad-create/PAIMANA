"""Auditable Causal Decision Trace.

Generates structured, replayable decision logs detailing how competing causal
claims were formed, tested, falsified, or confirmed.
"""
from __future__ import annotations
import time
from typing import Optional
from .models import CausalClaim, CausalConclusionStatus


class CausalTraceBuilder:
    """Builds auditable causal investigation traces for human review and governance."""

    @classmethod
    def build_trace(
        cls,
        investigation_id: str,
        project_code: str,
        effect: str,
        claims: list[CausalClaim],
        leading_claim: Optional[CausalClaim],
        alternatives: list[CausalClaim],
        conclusion_status: CausalConclusionStatus,
        summary_rationale: str
    ) -> dict:
        """Constructs a comprehensive, replayable causal audit trace."""
        claim_summaries = []
        for c in claims:
            verified_links = []
            unverified_links = []
            if c.mechanism:
                for k, v in c.mechanism.links_verified.items():
                    if v:
                        verified_links.append(k)
                    else:
                        unverified_links.append(k)

            claim_summaries.append({
                "id": c.id,
                "proposed_cause": c.proposed_cause,
                "causal_level": c.causal_level,
                "causal_support_score": c.causal_support_score,
                "status": c.status,
                "temporal_support": c.temporal_support,
                "mechanistic_support": c.mechanistic_support,
                "verified_intermediate_links": verified_links,
                "missing_intermediate_links": unverified_links,
                "unresolved_confounders": c.unresolved_confounders,
                "falsifications": c.falsification_notes,
                "actionable_intervention": c.actionable_intervention,
                "responsible_authority": c.responsible_authority,
            })

        return {
            "investigation_id": investigation_id,
            "project_code": project_code,
            "timestamp": time.time(),
            "observed_effect": effect,
            "conclusion_status": conclusion_status,
            "summary_rationale": summary_rationale,
            "leading_causal_explanation": leading_claim.proposed_cause if leading_claim else None,
            "leading_causal_level": leading_claim.causal_level if leading_claim else "LEVEL_0_OBSERVATION",
            "leading_support_score": leading_claim.causal_support_score if leading_claim else 0.0,
            "retained_alternatives": [a.proposed_cause for a in alternatives],
            "actionable_node": leading_claim.actionable_intervention if leading_claim else None,
            "responsible_authority": leading_claim.responsible_authority if leading_claim else None,
            "candidate_evaluations": claim_summaries,
            "governance_rule": "System must never convert correlation into causal language merely because two variables move together."
        }
