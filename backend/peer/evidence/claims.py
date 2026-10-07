"""5-Level Cognitive Claim Hierarchy & Semantic Claim Validation (ESS-05, ESS-06).

Enforces strict boundaries across the 5 cognitive tiers:
1. OBSERVATION: Raw empirical measurement (Level 1)
2. DERIVED_FINDING: Calculated metric or differential (Level 2)
3. INTERPRETATION: Descriptive qualitative pattern (Level 3)
4. HYPOTHESIS: Plausible candidate explanation (Level 4)
5. CAUSAL / ATTRIBUTION: Proven root cause or fault attribution (Level 5)

Safety Gate: Prevents silent semantic escalation from contextual or derived observations
into ungrounded causal or attribution assertions.
"""
from __future__ import annotations

import logging
import uuid
from typing import Dict, List, Optional, Tuple

from .registry import EvidenceRegistry
from .relations import SemanticRelationGraph
from .schemas import (
    Claim,
    ClaimLevel,
    ClaimStatus,
    Evidence,
    EvidenceRelationType,
    ReliabilityTier,
)

logger = logging.getLogger("paimana.peer.evidence.claims")


class ClaimValidator:
    """Validates candidate analytical claims against canonical evidence and relation graph."""

    def __init__(self, registry: EvidenceRegistry, relation_graph: SemanticRelationGraph):
        self.registry = registry
        self.relation_graph = relation_graph

    def validate_claim(self, claim: Claim) -> Tuple[Claim, List[str]]:
        """Evaluates a claim against registered evidence and semantic relations.
        
        Returns the updated Claim (with assigned status and audit note) and a list of safety notes.
        """
        safety_notes: List[str] = []

        # 1. Check if evidence is provided
        if not claim.evidence_ids:
            claim.status = ClaimStatus.UNSUPPORTED
            claim.audit_note = "Rejected: Claim has zero registered evidence backing."
            safety_notes.append(f"Claim [{claim.claim_id}] rejected: No supporting evidence attached.")
            return claim, safety_notes

        # 2. Retrieve all referenced evidence objects
        referenced_evidence: List[Evidence] = []
        missing_ids: List[str] = []
        for eid in claim.evidence_ids:
            ev = self.registry.get(eid)
            if ev:
                referenced_evidence.append(ev)
            else:
                missing_ids.append(eid)

        if missing_ids:
            safety_notes.append(f"Evidence IDs not found in registry: {missing_ids}")

        if not referenced_evidence:
            claim.status = ClaimStatus.UNSUPPORTED
            claim.audit_note = f"Rejected: None of the referenced evidence IDs {claim.evidence_ids} exist in registry."
            return claim, safety_notes

        # 3. Check for active contradictions in the relation graph
        contradicting_eids = self.relation_graph.get_contradicting_evidence_ids(claim.claim_id)
        if contradicting_eids:
            claim.status = ClaimStatus.CONTRADICTED
            claim.audit_note = f"Contradicted by evidence IDs: {contradicting_eids}."
            safety_notes.append(f"Claim [{claim.claim_id}] is contradicted by empirical facts: {contradicting_eids}")
            return claim, safety_notes

        # 4. Check edge relation types
        relations = self.relation_graph.get_relations_for_target(claim.claim_id)
        only_contextual = self.relation_graph.is_only_contextual(claim.claim_id)

        # 5. Evaluate based on cognitive ClaimLevel
        if claim.claim_level == ClaimLevel.OBSERVATION:
            # Level 1: Must be backed by direct observational evidence
            has_obs = any(e.source_type != "PEER_INTELLIGENCE" for e in referenced_evidence)
            if has_obs:
                claim.status = ClaimStatus.SUPPORTED
                claim.audit_note = "Verified empirical observation."
            else:
                claim.status = ClaimStatus.CONTEXTUAL
                claim.audit_note = "Observation backed only by peer comparison."

        elif claim.claim_level == ClaimLevel.DERIVED_FINDING:
            # Level 2: Derived findings require verified calculation methodology
            claim.status = ClaimStatus.SUPPORTED
            claim.audit_note = "Verified derived analytical finding."

        elif claim.claim_level == ClaimLevel.INTERPRETATION:
            # Level 3: Interpretation of patterns
            if only_contextual:
                claim.status = ClaimStatus.CONTEXTUAL
                claim.audit_note = "Descriptive interpretation supported solely by contextual indicators."
            else:
                claim.status = ClaimStatus.SUPPORTED
                claim.audit_note = "Valid descriptive interpretation backed by direct evidence."

        elif claim.claim_level == ClaimLevel.HYPOTHESIS:
            # Level 4: Candidate explanation
            if only_contextual:
                claim.status = ClaimStatus.CONTEXTUAL
                claim.audit_note = "Hypothesis contextualized by peer/domain precedents; requires empirical verification."
                safety_notes.append(f"Hypothesis [{claim.claim_id}] held at CONTEXTUAL tier (only contextual evidence).")
            else:
                claim.status = ClaimStatus.PARTIALLY_SUPPORTED
                claim.audit_note = "Plausible hypothesis supported by direct observations; retains alternate explanations."

        elif claim.claim_level in (ClaimLevel.CAUSAL, ClaimLevel.ATTRIBUTION):
            # Level 5: Causal or Attribution claims
            # Strict safety gate:
            # 1. CANNOT be supported if only contextual
            # 2. CANNOT be supported by model prediction alone
            # 3. Requires at least one CONFIRMED or high-reliability SUPPORTED evidence directly linking cause to effect
            if only_contextual:
                claim.claim_level = ClaimLevel.HYPOTHESIS  # Enforce downgrade!
                claim.status = ClaimStatus.CONTEXTUAL
                claim.audit_note = (
                    "Safety Gate Downgrade: Proposed causal claim downgraded to HYPOTHESIS. "
                    "Evidence consists exclusively of contextual or comparative signals."
                )
                safety_notes.append(
                    f"Causal escalation blocked for [{claim.claim_id}]: Downgraded to HYPOTHESIS "
                    f"(Contextual evidence cannot establish causation)."
                )
                return claim, safety_notes

            # Check if evidence contains authoritative proof
            authoritative = any(
                e.semantic_status in (ReliabilityTier.CONFIRMED, ReliabilityTier.SUPPORTED)
                and e.source_type not in ("PEER_INTELLIGENCE", "DOMAIN_CONTEXT")
                for e in referenced_evidence
            )

            if not authoritative:
                claim.claim_level = ClaimLevel.HYPOTHESIS  # Enforce downgrade
                claim.status = ClaimStatus.PARTIALLY_SUPPORTED
                claim.audit_note = (
                    "Safety Gate Downgrade: Causal claim lacks authoritative primary records. "
                    "Downgraded to HYPOTHESIS pending site audit."
                )
                safety_notes.append(
                    f"Attribution claim [{claim.claim_id}] downgraded to HYPOTHESIS: "
                    f"Lacks authoritative direct audit records."
                )
            else:
                claim.status = ClaimStatus.SUPPORTED
                claim.audit_note = "Causal finding verified against primary authoritative audit records."

        return claim, safety_notes


class ClaimManager:
    """Creates, registers, and tracks structured claims across the 5 cognitive levels."""

    def __init__(self, registry: EvidenceRegistry, relation_graph: SemanticRelationGraph):
        self.registry = registry
        self.relation_graph = relation_graph
        self.validator = ClaimValidator(registry, relation_graph)
        self._claims: Dict[str, Claim] = {}

    def create_claim(
        self,
        project_id: str,
        statement: str,
        claim_level: ClaimLevel,
        evidence_ids: List[str],
        claim_id: Optional[str] = None,
        limitations: Optional[List[str]] = None,
    ) -> Claim:
        """Instantiates a candidate claim and executes semantic validation gate."""
        cid = claim_id or f"claim_{uuid.uuid4().hex[:10]}"
        claim = Claim(
            claim_id=cid,
            project_id=project_id,
            statement=statement,
            claim_level=claim_level,
            evidence_ids=list(evidence_ids),
            required_level=claim_level,
            limitations=limitations or [],
        )

        validated_claim, _ = self.validator.validate_claim(claim)
        self._claims[cid] = validated_claim
        return validated_claim

    def get_claim(self, claim_id: str) -> Optional[Claim]:
        return self._claims.get(claim_id)

    def get_claims_by_level(self, level: ClaimLevel) -> List[Claim]:
        return [c for c in self._claims.values() if c.claim_level == level]

    def get_claims_by_status(self, status: ClaimStatus) -> List[Claim]:
        return [c for c in self._claims.values() if c.status == status]

    def all_claims(self) -> List[Claim]:
        return list(self._claims.values())

    def clear(self):
        self._claims.clear()
