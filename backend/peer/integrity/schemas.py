"""Domain Schemas & Data Contracts for the PAIMANA Data Integrity & Reliability Layer.

This module defines formal data models and contracts for:
- Canonical Project Identity & Alias Management (DIR-03, DIR-05)
- Historical Snapshot Records with distinct 4-way timestamps (DIR-01, DIR-02)
- Deterministic Immutability Hashing (DIR-02)
- Validation Results, Severities & Rules (DIR-07)
- Field-level Data Quality Classification (DIR-08)
- Duplicate Matching & Lineage Tracking (DIR-04, DIR-06)
- Data Provenance & Audit Trails (DIR-11)
- Temporal Eligibility & Point-in-time Filtering (DIR-01, DIR-10)
"""
from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class IdentityStatus(str, Enum):
    """Lifecycle status of a canonical project identity."""
    VERIFIED = "VERIFIED"
    PROVISIONAL = "PROVISIONAL"
    MERGED = "MERGED"
    DISPUTED = "DISPUTED"
    DEPRECATED = "DEPRECATED"


class ValidationStatus(str, Enum):
    """Result status of a validation rule execution."""
    PASSED = "PASSED"
    WARNING = "WARNING"
    FAILED = "FAILED"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    NOT_CHECKED = "NOT_CHECKED"


class ValidationSeverity(str, Enum):
    """Severity level of validation violations."""
    CRITICAL = "CRITICAL"  # Data cannot be used for any peer analysis
    ERROR = "ERROR"        # Metric cannot be used in benchmarking
    WARNING = "WARNING"    # Data usable with caveat / degraded confidence
    INFO = "INFO"          # Informational note / metadata notice


class FieldQualityStatus(str, Enum):
    """Standardized classification of individual field health."""
    VALID = "VALID"
    MISSING = "MISSING"
    INVALID = "INVALID"
    STALE = "STALE"
    CONFLICTING = "CONFLICTING"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    UNKNOWN = "UNKNOWN"


class DuplicateMatchLevel(str, Enum):
    """Classification level for potential duplicate project pairs."""
    EXACT_MATCH = "EXACT_MATCH"
    POSSIBLE_MATCH = "POSSIBLE_MATCH"
    NO_MATCH = "NO_MATCH"
    NEEDS_HUMAN_REVIEW = "NEEDS_HUMAN_REVIEW"


class TemporalEligibility(str, Enum):
    """Point-in-time snapshot eligibility for comparative analysis."""
    ELIGIBLE = "ELIGIBLE"
    FUTURE_OBSERVATION_EXCLUDED = "FUTURE_OBSERVATION_EXCLUDED"  # observation_date > as_of_date (lookahead prevention)
    FUTURE_INGESTION_EXCLUDED = "FUTURE_INGESTION_EXCLUDED"      # ingested_at > as_of_time
    INSUFFICIENT_HISTORY = "INSUFFICIENT_HISTORY"
    OUT_OF_SEQUENCE = "OUT_OF_SEQUENCE"


class NormalizationUnit(str, Enum):
    """Standard measurement units for metric comparison."""
    BASE_INR = "BASE_INR"
    CRORES = "CRORES"
    LAKHS = "LAKHS"
    MILLIONS = "MILLIONS"
    PERCENTAGE_0_1 = "PERCENTAGE_0_1"
    PERCENTAGE_0_100 = "PERCENTAGE_0_100"
    DAYS = "DAYS"
    MONTHS = "MONTHS"
    YEARS = "YEARS"


@dataclass
class CanonicalProjectIdentity:
    """Canonical identifier and master identity registry for a project.
    
    Prevents fragmentation when projects are renamed, code prefixes change,
    or multiple sources reference the same physical project.
    """
    canonical_project_id: str
    source_project_id: str
    project_name: str
    aliases: List[str] = field(default_factory=list)
    parent_project_id: Optional[str] = None
    child_project_ids: List[str] = field(default_factory=list)
    project_type: str = ""
    sector: str = ""
    implementing_agency: str = ""
    identity_status: IdentityStatus = IdentityStatus.PROVISIONAL
    confidence_score: float = 1.0
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "canonical_project_id": self.canonical_project_id,
            "source_project_id": self.source_project_id,
            "project_name": self.project_name,
            "aliases": list(self.aliases),
            "parent_project_id": self.parent_project_id,
            "child_project_ids": list(self.child_project_ids),
            "project_type": self.project_type,
            "sector": self.sector,
            "implementing_agency": self.implementing_agency,
            "identity_status": self.identity_status.value,
            "confidence_score": round(self.confidence_score, 4),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> CanonicalProjectIdentity:
        status_raw = data.get("identity_status", IdentityStatus.PROVISIONAL.value)
        try:
            status = IdentityStatus(status_raw)
        except ValueError:
            status = IdentityStatus.PROVISIONAL

        return cls(
            canonical_project_id=str(data.get("canonical_project_id", "")),
            source_project_id=str(data.get("source_project_id", "")),
            project_name=str(data.get("project_name", "")),
            aliases=list(data.get("aliases", [])),
            parent_project_id=data.get("parent_project_id"),
            child_project_ids=list(data.get("child_project_ids", [])),
            project_type=str(data.get("project_type", "")),
            sector=str(data.get("sector", "")),
            implementing_agency=str(data.get("implementing_agency", "")),
            identity_status=status,
            confidence_score=float(data.get("confidence_score", 1.0)),
            created_at=float(data.get("created_at", time.time())),
            updated_at=float(data.get("updated_at", time.time())),
            metadata=dict(data.get("metadata", {})),
        )


@dataclass
class ProjectSnapshot:
    """Historical snapshot record with bitemporal timestamps and cryptographic verification.
    
    Timestamps:
    - observation_date: Valid time (measurement period e.g. "2024-03-31")
    - source_updated_at: Timestamp given by originating agency/source
    - ingested_at: Timestamp when our ingestion pipeline received it
    - recorded_at: Transaction time when persisted in PAIMANA's store
    """
    snapshot_id: str
    canonical_project_id: str
    observation_date: str  # ISO YYYY-MM-DD
    recorded_at: float = field(default_factory=time.time)
    source_updated_at: Optional[str] = None
    ingested_at: float = field(default_factory=time.time)
    original_cost: Optional[float] = None
    revised_cost: Optional[float] = None
    expenditure: Optional[float] = None
    physical_progress: Optional[float] = None  # 0.0 to 100.0
    financial_progress: Optional[float] = None  # 0.0 to 100.0
    cost_overrun_pct: Optional[float] = None
    time_overrun_pct: Optional[float] = None
    schedule_delay_months: Optional[float] = None
    planned_start_date: Optional[str] = None
    planned_completion_date: Optional[str] = None
    actual_completion_date: Optional[str] = None
    status: str = "ONGOING"
    currency: str = "INR"
    cost_unit: str = "CRORES"
    data_source: str = "MOSPI"
    schema_version: str = "1.0.0"
    data_hash: str = ""
    raw_attributes: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.data_hash:
            self.data_hash = self.compute_hash()

    def compute_hash(self) -> str:
        """Computes deterministic SHA-256 hash over core invariant business attributes."""
        payload = {
            "canonical_project_id": self.canonical_project_id,
            "observation_date": self.observation_date,
            "original_cost": round(self.original_cost, 4) if self.original_cost is not None else None,
            "revised_cost": round(self.revised_cost, 4) if self.revised_cost is not None else None,
            "expenditure": round(self.expenditure, 4) if self.expenditure is not None else None,
            "physical_progress": round(self.physical_progress, 4) if self.physical_progress is not None else None,
            "financial_progress": round(self.financial_progress, 4) if self.financial_progress is not None else None,
            "cost_overrun_pct": round(self.cost_overrun_pct, 4) if self.cost_overrun_pct is not None else None,
            "time_overrun_pct": round(self.time_overrun_pct, 4) if self.time_overrun_pct is not None else None,
            "schedule_delay_months": round(self.schedule_delay_months, 4) if self.schedule_delay_months is not None else None,
            "planned_start_date": self.planned_start_date,
            "planned_completion_date": self.planned_completion_date,
            "actual_completion_date": self.actual_completion_date,
            "status": self.status,
            "currency": self.currency,
            "cost_unit": self.cost_unit,
            "data_source": self.data_source,
            "schema_version": self.schema_version,
        }
        serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def verify_hash(self) -> bool:
        """Returns True if the stored data_hash matches the currently computed hash."""
        return self.data_hash == self.compute_hash()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "canonical_project_id": self.canonical_project_id,
            "observation_date": self.observation_date,
            "recorded_at": self.recorded_at,
            "source_updated_at": self.source_updated_at,
            "ingested_at": self.ingested_at,
            "original_cost": self.original_cost,
            "revised_cost": self.revised_cost,
            "expenditure": self.expenditure,
            "physical_progress": self.physical_progress,
            "financial_progress": self.financial_progress,
            "cost_overrun_pct": self.cost_overrun_pct,
            "time_overrun_pct": self.time_overrun_pct,
            "schedule_delay_months": self.schedule_delay_months,
            "planned_start_date": self.planned_start_date,
            "planned_completion_date": self.planned_completion_date,
            "actual_completion_date": self.actual_completion_date,
            "status": self.status,
            "currency": self.currency,
            "cost_unit": self.cost_unit,
            "data_source": self.data_source,
            "schema_version": self.schema_version,
            "data_hash": self.data_hash,
            "raw_attributes": self.raw_attributes,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ProjectSnapshot:
        return cls(
            snapshot_id=str(data.get("snapshot_id", "")),
            canonical_project_id=str(data.get("canonical_project_id", "")),
            observation_date=str(data.get("observation_date", "")),
            recorded_at=float(data.get("recorded_at", time.time())),
            source_updated_at=data.get("source_updated_at"),
            ingested_at=float(data.get("ingested_at", time.time())),
            original_cost=_to_opt_float(data.get("original_cost")),
            revised_cost=_to_opt_float(data.get("revised_cost")),
            expenditure=_to_opt_float(data.get("expenditure")),
            physical_progress=_to_opt_float(data.get("physical_progress")),
            financial_progress=_to_opt_float(data.get("financial_progress")),
            cost_overrun_pct=_to_opt_float(data.get("cost_overrun_pct")),
            time_overrun_pct=_to_opt_float(data.get("time_overrun_pct")),
            schedule_delay_months=_to_opt_float(data.get("schedule_delay_months")),
            planned_start_date=data.get("planned_start_date"),
            planned_completion_date=data.get("planned_completion_date"),
            actual_completion_date=data.get("actual_completion_date"),
            status=str(data.get("status", "ONGOING")),
            currency=str(data.get("currency", "INR")),
            cost_unit=str(data.get("cost_unit", "CRORES")),
            data_source=str(data.get("data_source", "MOSPI")),
            schema_version=str(data.get("schema_version", "1.0.0")),
            data_hash=str(data.get("data_hash", "")),
            raw_attributes=dict(data.get("raw_attributes", {})),
        )

    def to_peer_record(self, identity: Optional[CanonicalProjectIdentity] = None) -> Dict[str, Any]:
        """Convert snapshot into the dictionary format expected by existing peer engines."""
        return {
            "project_code": self.canonical_project_id,
            "project_name": identity.project_name if identity else self.canonical_project_id,
            "sector": identity.sector if identity else "",
            "project_type": identity.project_type if identity else "",
            "implementing_agency": identity.implementing_agency if identity else "",
            "original_cost": self.original_cost,
            "revised_cost": self.revised_cost,
            "expenditure": self.expenditure,
            "physical_progress": self.physical_progress,
            "cost_overrun_pct": self.cost_overrun_pct,
            "time_overrun_pct": self.time_overrun_pct,
            "schedule_delay_months": self.schedule_delay_months,
            "snapshot_date": self.observation_date,
            "status": self.status,
        }


@dataclass
class ValidationResult:
    """Individual assertion outcome against a domain data rule."""
    rule_id: str
    field: str
    status: ValidationStatus
    severity: ValidationSeverity
    observed_value: Any
    expected: str
    message: str
    source: str = "DataIntegrityEngine"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "field": self.field,
            "status": self.status.value,
            "severity": self.severity.value,
            "observed_value": self.observed_value,
            "expected": self.expected,
            "message": self.message,
            "source": self.source,
        }


@dataclass
class FieldQualityReport:
    """Quality and completeness evaluation for a specific attribute."""
    field_name: str
    status: FieldQualityStatus
    score: float  # 0.0 to 1.0
    details: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "field_name": self.field_name,
            "status": self.status.value,
            "score": round(self.score, 4),
            "details": self.details,
        }


@dataclass
class DuplicateCandidate:
    """Candidate match between two project entities."""
    canonical_project_id: str
    candidate_project_id: str
    match_level: DuplicateMatchLevel
    confidence_score: float
    matching_criteria: List[str] = field(default_factory=list)
    differing_criteria: List[str] = field(default_factory=list)
    recommended_action: str = "MANUAL_REVIEW"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "canonical_project_id": self.canonical_project_id,
            "candidate_project_id": self.candidate_project_id,
            "match_level": self.match_level.value,
            "confidence_score": round(self.confidence_score, 4),
            "matching_criteria": self.matching_criteria,
            "differing_criteria": self.differing_criteria,
            "recommended_action": self.recommended_action,
        }


@dataclass
class DataProvenanceRecord:
    """Cryptographic audit trail capturing data origin, ingestion, and transformations."""
    record_id: str
    entity_type: str  # "ProjectSnapshot", "CanonicalIdentity"
    entity_id: str
    source_system: str
    raw_payload_hash: str
    transformations: List[Dict[str, Any]] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    created_by: str = "DataIntegrityPipeline"
    version: int = 1
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "record_id": self.record_id,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "source_system": self.source_system,
            "raw_payload_hash": self.raw_payload_hash,
            "transformations": self.transformations,
            "created_at": self.created_at,
            "created_by": self.created_by,
            "version": self.version,
            "metadata": self.metadata,
        }


@dataclass
class IntegrityEvaluationReport:
    """Comprehensive integrity evaluation for a project or snapshot."""
    canonical_project_id: str
    snapshot_id: Optional[str] = None
    is_valid: bool = True
    overall_score: float = 1.0  # 0.0 to 1.0
    temporal_eligibility: TemporalEligibility = TemporalEligibility.ELIGIBLE
    validation_results: List[ValidationResult] = field(default_factory=list)
    field_qualities: Dict[str, FieldQualityReport] = field(default_factory=dict)
    provenance: Optional[DataProvenanceRecord] = None
    summary: str = ""
    evaluated_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "canonical_project_id": self.canonical_project_id,
            "snapshot_id": self.snapshot_id,
            "is_valid": self.is_valid,
            "overall_score": round(self.overall_score, 4),
            "temporal_eligibility": self.temporal_eligibility.value,
            "validation_results": [v.to_dict() for v in self.validation_results],
            "field_qualities": {k: v.to_dict() for k, v in self.field_qualities.items()},
            "provenance": self.provenance.to_dict() if self.provenance else None,
            "summary": self.summary,
            "evaluated_at": self.evaluated_at,
        }


def _to_opt_float(val: Any) -> Optional[float]:
    """Helper to convert string/numeric values into Optional[float]."""
    if val is None:
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None
