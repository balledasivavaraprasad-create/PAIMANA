"""Semantic Graph Relations & Edge Management (ESS-04).

Manages explicit semantic relations between evidence objects, claims, and hypotheses:
- OBSERVES: Direct empirical measurement
- SUPPORTS: Probabilistic reinforcement of a finding or hypothesis
- CONTRADICTS: Empirical falsification or challenge
- CONTEXTUALIZES: Environmental or peer baseline context (non-causal)
- DERIVED_FROM: Computational or mathematical lineage
- CORROBORATES: Independent multi-source verification
"""
from __future__ import annotations

import logging
import uuid
from typing import Dict, List, Optional, Set, Tuple

from .schemas import Evidence, EvidenceRelationType, ReliabilityTier, SemanticRelation

logger = logging.getLogger("paimana.peer.evidence.relations")


class SemanticRelationGraph:
    """Directed relational graph tracking semantic links between evidence, findings, and hypotheses."""

    def __init__(self):
        self._relations: Dict[str, SemanticRelation] = {}
        self._by_target: Dict[str, List[SemanticRelation]] = {}
        self._by_source: Dict[str, List[SemanticRelation]] = {}

    def add_relation(
        self,
        source_id: str,
        target_id: str,
        relation_type: EvidenceRelationType,
        confidence: float = 1.0,
        rationale: str = "",
        created_by: str = "deterministic_engine",
        relation_id: Optional[str] = None,
    ) -> SemanticRelation:
        """Adds a verified semantic relation between source evidence and target node."""
        rel_id = relation_id or f"rel_{uuid.uuid4().hex[:10]}"
        relation = SemanticRelation(
            relation_id=rel_id,
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type,
            confidence=max(0.0, min(1.0, confidence)),
            rationale=rationale,
            created_by=created_by,
        )

        self._relations[rel_id] = relation

        if target_id not in self._by_target:
            self._by_target[target_id] = []
        self._by_target[target_id].append(relation)

        if source_id not in self._by_source:
            self._by_source[source_id] = []
        self._by_source[source_id].append(relation)

        logger.debug(
            f"SemanticRelationGraph: Added {relation_type.value} edge {source_id} -> {target_id} ({rel_id})"
        )
        return relation

    def get_relation(self, relation_id: str) -> Optional[SemanticRelation]:
        return self._relations.get(relation_id)

    def get_relations_for_target(self, target_id: str) -> List[SemanticRelation]:
        return list(self._by_target.get(target_id, []))

    def get_relations_from_source(self, source_id: str) -> List[SemanticRelation]:
        return list(self._by_source.get(source_id, []))

    def get_supporting_evidence_ids(self, target_id: str) -> List[str]:
        return [
            rel.source_id
            for rel in self._by_target.get(target_id, [])
            if rel.relation_type in (EvidenceRelationType.SUPPORTS, EvidenceRelationType.OBSERVES, EvidenceRelationType.CORROBORATES)
        ]

    def get_contradicting_evidence_ids(self, target_id: str) -> List[str]:
        return [
            rel.source_id
            for rel in self._by_target.get(target_id, [])
            if rel.relation_type == EvidenceRelationType.CONTRADICTS
        ]

    def get_contextual_evidence_ids(self, target_id: str) -> List[str]:
        return [
            rel.source_id
            for rel in self._by_target.get(target_id, [])
            if rel.relation_type == EvidenceRelationType.CONTEXTUALIZES
        ]

    def is_only_contextual(self, target_id: str) -> bool:
        """Returns True if the target has edges and ALL incoming edges are CONTEXTUALIZES."""
        rels = self._by_target.get(target_id, [])
        if not rels:
            return False
        return all(r.relation_type == EvidenceRelationType.CONTEXTUALIZES for r in rels)

    def has_contradiction(self, target_id: str) -> bool:
        """Returns True if target has at least one active CONTRADICTS relation."""
        return any(
            r.relation_type == EvidenceRelationType.CONTRADICTS
            for r in self._by_target.get(target_id, [])
        )

    def validate_relation_assignment(
        self,
        source_evidence: Optional[Evidence],
        target_claim_level: str,
        relation_type: EvidenceRelationType,
    ) -> Tuple[bool, Optional[str]]:
        """Guards against invalid semantic edge assignment (e.g. contextual source directly supporting causal claim)."""
        if not source_evidence:
            return True, None

        # Contextual or unverified evidence cannot directly SUPPORT a Level 5 CAUSAL or ATTRIBUTION claim
        if target_claim_level in ("CAUSAL", "ATTRIBUTION") and relation_type == EvidenceRelationType.SUPPORTS:
            if source_evidence.semantic_status in (ReliabilityTier.CONTEXTUAL, ReliabilityTier.UNVERIFIED):
                return False, (
                    f"Evidence {source_evidence.evidence_id} has tier {source_evidence.semantic_status.value} "
                    f"and cannot directly SUPPORTS causal/attribution claim without empirical corroboration."
                )

        return True, None

    def clear(self):
        self._relations.clear()
        self._by_target.clear()
        self._by_source.clear()

    def count(self) -> int:
        return len(self._relations)
