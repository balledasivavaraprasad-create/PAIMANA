"""Evidence Contradiction Modeling & Detection Engine (ESS-08).

Identifies, models, and tracks empirical contradictions where registered evidence
directly challenges hypotheses, derived findings, or candidate claims.
"""
from __future__ import annotations

import logging
import uuid
from typing import Dict, List, Optional, Tuple

from .registry import EvidenceRegistry
from .relations import SemanticRelationGraph
from .schemas import (
    Claim,
    ContradictionRecord,
    Evidence,
    EvidenceRelationType,
)

logger = logging.getLogger("paimana.peer.evidence.contradiction")


class ContradictionDetector:
    """Detects and registers empirical contradictions across evidence, claims, and hypotheses."""

    def __init__(self, registry: EvidenceRegistry, relation_graph: SemanticRelationGraph):
        self.registry = registry
        self.relation_graph = relation_graph
        self._records: Dict[str, ContradictionRecord] = {}

    def register_contradiction(
        self,
        claim_or_hypothesis: str,
        evidence_ids: List[str],
        conflicting_evidence_ids: List[str],
        severity: str = "HIGH",
        impact: str = "REDUCE_CONFIDENCE",
        resolution_action: str = "Require secondary documentary verification",
    ) -> ContradictionRecord:
        """Explicitly records an empirical contradiction."""
        cid = f"contra_{uuid.uuid4().hex[:10]}"
        record = ContradictionRecord(
            contradiction_id=cid,
            claim_or_hypothesis=claim_or_hypothesis,
            evidence_ids=list(evidence_ids),
            conflicting_evidence_ids=list(conflicting_evidence_ids),
            severity=severity,
            impact=impact,
            resolution_action=resolution_action,
        )
        self._records[cid] = record

        # Link conflicting evidence in the relation graph
        for eid in conflicting_evidence_ids:
            self.relation_graph.add_relation(
                source_id=eid,
                target_id=claim_or_hypothesis,
                relation_type=EvidenceRelationType.CONTRADICTS,
                confidence=1.0,
                rationale=f"Empirical contradiction registered under {cid}",
            )

        logger.info(f"Contradiction registered: {cid} for '{claim_or_hypothesis}' ({severity})")
        return record

    def scan_for_contradictions(
        self,
        claims: List[Claim],
        project_id: Optional[str] = None,
    ) -> List[ContradictionRecord]:
        """Scans claims and project evidence to detect automatic semantic/numerical contradictions."""
        detected: List[ContradictionRecord] = []
        ev_pool = self.registry.get_by_project(project_id) if project_id else []

        for claim in claims:
            # 1. Check graph for existing CONTRADICTS edges
            contradicting_eids = self.relation_graph.get_contradicting_evidence_ids(claim.claim_id)
            if contradicting_eids:
                rec = self.register_contradiction(
                    claim_or_hypothesis=claim.claim_id,
                    evidence_ids=claim.evidence_ids,
                    conflicting_evidence_ids=contradicting_eids,
                    severity="HIGH",
                    impact="INVALIDATE_CLAIM",
                    resolution_action="Flag contradictory primary records for supervisory review",
                )
                detected.append(rec)
                continue

            # 2. Heuristic contradiction rules across domain evidence:
            # Case A: Claim states works are halted/idle, but progress > 0 in recent period
            stmt_lower = claim.statement.lower()
            if any(term in stmt_lower for term in ["idle", "stalled", "no work", "halted", "frozen"]):
                for ev in ev_pool:
                    if ev.evidence_type in ("PHYSICAL_PROGRESS", "VELOCITY_ANALYSIS"):
                        val = ev.value if isinstance(ev.value, (int, float)) else 0.0
                        if val > 0.05:  # more than 5% progress recorded
                            rec = self.register_contradiction(
                                claim_or_hypothesis=claim.claim_id,
                                evidence_ids=claim.evidence_ids,
                                conflicting_evidence_ids=[ev.evidence_id],
                                severity="CRITICAL",
                                impact="REDUCE_CONFIDENCE",
                                resolution_action="Physical progress measurement directly refutes project idle assertion",
                            )
                            detected.append(rec)
                            break

            # Case B: Claim states contractor mobilization missing, but equipment/workforce evidence exists
            if any(term in stmt_lower for term in ["no mobilization", "zero equipment", "contractor absent"]):
                for ev in ev_pool:
                    if "MOBILIZATION" in ev.evidence_type or "EQUIPMENT" in ev.evidence_type:
                        rec = self.register_contradiction(
                            claim_or_hypothesis=claim.claim_id,
                            evidence_ids=claim.evidence_ids,
                            conflicting_evidence_ids=[ev.evidence_id],
                            severity="HIGH",
                            impact="INVALIDATE_CLAIM",
                            resolution_action="Equipment deployment logs directly contradict absence claim",
                        )
                        detected.append(rec)
                        break

        return detected

    def get_contradictions(self) -> List[ContradictionRecord]:
        return list(self._records.values())

    def get_unresolved(self) -> List[ContradictionRecord]:
        return [r for r in self._records.values() if not r.resolved]

    def clear(self):
        self._records.clear()
