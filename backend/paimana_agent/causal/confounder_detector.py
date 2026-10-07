"""Confounder Detection Engine.

Identifies potential common causes (confounders) that simultaneously influence
both the proposed cause and observed effect. Penalizes naive causal claims
and generates evidence needs to resolve ambiguity.
"""
from __future__ import annotations
from typing import Any, Optional
from .models import Confounder


class ConfounderDetector:
    """Detects confounding variables in infrastructure project investigations."""

    KNOWN_CONFOUNDER_PATTERNS = [
        {
            "id": "CONF_FUNDING_SHORTAGE",
            "variable": "Funding / Liquidity Shortage",
            "candidate_causes": ["approval", "clearance", "contractor", "execution", "material", "procurement", "approval_delay", "contractor_execution"],
            "description": "A systemic funding or cashflow bottleneck may simultaneously stall statutory deposit payments (delaying approvals) and starve contractor working capital.",
            "indicators": ["fund", "budget", "escrow", "payment", "bills pending", "disbursement"],
            "resolution_evidence_needed": "Verify whether escrow disbursement milestones and statutory fee deposits were funded on time."
        },
        {
            "id": "CONF_LAND_DISPUTE",
            "variable": "Corridor Land Litigation / Encroachment",
            "candidate_causes": ["approval", "clearance", "contractor", "execution", "design", "revision", "land", "row"],
            "description": "An underlying land boundary litigation can stall local body approvals while simultaneously preventing contractor plant mobilization.",
            "indicators": ["land", "court", "stay", "litigation", "encroachment", "compensation", "revenue"],
            "resolution_evidence_needed": "Audit district revenue court records to establish whether land dispute predates contractor idling."
        },
        {
            "id": "CONF_CONTRACTOR_PREEXISTING_INSOLVENCY",
            "variable": "Contractor Pre-existing Balance Sheet Distress",
            "candidate_causes": ["contractor", "execution", "approval", "weather", "disruption", "design"],
            "description": "A contractor already facing corporate insolvency may submit excessive approval/variation requests to excuse pre-existing site abandonment.",
            "indicators": ["insolvency", "nclt", "subcontractor default", "bank guarantee", "working capital"],
            "resolution_evidence_needed": "Inspect independent financial audit and bank credit limits across other contractor sites."
        }
    ]

    @classmethod
    def detect_confounders(
        cls,
        proposed_cause: str,
        observed_effect: str,
        observations: dict[str, Any],
        evidence_claims: Optional[list[str]] = None
    ) -> list[Confounder]:
        """Scans project observations and evidence to flag active confounding risks."""
        evidence_claims = evidence_claims or []
        obs_text = " ".join([
            str(proposed_cause),
            str(observed_effect),
            " ".join(evidence_claims),
            str(observations)
        ]).lower()

        cause_lower = proposed_cause.lower()
        detected: list[Confounder] = []

        for pat in cls.KNOWN_CONFOUNDER_PATTERNS:
            # Check if this confounder applies to the proposed cause
            if not any(c in cause_lower for c in pat["candidate_causes"]):
                continue

            # Check if indicators of the confounder are present in observations
            hits = [w for w in pat["indicators"] if w in obs_text]
            if hits:
                # Confounder is plausibly active
                conf = Confounder(
                    id=pat["id"],
                    variable=pat["variable"],
                    affects_cause=True,
                    affects_effect=True,
                    evidence_ids=hits,
                    confidence=min(0.85, 0.40 + 0.15 * len(hits)),
                    description=pat["description"],
                    resolved=False,
                    resolution_evidence_needed=pat["resolution_evidence_needed"]
                )
                detected.append(conf)

        return detected

    @classmethod
    def calculate_confounder_penalty(cls, confounders: list[Confounder]) -> float:
        """Returns penalty in [0.0, 0.50] for unresolved confounding."""
        unresolved = [c for c in confounders if not c.resolved]
        if not unresolved:
            return 0.0
        # Each unresolved confounder incurs a 0.20 penalty, capped at 0.50
        raw = sum(0.20 * c.confidence for c in unresolved)
        return round(min(0.50, max(0.10, raw)), 3)
