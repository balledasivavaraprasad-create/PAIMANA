"""Semantic-Safe Report Synthesis Engine (ESS-10).

Produces structured, semantically bounded executive reports ensuring:
- Absolute separation between Observations, Derived Findings, Hypotheses, and Context
- Strict exclusion of rejected or unverified causal claims
- Transparent presentation of evidence gaps and epistemic limitations
- Preservation of the mandatory human approval boundary
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from .causal_guard import CausalClaimGuard
from .registry import EvidenceRegistry
from .relations import SemanticRelationGraph
from .schemas import (
    Claim,
    ClaimLevel,
    ClaimStatus,
    Evidence,
    ReliabilityTier,
    SemanticSafeReport,
    SemanticSafetyAuditReport,
)
from .unsupported_claims import UnsupportedClaimAuditor

logger = logging.getLogger("paimana.peer.evidence.synthesis")


class SemanticReportSynthesizer:
    """Synthesizes executive reports guaranteed to be free of ungrounded causal claims."""

    def __init__(
        self,
        registry: EvidenceRegistry,
        relation_graph: SemanticRelationGraph,
        auditor: Optional[UnsupportedClaimAuditor] = None,
    ):
        self.registry = registry
        self.relation_graph = relation_graph
        self.auditor = auditor or UnsupportedClaimAuditor(registry, relation_graph)

    def generate_safe_report(
        self,
        project_id: str,
        project_name: str,
        candidate_claims: List[Claim],
        evidence_gaps: Optional[List[str]] = None,
    ) -> SemanticSafeReport:
        """Assembles a validated SemanticSafeReport adhering strictly to ESS-10 specifications."""
        # 1. Audit and filter claims
        safe_claims, audit_report = self.auditor.filter_safe_claims_for_reporting(candidate_claims)

        # 2. Extract Level 1 Observations
        observations: List[str] = []
        for claim in safe_claims:
            if claim.claim_level == ClaimLevel.OBSERVATION:
                observations.append(claim.statement)

        # Also pull empirical observations directly from registered evidence for this project
        project_evidence = self.registry.get_by_project(project_id)
        for ev in project_evidence:
            if ev.source_type not in ("PEER_INTELLIGENCE", "DOMAIN_CONTEXT"):
                obs_str = f"[{ev.source_id}] {ev.observation} (Confidence: {ev.confidence:.0%})"
                if obs_str not in observations:
                    observations.append(obs_str)

        # 3. Extract Level 2 Derived Findings
        derived_findings: List[str] = []
        for claim in safe_claims:
            if claim.claim_level == ClaimLevel.DERIVED_FINDING:
                derived_findings.append(claim.statement)

        # 4. Extract Level 4 Hypotheses & Evaluated Scenarios
        hypotheses_evaluated: List[Dict[str, Any]] = []
        for claim in safe_claims:
            if claim.claim_level in (ClaimLevel.HYPOTHESIS, ClaimLevel.CAUSAL, ClaimLevel.ATTRIBUTION):
                hypotheses_evaluated.append({
                    "hypothesis": claim.statement,
                    "level": claim.claim_level.value,
                    "status": claim.status.value,
                    "supporting_evidence": self.relation_graph.get_supporting_evidence_ids(claim.claim_id),
                    "contradicting_evidence": self.relation_graph.get_contradicting_evidence_ids(claim.claim_id),
                    "audit_note": claim.audit_note,
                })

        # 5. Extract Context Factors (Peer & Domain baselines)
        context_factors: List[str] = []
        for ev in project_evidence:
            if ev.source_type in ("PEER_INTELLIGENCE", "DOMAIN_CONTEXT"):
                context_factors.append(f"[{ev.source_type}] {ev.observation}")

        # 6. Extract Semantic Safety Notes
        safety_notes: List[str] = []
        for v in audit_report.violations_prevented:
            safety_notes.append(f"[{v.get('claim_id', 'SAFETY')}] {v.get('action', '')}")

        for rejected in audit_report.rejected_claims:
            safety_notes.append(
                f"Suppressed ungrounded claim [{rejected.claim_id}]: '{rejected.statement}' ({rejected.audit_note})"
            )

        # 7. Formulate Executive Narrative
        narrative_lines: List[str] = [
            f"# Executive Project Assessment: {project_name} ({project_id})",
            "",
            "## 1. Verified Empirical Observations",
        ]
        if observations:
            for obs in observations:
                narrative_lines.append(f"- {obs}")
        else:
            narrative_lines.append("- No primary empirical observations recorded.")

        narrative_lines.extend([
            "",
            "## 2. Derived Analytical Findings",
        ])
        if derived_findings:
            for df in derived_findings:
                narrative_lines.append(f"- {df}")
        else:
            narrative_lines.append("- No derived differentials calculated.")

        narrative_lines.extend([
            "",
            "## 3. Evaluated Hypotheses & Potential Drivers",
        ])
        if hypotheses_evaluated:
            for hyp in hypotheses_evaluated:
                narrative_lines.append(
                    f"- **[{hyp['status']}]** {hyp['hypothesis']} *(Status: {hyp['level']}, Note: {hyp['audit_note']})*"
                )
        else:
            narrative_lines.append("- No competing hypotheses required.")

        narrative_lines.extend([
            "",
            "## 4. Contextual & Comparative Baselines",
        ])
        if context_factors:
            for ctx in context_factors:
                narrative_lines.append(f"- {ctx}")
        else:
            narrative_lines.append("- Standard domain baselines apply.")

        narrative_lines.extend([
            "",
            "## 5. Epistemic Limitations & Evidence Gaps",
        ])
        final_gaps = evidence_gaps or [
            "Site-level measurement book verification pending.",
            "Sub-contractor advance reconciliation records uninspected.",
        ]
        for gap in final_gaps:
            narrative_lines.append(f"- {gap}")

        narrative_lines.extend([
            "",
            "> [!NOTE]",
            "> **Human Approval Gate Active**: The findings and hypotheses in this report are mathematically",
            "> and semantically constrained. Definitive causal determinations or contractual fault attributions",
            "> strictly require manual inspection and human supervisory sign-off.",
        ])

        narrative = "\n".join(narrative_lines)

        report = SemanticSafeReport(
            project_id=project_id,
            project_name=project_name,
            observations=observations,
            derived_findings=derived_findings,
            hypotheses_evaluated=hypotheses_evaluated,
            context_factors=context_factors,
            evidence_gaps=final_gaps,
            semantic_safety_notes=safety_notes,
            audit_summary=audit_report,
            executive_narrative=narrative,
            human_approval_required=True,
        )

        return report
