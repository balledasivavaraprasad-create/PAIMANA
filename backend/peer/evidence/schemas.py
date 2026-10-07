"""Formal Data Contracts, Schemas & Semantic State Models for Evidence & Semantic Safety (ESS-01 to ESS-10).

Defines canonical representations for:
- Standardized Evidence Objects & Provenance Lineage (ESS-01, ESS-02)
- Multi-Dimensional Reliability Profiling (ESS-03)
- Semantic Graph Relations (ESS-04)
- 5-Level Cognitive Claim Hierarchy & Validation (ESS-05, ESS-06)
- Causal Claim Guard & Semantic Safety Rules (ESS-07)
- Evidence Contradiction Modeling (ESS-08)
- Unsupported Claim Auditing (ESS-09)
- Semantic-Safe Report Structures (ESS-10)
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class EvidenceRelationType(str, Enum):
    """Strict relational edge semantics connecting evidence to nodes and hypotheses (ESS-04)."""
    OBSERVES = "OBSERVES"  # Direct measurement of a parameter
    SUPPORTS = "SUPPORTS"  # Probabilistically strengthens a finding or hypothesis
    CONTRADICTS = "CONTRADICTS"  # Falsifies or significantly weakens a hypothesis
    CONTEXTUALIZES = "CONTEXTUALIZES"  # Provides background conditions without proving causation
    DERIVED_FROM = "DERIVED_FROM"  # Mathematical or computational child of upstream evidence
    CORROBORATES = "CORROBORATES"  # Independent source confirming identical observation


class ReliabilityTier(str, Enum):
    """Categorical reliability tiers of evidentiary sources (ESS-03)."""
    CONFIRMED = "CONFIRMED"  # Official signed/certified ground truth (e.g., audited ledger)
    SUPPORTED = "SUPPORTED"  # Verified calculation from official source records
    CORROBORATED = "CORROBORATED"  # Confirmed across multiple independent sources
    CONTEXTUAL = "CONTEXTUAL"  # Peer comparative or historical precedent signal
    UNVERIFIED = "UNVERIFIED"  # Uncorroborated estimate, proxy, or text inference


class ClaimLevel(str, Enum):
    """5-Level Cognitive Claim Hierarchy (ESS-05)."""
    OBSERVATION = "OBSERVATION"  # Level 1: Raw empirical measurement (e.g., spend = 78%)
    DERIVED_FINDING = "DERIVED_FINDING"  # Level 2: Calculated differential (e.g., gap = 32pp)
    INTERPRETATION = "INTERPRETATION"  # Level 3: Qualitative synthesis (e.g., mismatch exists)
    HYPOTHESIS = "HYPOTHESIS"  # Level 4: Competing causal candidate (e.g., front-loaded advances)
    CAUSAL = "CAUSAL"  # Level 5: Verified causal explanation (requires causal proof)
    ATTRIBUTION = "ATTRIBUTION"  # Level 5b: Culpability attribution (requires authoritative evidence)


class ClaimStatus(str, Enum):
    """Verification status of candidate claims (ESS-06, ESS-09)."""
    SUPPORTED = "SUPPORTED"  # Rigorously established by direct or derived evidence
    PARTIALLY_SUPPORTED = "PARTIALLY_SUPPORTED"  # Some supporting evidence, minor gaps remain
    CONTEXTUAL = "CONTEXTUAL"  # Backed only by contextual or peer evidence
    UNVERIFIED = "UNVERIFIED"  # Lacks empirical verification in active registry
    CONTRADICTED = "CONTRADICTED"  # Directly challenged by opposing empirical facts
    UNSUPPORTED = "UNSUPPORTED"  # Zero supporting evidence or violates semantic safety


# ==============================================================================
# 1. Provenance & Reliability Schemas (ESS-02, ESS-03)
# ==============================================================================

@dataclass
class EvidenceProvenance:
    """Detailed source lineage and audit trail (ESS-02)."""
    source: str  # e.g., "CUF Financial Ledger", "MoRTH Monthly Progress Report"
    source_id: str  # e.g., "financial_velocity", "milestone_audit", "peer_intelligence"
    project_id: str  # e.g., "PROJECT_101"
    snapshot_id: Optional[str] = None  # e.g., "SNAP-2026-09-30"
    observation_date: Optional[str] = None
    ingestion_date: str = field(default_factory=lambda: time.strftime("%Y-%m-%d %H:%M:%S"))
    tool_name: str = ""
    tool_version: str = "1.0.0"
    algorithm_version: str = "1.0.0"
    input_hash: str = ""  # sha256 hash of input parameters & payload
    calculation_method: str = ""
    transformation_history: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source,
            "source_id": self.source_id,
            "project_id": self.project_id,
            "snapshot_id": self.snapshot_id,
            "observation_date": self.observation_date,
            "ingestion_date": self.ingestion_date,
            "tool_name": self.tool_name,
            "tool_version": self.tool_version,
            "algorithm_version": self.algorithm_version,
            "input_hash": self.input_hash,
            "calculation_method": self.calculation_method,
            "transformation_history": self.transformation_history,
        }


@dataclass
class EvidenceReliability:
    """Multi-dimensional reliability evaluation (ESS-03)."""
    source_quality: str = "HIGH"  # HIGH, MEDIUM, LOW, MODEL_DERIVED, UNVERIFIED
    freshness: str = "CURRENT"  # CURRENT, RECENT, STALE, HISTORICAL
    provenance_completeness: str = "COMPLETE"  # COMPLETE, PARTIAL, MISSING
    methodological_quality: str = "HIGH"  # HIGH, ESTIMATED, HEURISTIC
    corroboration: str = "SINGLE_SOURCE"  # MULTI_SOURCE, CORROBORATED, SINGLE_SOURCE, UNCORROBORATED
    overall_tier: ReliabilityTier = ReliabilityTier.SUPPORTED
    reliability_score: float = 0.85

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_quality": self.source_quality,
            "freshness": self.freshness,
            "provenance_completeness": self.provenance_completeness,
            "methodological_quality": self.methodological_quality,
            "corroboration": self.corroboration,
            "overall_tier": self.overall_tier.value,
            "reliability_score": round(self.reliability_score, 2),
        }


# ==============================================================================
# 2. Canonical Evidence Schema (ESS-01)
# ==============================================================================

@dataclass
class Evidence:
    """Canonical standardized evidence object across all PAIMANA subsystems (ESS-01)."""
    evidence_id: str
    project_id: str
    evidence_type: str  # e.g., "COST_PROGRESS_MISMATCH", "SCHEDULE_SLIPPAGE"
    source_type: str  # e.g., "FINANCIAL_TOOL", "PEER_INTELLIGENCE", "DOMAIN_CONTEXT"
    source_id: str  # specific tool or table ID
    observation: str
    value: Any = None
    unit: Optional[str] = None
    as_of_date: Optional[str] = None
    observed_at: float = field(default_factory=time.time)
    methodology: str = ""
    confidence: float = 0.90
    provenance: Optional[EvidenceProvenance] = None
    reliability: Optional[EvidenceReliability] = None
    limitations: List[str] = field(default_factory=list)
    semantic_status: ReliabilityTier = ReliabilityTier.SUPPORTED

    def to_dict(self) -> Dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "project_id": self.project_id,
            "evidence_type": self.evidence_type,
            "source_type": self.source_type,
            "source_id": self.source_id,
            "observation": self.observation,
            "value": self.value,
            "unit": self.unit,
            "as_of_date": self.as_of_date,
            "observed_at": self.observed_at,
            "methodology": self.methodology,
            "confidence": round(self.confidence, 2),
            "provenance": self.provenance.to_dict() if self.provenance else None,
            "reliability": self.reliability.to_dict() if self.reliability else None,
            "limitations": self.limitations,
            "semantic_status": self.semantic_status.value,
        }


# ==============================================================================
# 3. Semantic Relations & Claim Hierarchy Schemas (ESS-04, ESS-05, ESS-06)
# ==============================================================================

@dataclass
class SemanticRelation:
    """Explicit semantic edge linking evidence to hypotheses, claims, or other evidence (ESS-04)."""
    relation_id: str
    source_id: str
    target_id: str
    relation_type: EvidenceRelationType
    confidence: float = 1.0
    rationale: str = ""
    created_by: str = "deterministic_engine"
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "relation_id": self.relation_id,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "relation_type": self.relation_type.value,
            "confidence": round(self.confidence, 2),
            "rationale": self.rationale,
            "created_by": self.created_by,
            "timestamp": self.timestamp,
        }


@dataclass
class Claim:
    """Structured analytical claim evaluated against registered evidence (ESS-05, ESS-06)."""
    claim_id: str
    project_id: str
    statement: str
    claim_level: ClaimLevel
    evidence_ids: List[str] = field(default_factory=list)
    status: ClaimStatus = ClaimStatus.UNVERIFIED
    required_level: ClaimLevel = ClaimLevel.OBSERVATION
    limitations: List[str] = field(default_factory=list)
    audit_note: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "claim_id": self.claim_id,
            "project_id": self.project_id,
            "statement": self.statement,
            "claim_level": self.claim_level.value,
            "evidence_ids": self.evidence_ids,
            "status": self.status.value,
            "required_level": self.required_level.value,
            "limitations": self.limitations,
            "audit_note": self.audit_note,
        }


# ==============================================================================
# 4. Causal Guard, Contradiction & Safety Audit Schemas (ESS-07, ESS-08, ESS-09)
# ==============================================================================

@dataclass
class SemanticSafetyRule:
    """Safety guardrail preventing unwarranted semantic escalation (ESS-07)."""
    rule_id: str
    rule_name: str
    description: str
    prohibited_escalation: str
    enforcement_action: str  # REJECT, DOWNGRADE, QUALIFY


@dataclass
class ContradictionRecord:
    """Explicit contradiction where empirical evidence directly challenges a claim (ESS-08)."""
    contradiction_id: str
    claim_or_hypothesis: str
    evidence_ids: List[str]
    conflicting_evidence_ids: List[str]
    severity: str = "HIGH"  # CRITICAL, HIGH, MODERATE, LOW
    impact: str = "REDUCE_CONFIDENCE"
    resolution_action: str = ""
    resolved: bool = False
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "contradiction_id": self.contradiction_id,
            "claim_or_hypothesis": self.claim_or_hypothesis,
            "evidence_ids": self.evidence_ids,
            "conflicting_evidence_ids": self.conflicting_evidence_ids,
            "severity": self.severity,
            "impact": self.impact,
            "resolution_action": self.resolution_action,
            "resolved": self.resolved,
            "timestamp": self.timestamp,
        }


@dataclass
class SemanticSafetyAuditReport:
    """Pre-report semantic audit result enforcing zero unsupported claims (ESS-09)."""
    total_claims_evaluated: int
    supported_claims: List[Claim] = field(default_factory=list)
    downgraded_claims: List[Claim] = field(default_factory=list)
    rejected_claims: List[Claim] = field(default_factory=list)
    violations_prevented: List[Dict[str, str]] = field(default_factory=list)
    unsupported_claim_rate: float = 0.0
    passed_safety_gate: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_claims_evaluated": self.total_claims_evaluated,
            "supported_count": len(self.supported_claims),
            "downgraded_count": len(self.downgraded_claims),
            "rejected_count": len(self.rejected_claims),
            "violations_prevented": self.violations_prevented,
            "unsupported_claim_rate": round(self.unsupported_claim_rate, 3),
            "passed_safety_gate": self.passed_safety_gate,
        }


# ==============================================================================
# 5. Semantic-Safe Final Report Schema (ESS-10)
# ==============================================================================

@dataclass
class SemanticSafeReport:
    """Final executive report strictly bounded by evidentiary provenance (ESS-10)."""
    project_id: str
    project_name: str
    observations: List[str] = field(default_factory=list)
    derived_findings: List[str] = field(default_factory=list)
    hypotheses_evaluated: List[Dict[str, Any]] = field(default_factory=list)
    context_factors: List[str] = field(default_factory=list)
    evidence_gaps: List[str] = field(default_factory=list)
    semantic_safety_notes: List[str] = field(default_factory=list)
    audit_summary: Optional[SemanticSafetyAuditReport] = None
    executive_narrative: str = ""
    human_approval_required: bool = True
    generated_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_id": self.project_id,
            "project_name": self.project_name,
            "observations": self.observations,
            "derived_findings": self.derived_findings,
            "hypotheses_evaluated": self.hypotheses_evaluated,
            "context_factors": self.context_factors,
            "evidence_gaps": self.evidence_gaps,
            "semantic_safety_notes": self.semantic_safety_notes,
            "audit_summary": self.audit_summary.to_dict() if self.audit_summary else None,
            "executive_narrative": self.executive_narrative,
            "human_approval_required": self.human_approval_required,
            "generated_at": self.generated_at,
        }
