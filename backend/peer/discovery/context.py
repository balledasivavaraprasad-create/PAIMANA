"""Structured Investigation Context for Question-Conditioned Peer Discovery.

Enables the Supervisor and Peer Intelligence subsystem to tailor peer selection
specifically to the active hypothesis, question type, and temporal boundaries.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class PeerInvestigationContext:
    """Structured context defining the exact question and boundaries for peer discovery.
    
    Attributes:
        target_project_id: Canonical or source code of the project under investigation.
        investigation_question: Natural language question posed by the Supervisor.
        hypothesis_id: Unique identifier of the active hypothesis (e.g. front_loaded_billing).
        investigation_type: Explicit category (e.g. COST_OVERRUN, EXPENDITURE_PROGRESS_MISMATCH).
        as_of_date: ISO 8601 YYYY-MM-DD point-in-time date for temporal safety.
        max_peers: Target maximum number of peer comparators.
        min_similarity: Minimum soft similarity score threshold.
        allow_relaxation: Whether controlled relaxation may be attempted if cohort is insufficient.
        metadata: Additional contextual signals or parameters.
    """
    target_project_id: str
    investigation_question: Optional[str] = None
    hypothesis_id: Optional[str] = None
    investigation_type: Optional[str] = None
    as_of_date: Optional[str] = None
    max_peers: int = 10
    min_similarity: float = 0.50
    allow_relaxation: bool = True
    created_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "target_project_id": self.target_project_id,
            "investigation_question": self.investigation_question,
            "hypothesis_id": self.hypothesis_id,
            "investigation_type": self.investigation_type,
            "as_of_date": self.as_of_date,
            "max_peers": self.max_peers,
            "min_similarity": round(self.min_similarity, 4),
            "allow_relaxation": self.allow_relaxation,
            "created_at": self.created_at,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> PeerInvestigationContext:
        return cls(
            target_project_id=str(data.get("target_project_id", "")),
            investigation_question=data.get("investigation_question"),
            hypothesis_id=data.get("hypothesis_id"),
            investigation_type=data.get("investigation_type"),
            as_of_date=data.get("as_of_date"),
            max_peers=int(data.get("max_peers", 10)),
            min_similarity=float(data.get("min_similarity", 0.50)),
            allow_relaxation=bool(data.get("allow_relaxation", True)),
            created_at=float(data.get("created_at", time.time())),
            metadata=dict(data.get("metadata", {})),
        )
