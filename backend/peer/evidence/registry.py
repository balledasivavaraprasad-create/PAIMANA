"""Canonical Evidence Registry & Ingestion Store (ESS-01).

Maintains a centralized, indexed, and deduplicated repository of canonical Evidence objects,
enforcing standard schema compliance across all analytical subsystems.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Set

from .schemas import Evidence, ReliabilityTier

logger = logging.getLogger("paimana.peer.evidence.registry")


class EvidenceRegistry:
    """Centralized in-memory registry for standardized evidence objects."""

    def __init__(self):
        self._by_id: Dict[str, Evidence] = {}
        self._by_project: Dict[str, List[Evidence]] = {}
        self._by_type: Dict[str, List[Evidence]] = {}
        self._seen_hashes: Set[str] = set()

    def register(self, evidence: Evidence) -> Evidence:
        """Registers a canonical Evidence object, with deterministic hash deduplication."""
        # Check input hash deduplication if provenance present
        if evidence.provenance and evidence.provenance.input_hash:
            dedup_key = f"{evidence.project_id}_{evidence.source_type}_{evidence.provenance.input_hash}"
            if dedup_key in self._seen_hashes:
                # Return existing evidence rather than duplicating
                for existing in self._by_project.get(evidence.project_id, []):
                    if (
                        existing.provenance
                        and existing.provenance.input_hash == evidence.provenance.input_hash
                        and existing.source_type == evidence.source_type
                    ):
                        logger.debug(f"EvidenceRegistry: deduplicated existing evidence {existing.evidence_id}")
                        return existing
            self._seen_hashes.add(dedup_key)

        self._by_id[evidence.evidence_id] = evidence

        # Index by Project ID
        if evidence.project_id not in self._by_project:
            self._by_project[evidence.project_id] = []
        self._by_project[evidence.project_id].append(evidence)

        # Index by Evidence Type
        if evidence.evidence_type not in self._by_type:
            self._by_type[evidence.evidence_type] = []
        self._by_type[evidence.evidence_type].append(evidence)

        return evidence

    def get(self, evidence_id: str) -> Optional[Evidence]:
        return self._by_id.get(evidence_id)

    def get_by_project(self, project_id: str) -> List[Evidence]:
        return list(self._by_project.get(project_id, []))

    def get_by_type(self, evidence_type: str) -> List[Evidence]:
        return list(self._by_type.get(evidence_type, []))

    def get_by_tier(self, tier: ReliabilityTier, project_id: Optional[str] = None) -> List[Evidence]:
        pool = self.get_by_project(project_id) if project_id else self._by_id.values()
        return [e for e in pool if e.semantic_status == tier]

    def clear(self):
        self._by_id.clear(
        )
        self._by_project.clear()
        self._by_type.clear()
        self._seen_hashes.clear()

    def count(self) -> int:
        return len(self._by_id)
