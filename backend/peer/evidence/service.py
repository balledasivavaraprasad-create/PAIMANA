"""Central Coordinator: Evidence and Semantic Safety Service (ESS-01 to ESS-10).

Orchestrates evidence normalization, provenance tracing, multi-dimensional reliability evaluation,
semantic graph relations, 5-level claim hierarchy enforcement, causal-claim guards,
contradiction detection, pre-report safety audits, and semantic-safe report synthesis.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple

from .causal_guard import CausalClaimGuard
from .claims import ClaimManager, ClaimValidator
from .contradiction import ContradictionDetector
from .extraction import EvidenceExtractor
from .provenance import ProvenanceTracker
from .registry import EvidenceRegistry
from .relations import SemanticRelationGraph
from .reliability import ReliabilityEvaluator
from .schemas import (
    Claim,
    ClaimLevel,
    ClaimStatus,
    ContradictionRecord,
    Evidence,
    EvidenceProvenance,
    EvidenceRelationType,
    EvidenceReliability,
    ReliabilityTier,
    SemanticSafeReport,
    SemanticSafetyAuditReport,
)
from .synthesis import SemanticReportSynthesizer
from .unsupported_claims import UnsupportedClaimAuditor

logger = logging.getLogger("paimana.peer.evidence.service")


class EvidenceAndSemanticSafetyService:
    """Unified service interface for all Evidence and Semantic Safety operations."""

    def __init__(
        self,
        registry: Optional[EvidenceRegistry] = None,
        relation_graph: Optional[SemanticRelationGraph] = None,
        provenance_tracker: Optional[ProvenanceTracker] = None,
        reliability_evaluator: Optional[ReliabilityEvaluator] = None,
        causal_guard: Optional[CausalClaimGuard] = None,
    ):
        self.registry = registry or EvidenceRegistry()
        self.relation_graph = relation_graph or SemanticRelationGraph()
        self.provenance_tracker = provenance_tracker or ProvenanceTracker()
        self.reliability_evaluator = reliability_evaluator or ReliabilityEvaluator()
        self.causal_guard = causal_guard or CausalClaimGuard()

        self.extractor = EvidenceExtractor(
            provenance_tracker=self.provenance_tracker,
            reliability_evaluator=self.reliability_evaluator,
        )
        self.claim_manager = ClaimManager(
            registry=self.registry,
            relation_graph=self.relation_graph,
        )
        self.contradiction_detector = ContradictionDetector(
            registry=self.registry,
            relation_graph=self.relation_graph,
        )
        self.auditor = UnsupportedClaimAuditor(
            registry=self.registry,
            relation_graph=self.relation_graph,
            causal_guard=self.causal_guard,
        )
        self.synthesizer = SemanticReportSynthesizer(
            registry=self.registry,
            relation_graph=self.relation_graph,
            auditor=self.auditor,
        )

    # --------------------------------------------------------------------------
    # Evidence Ingestion & Normalization (ESS-01, ESS-02, ESS-03)
    # --------------------------------------------------------------------------

    def ingest_from_financial_velocity(
        self,
        project_id: str,
        financial_payload: Dict[str, Any],
    ) -> List[Evidence]:
        """Extracts and registers canonical evidence from financial velocity output."""
        ev_list = self.extractor.extract_from_financial_velocity(project_id, financial_payload)
        for ev in ev_list:
            self.registry.register(ev)
        return ev_list

    def ingest_from_milestone_audit(
        self,
        project_id: str,
        milestone_payload: Dict[str, Any],
    ) -> List[Evidence]:
        """Extracts and registers canonical evidence from milestone audit output."""
        ev_list = self.extractor.extract_from_milestone_audit(project_id, milestone_payload)
        for ev in ev_list:
            self.registry.register(ev)
        return ev_list

    def ingest_from_peer_intelligence(
        self,
        project_id: str,
        peer_payload: Dict[str, Any],
    ) -> List[Evidence]:
        """Extracts and registers canonical evidence from peer benchmark output."""
        ev_list = self.extractor.extract_from_peer_intelligence(project_id, peer_payload)
        for ev in ev_list:
            self.registry.register(ev)
        return ev_list

    def ingest_from_domain_context(
        self,
        project_id: str,
        domain_payload: Dict[str, Any],
    ) -> List[Evidence]:
        """Extracts and registers canonical evidence from domain intelligence output."""
        ev_list = self.extractor.extract_from_domain_context(project_id, domain_payload)
        for ev in ev_list:
            self.registry.register(ev)
        return ev_list

    def register_evidence(self, evidence: Evidence) -> Evidence:
        """Directly registers a canonical Evidence instance."""
        return self.registry.register(evidence)

    # --------------------------------------------------------------------------
    # Semantic Relations (ESS-04)
    # --------------------------------------------------------------------------

    def link_evidence_to_claim(
        self,
        evidence_id: str,
        claim_id: str,
        relation_type: EvidenceRelationType,
        confidence: float = 1.0,
        rationale: str = "",
    ):
        """Creates a semantic relational link between an evidence item and a claim/hypothesis."""
        ev = self.registry.get(evidence_id)
        valid, msg = self.relation_graph.validate_relation_assignment(
            source_evidence=ev,
            target_claim_level="HYPOTHESIS",
            relation_type=relation_type,
        )
        if not valid:
            logger.warning(f"Relation assignment warning: {msg}")

        return self.relation_graph.add_relation(
            source_id=evidence_id,
            target_id=claim_id,
            relation_type=relation_type,
            confidence=confidence,
            rationale=rationale,
        )

    # --------------------------------------------------------------------------
    # Claims & Causal Safety (ESS-05, ESS-06, ESS-07)
    # --------------------------------------------------------------------------

    def propose_claim(
        self,
        project_id: str,
        statement: str,
        claim_level: ClaimLevel,
        evidence_ids: List[str],
        claim_id: Optional[str] = None,
        limitations: Optional[List[str]] = None,
    ) -> Claim:
        """Proposes and validates a candidate analytical claim."""
        return self.claim_manager.create_claim(
            project_id=project_id,
            statement=statement,
            claim_level=claim_level,
            evidence_ids=evidence_ids,
            claim_id=claim_id,
            limitations=limitations,
        )

    def guard_statement(self, text: str) -> Tuple[bool, List[str], str]:
        """Checks a free-form statement against the 8 semantic safety rules."""
        return self.causal_guard.check_statement(text)

    # --------------------------------------------------------------------------
    # Contradictions & Audit (ESS-08, ESS-09)
    # --------------------------------------------------------------------------

    def detect_contradictions(
        self,
        claims: List[Claim],
        project_id: Optional[str] = None,
    ) -> List[ContradictionRecord]:
        """Detects contradictions between claims and empirical evidence."""
        return self.contradiction_detector.scan_for_contradictions(claims, project_id)

    def audit_claims(self, claims: List[Claim]) -> SemanticSafetyAuditReport:
        """Executes pre-report audit across all candidate claims."""
        return self.auditor.audit_claims(claims)

    # --------------------------------------------------------------------------
    # Safe Report Synthesis (ESS-10)
    # --------------------------------------------------------------------------

    def generate_safe_report(
        self,
        project_id: str,
        project_name: str,
        candidate_claims: List[Claim],
        evidence_gaps: Optional[List[str]] = None,
    ) -> SemanticSafeReport:
        """Synthesizes an executive report strictly bounded by verified evidence."""
        return self.synthesizer.generate_safe_report(
            project_id=project_id,
            project_name=project_name,
            candidate_claims=candidate_claims,
            evidence_gaps=evidence_gaps,
        )
