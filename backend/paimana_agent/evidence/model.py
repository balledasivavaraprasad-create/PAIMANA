"""First-class Evidence Data Model for PAIMANA Agentic Layer.

Represents an individual, normalized, auditable piece of evidence observed during
an investigation, capturing source provenance, record lineage, timestamps,
authority scoring, freshness decay, independence grouping, materiality,
and bidirectional relations to hypotheses.
"""
from __future__ import annotations
import math
import time
from dataclasses import dataclass, field
from typing import Any, Optional


SOURCE_AUTHORITY: dict[str, float] = {
    "official_project_record": 1.00,
    "verified_financial_record": 0.95,
    "official_milestone_record": 0.95,
    "approved_external_api": 0.90,
    "gis_derived_measurement": 0.85,
    "historical_precedent": 0.70,
    "model_inference": 0.60,
    "tool_result": 0.80,
    "llm_generated_claim": 0.10,
    "default": 0.70,
}

# Freshness decay half-life in days (tau = half_life / ln(2))
SOURCE_HALF_LIFE_DAYS: dict[str, float] = {
    "verified_financial_record": 45.0,     # Fast-moving financial burn rate
    "tool_result": 60.0,
    "official_milestone_record": 90.0,     # Quarterly milestone reviews
    "official_project_record": 120.0,
    "approved_external_api": 90.0,
    "gis_derived_measurement": 90.0,
    "model_inference": 60.0,
    "historical_precedent": 365.0,         # Slow decay for historical precedents
    "default": 90.0,
}


@dataclass
class SourceLineage:
    """Detailed audit lineage of an individual evidence item."""
    evidence_id: str
    source_system: str
    source_record_id: Optional[str]
    source_field: Optional[str]
    parent_evidence_ids: list[str] = field(default_factory=list)
    transformation_chain: list[str] = field(default_factory=list)
    lineage_quality: float = 1.0

    def to_dict(self) -> dict:
        return {
            "evidence_id": self.evidence_id,
            "source_system": self.source_system,
            "source_record_id": self.source_record_id,
            "source_field": self.source_field,
            "parent_evidence_ids": list(self.parent_evidence_ids),
            "transformation_chain": list(self.transformation_chain),
            "lineage_quality": round(self.lineage_quality, 3),
        }


@dataclass
class EvidenceGroup:
    """Group of evidence items sharing an underlying primary source or snapshot."""
    group_id: str
    source_system: str
    primary_evidence_ids: list[str] = field(default_factory=list)
    derived_evidence_ids: list[str] = field(default_factory=list)
    base_authority: float = 1.0
    group_freshness: float = 1.0
    effective_group_weight: float = 1.0

    def to_dict(self) -> dict:
        return {
            "group_id": self.group_id,
            "source_system": self.source_system,
            "primary_evidence_ids": list(self.primary_evidence_ids),
            "derived_evidence_ids": list(self.derived_evidence_ids),
            "base_authority": round(self.base_authority, 3),
            "group_freshness": round(self.group_freshness, 3),
            "effective_group_weight": round(self.effective_group_weight, 3),
        }


@dataclass
class ConfidenceUpdate:
    """Audit record capturing the exact delta and justification for a confidence update."""
    hypothesis_id: str
    iteration: int
    previous_score: float
    new_score: float
    evidence_added: list[str] = field(default_factory=list)
    evidence_removed: list[str] = field(default_factory=list)
    support_delta: float = 0.0
    contradiction_delta: float = 0.0
    independent_groups: list[str] = field(default_factory=list)
    reason: str = ""
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "hypothesis_id": self.hypothesis_id,
            "iteration": self.iteration,
            "previous_score": round(self.previous_score, 3),
            "new_score": round(self.new_score, 3),
            "evidence_added": list(self.evidence_added),
            "evidence_removed": list(self.evidence_removed),
            "support_delta": round(self.support_delta, 3),
            "contradiction_delta": round(self.contradiction_delta, 3),
            "independent_groups": list(self.independent_groups),
            "reason": self.reason,
            "timestamp": self.timestamp,
        }

    @property
    def delta(self) -> float:
        return self.support_delta


@dataclass
class Evidence:
    """Explicit, normalized piece of investigation evidence with full provenance."""
    id: str                               # Unique ID, e.g. E1, E2, E3
    claim: str                            # Human-readable factual observation
    source_tool: str = "general"          # Generating tool or sensor (backward-compatible alias)
    source_id: str = ""                   # Identifier of producing agent/tool
    source_type: str = "official_project_record"  # official_project_record, verified_financial_record, etc.
    source_system: str = "PAIMANA"        # PAIMANA, PMIS, GIS, AUDIT, PEER_REPO, PRECEDENT_DB
    source_record_id: Optional[str] = None # Underlying snapshot / table row ID
    source_field: Optional[str] = None    # Specific field or measurement metric
    source_location: Optional[str] = None # Geographic or contractual location

    # Timestamps
    observed_at: Optional[float] = None   # When the physical ground fact occurred (epoch sec)
    recorded_at: Optional[float] = None   # When it was logged into official records
    retrieved_at: float = field(default_factory=time.time) # When agent retrieved it

    # Authority & Quality
    authority_score: float = 1.0          # Source authority (0.0 to 1.0)
    source_quality_score: float = 1.0     # Cleanliness / verification score

    # Lineage & Independence
    parent_evidence_ids: list[str] = field(default_factory=list) # Raw evidence this was derived from
    transformation_chain: list[str] = field(default_factory=list) # Transformations applied
    independence_group_id: str = "default" # Shared ID for correlated/same-snapshot evidence

    # Analytical Role & Linkages
    evidence_type: str = "direct_observation" # direct_observation, derived_metric, model_attribution, precedent
    supports_hypotheses: list[str] = field(default_factory=list)      # IDs of hypotheses supported
    contradicts_hypotheses: list[str] = field(default_factory=list)    # IDs of hypotheses contradicted

    # Strength Dimensions
    reliability: float = 1.0              # Empirical source reliability score (0.0 to 1.0)
    relevance: float = 1.0                # Relevance to targeted project context (0.0 to 1.0)
    freshness: float = 1.0                # Current temporal freshness (0.0 to 1.0)

    # Values
    raw_value: Any = None                 # Raw quantitative/qualitative value
    derived_value: Any = None             # Normalized metric or percentage
    is_material: bool = True              # Materiality flag (critical to investigation)
    coverage_status: str = "UNEXPLAINED"  # EXPLAINED, PARTIALLY_EXPLAINED, UNEXPLAINED, CONTRADICTORY

    def __post_init__(self):
        if not self.source_id:
            self.source_id = self.source_tool or "general"
        if not self.source_tool:
            self.source_tool = self.source_id
        if self.authority_score == 1.0 and self.source_type in SOURCE_AUTHORITY:
            self.authority_score = SOURCE_AUTHORITY[self.source_type]
        if self.observed_at is None:
            self.observed_at = self.retrieved_at
        if self.recorded_at is None:
            self.recorded_at = self.retrieved_at

    # Backward-compatible property aliases
    @property
    def independence_group(self) -> str:
        return self.independence_group_id

    @independence_group.setter
    def independence_group(self, val: str):
        self.independence_group_id = val

    @property
    def timestamp(self) -> float:
        return self.retrieved_at

    @timestamp.setter
    def timestamp(self, val: float):
        self.retrieved_at = val

    @property
    def normalized_value(self) -> Any:
        return self.derived_value

    def calculate_freshness(self, current_time: Optional[float] = None) -> float:
        """Calculates freshness decay based on evidence type half-life."""
        now = current_time or time.time()
        obs = self.observed_at or self.retrieved_at
        age_days = max(0.0, (now - obs) / 86400.0)
        
        half_life = SOURCE_HALF_LIFE_DAYS.get(self.source_type, SOURCE_HALF_LIFE_DAYS["default"])
        decay_constant = math.log(2) / max(1.0, half_life)
        computed_freshness = math.exp(-decay_constant * age_days)
        self.freshness = max(0.05, min(1.0, computed_freshness))
        return self.freshness

    def calculate_effective_strength(self, current_time: Optional[float] = None) -> float:
        """Calculates effective evidence strength = authority * freshness * reliability * relevance."""
        f = self.calculate_freshness(current_time)
        lineage_factor = 1.0 if not self.parent_evidence_ids else 0.85
        strength = self.authority_score * f * self.reliability * self.relevance * lineage_factor
        return max(0.01, min(1.0, strength))

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "claim": self.claim,
            "source_id": self.source_id,
            "source_tool": self.source_tool,
            "source_type": self.source_type,
            "source_system": self.source_system,
            "source_record_id": self.source_record_id,
            "source_field": self.source_field,
            "source_location": self.source_location,
            "observed_at": self.observed_at,
            "recorded_at": self.recorded_at,
            "retrieved_at": self.retrieved_at,
            "timestamp": self.retrieved_at,
            "authority_score": round(self.authority_score, 3),
            "source_quality_score": round(self.source_quality_score, 3),
            "parent_evidence_ids": list(self.parent_evidence_ids),
            "transformation_chain": list(self.transformation_chain),
            "independence_group_id": self.independence_group_id,
            "independence_group": self.independence_group_id,
            "evidence_type": self.evidence_type,
            "reliability": round(self.reliability, 3),
            "relevance": round(self.relevance, 3),
            "freshness": round(self.freshness, 3),
            "effective_strength": round(self.calculate_effective_strength(), 3),
            "supports_hypotheses": list(self.supports_hypotheses),
            "contradicts_hypotheses": list(self.contradicts_hypotheses),
            "raw_value": self.raw_value,
            "derived_value": self.derived_value,
            "is_material": self.is_material,
            "coverage_status": self.coverage_status,
        }
