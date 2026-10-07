"""Pre-Report Unsupported-Claim Audit Engine (ESS-09).

Performs rigorous pre-publication verification across all candidate findings:
- Audits claim-to-evidence bindings in the canonical registry
- Enforces safety downgrade / rejection of unbacked assertions
- Strips unsupported claims from final executive narrative
- Computes empirical unsupported_claim_rate
- Emits formal SemanticSafetyAuditReport
"""
from __future__ import annotations

import logging
from typing import Dict, List, Optional, Tuple

from .causal_guard import CausalClaimGuard
from .claims import ClaimValidator
from .registry import EvidenceRegistry
from .relations import SemanticRelationGraph
from .schemas import (
    Claim,
    ClaimLevel,
    ClaimStatus,
    SemanticSafetyAuditReport,
)

logger = logging.getLogger("paimana.peer.evidence.unsupported_claims")


class UnsupportedClaimAuditor:
    """Pre-report safety gate auditing candidate claims against evidence registry and semantic rules."""

    def __init__(
        self,
        registry: EvidenceRegistry,
        relation_graph: SemanticRelationGraph,
        causal_guard: Optional[CausalClaimGuard] = None,
    ):
        self.registry = registry
        self.relation_graph = relation_graph
        self.causal_guard = causal_guard or CausalClaimGuard()
        self.claim_validator = ClaimValidator(registry, relation_graph)

    def audit_claims(self, candidate_claims: List[Claim]) -> SemanticSafetyAuditReport:
        """Executes full semantic safety audit over candidate claims.
        
        Evaluates evidence backing, relation graph integrity, contradiction flags,
        and causal guard safety rules.
        """
        if not candidate_claims:
            return SemanticSafetyAuditReport(
                total_claims_evaluated=0,
                supported_claims=[],
                downgraded_claims=[],
                rejected_claims=[],
                violations_prevented=[],
                unsupported_claim_rate=0.0,
                passed_safety_gate=True,
            )

        supported: List[Claim] = []
        downgraded: List[Claim] = []
        rejected: List[Claim] = []
        violations: List[Dict[str, str]] = []

        for candidate in candidate_claims:
            orig_level = candidate.claim_level
            orig_status = candidate.status

            # Step 1: Validate through ClaimValidator (checks evidence existence, contradictions, level boundaries)
            validated, safety_notes = self.claim_validator.validate_claim(candidate)

            # Step 2: Pass through CausalClaimGuard (enforces 8 safety rules, sanitizes text)
            guarded_claim, guard_actions = self.causal_guard.enforce_on_claim(validated)

            for act in guard_actions:
                violations.append({
                    "claim_id": guarded_claim.claim_id,
                    "action": act,
                })

            # Step 3: Categorize outcome
            if guarded_claim.status in (ClaimStatus.UNSUPPORTED, ClaimStatus.CONTRADICTED):
                rejected.append(guarded_claim)
            elif (
                guarded_claim.claim_level != orig_level
                or guarded_claim.status in (ClaimStatus.CONTEXTUAL, ClaimStatus.PARTIALLY_SUPPORTED)
            ):
                downgraded.append(guarded_claim)
            else:
                supported.append(guarded_claim)

        total = len(candidate_claims)
        unsupported_rate = (len(rejected) + len(downgraded)) / float(total) if total > 0 else 0.0

        # Safety Gate Pass Criteria: Zero rejected causal claims and unbacked assertions stripped
        passed = len([c for c in rejected if c.claim_level in (ClaimLevel.CAUSAL, ClaimLevel.ATTRIBUTION)]) == 0

        report = SemanticSafetyAuditReport(
            total_claims_evaluated=total,
            supported_claims=supported,
            downgraded_claims=downgraded,
            rejected_claims=rejected,
            violations_prevented=violations,
            unsupported_claim_rate=unsupported_rate,
            passed_safety_gate=passed,
        )

        logger.info(
            f"SemanticSafetyAudit completed: evaluated={total}, supported={len(supported)}, "
            f"downgraded={len(downgraded)}, rejected={len(rejected)}, passed={passed}"
        )
        return report

    def filter_safe_claims_for_reporting(self, candidate_claims: List[Claim]) -> Tuple[List[Claim], SemanticSafetyAuditReport]:
        """Audits claims and returns only the safe (supported and safely downgraded) claims, omitting rejected ones."""
        audit_report = self.audit_claims(candidate_claims)
        # Suppress completely rejected or contradicted claims from narrative
        safe_claims = audit_report.supported_claims + audit_report.downgraded_claims
        return safe_claims, audit_report
