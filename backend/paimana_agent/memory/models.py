"""First-Class Institutional Memory & Precedent Data Models.

Defines the formal structures for institutional learning:
- PatternFingerprint: Compact structured representation of project anomaly patterns.
- PrecedentContext: Multi-dimensional environmental, sector, and contract context.
- PrecedentProvenance: Evidentiary lineage, validation history, and independence groups.
- Precedent: The primary durable unit of validated institutional knowledge.
- PrecedentBundle: Multi-perspective retrieval output containing positive precedents,
  failure precedents, and counterexamples.
- InvestigationMemory: Complete audit replay model for completed investigations.
"""
from __future__ import annotations
import time
from dataclasses import dataclass, field
from typing import Any, Literal, Optional

PrecedentStatus = Literal[
    "CANDIDATE",      # Extracted from investigation, awaiting real-world outcome
    "VALIDATED",      # Empirical outcome verified and attributed
    "PROVISIONAL",    # Early partial outcome recorded
    "SUPERSEDED",     # Replaced by newer consolidated precedent
    "CONTRADICTED",   # Subsequent investigation or outcome refuted causal link
    "REJECTED",       # Evidence quality or attribution failed checks
    "STALE"           # Temporal relevance expired
]

AttributionClass = Literal[
    "LIKELY_EFFECTIVE",
    "POSSIBLY_EFFECTIVE",
    "INCONCLUSIVE",
    "LIKELY_INEFFECTIVE",
    "FAILED"
]


@dataclass
class PatternFingerprint:
    """Structured, compact fingerprint of anomaly dynamics for non-semantic matching."""
    event_type: str = "general_review"
    risk_direction: str = "stable"       # increasing, stable, decreasing
    risk_velocity: str = "moderate"      # fast, moderate, slow
    progress_variance: str = "low"       # high, moderate, low
    milestone_slippage: str = "none"     # persistent, moderate, none
    financial_velocity: str = "balanced" # decoupled, ahead, balanced, behind
    approval_delay: str = "low"          # high, moderate, low
    contractor_delay: str = "low"        # high, moderate, low

    def to_dict(self) -> dict:
        return {
            "event_type": self.event_type,
            "risk_direction": self.risk_direction,
            "risk_velocity": self.risk_velocity,
            "progress_variance": self.progress_variance,
            "milestone_slippage": self.milestone_slippage,
            "financial_velocity": self.financial_velocity,
            "approval_delay": self.approval_delay,
            "contractor_delay": self.contractor_delay,
        }

    @classmethod
    def from_dict(cls, data: dict) -> PatternFingerprint:
        if not data:
            return cls()
        return cls(
            event_type=data.get("event_type", "general_review"),
            risk_direction=data.get("risk_direction", "stable"),
            risk_velocity=data.get("risk_velocity", "moderate"),
            progress_variance=data.get("progress_variance", "low"),
            milestone_slippage=data.get("milestone_slippage", "none"),
            financial_velocity=data.get("financial_velocity", "balanced"),
            approval_delay=data.get("approval_delay", "low"),
            contractor_delay=data.get("contractor_delay", "low"),
        )


@dataclass
class PrecedentContext:
    """Contextual envelope defining boundary conditions for precedent transferability."""
    sector: str = "General Infrastructure"
    project_type: str = "Civil Works"
    project_size_cr: float = 0.0
    cost_band: str = "Standard (150-1000Cr)" # Mega (>1000Cr), Standard, Minor
    stage_bracket: str = "Mid (25-75%)"     # Early (<25%), Mid (25-75%), Late (>75%)
    implementing_agency: str = ""
    state: str = ""
    contract_type: str = "EPC"              # EPC, Item Rate, HAM, DBFOT, Standard

    def to_dict(self) -> dict:
        return {
            "sector": self.sector,
            "project_type": self.project_type,
            "project_size_cr": round(self.project_size_cr, 1),
            "cost_band": self.cost_band,
            "stage_bracket": self.stage_bracket,
            "implementing_agency": self.implementing_agency,
            "state": self.state,
            "contract_type": self.contract_type,
        }

    @classmethod
    def from_dict(cls, data: dict) -> PrecedentContext:
        if not data:
            return cls()
        return cls(
            sector=str(data.get("sector", "General Infrastructure")),
            project_type=str(data.get("project_type", "Civil Works")),
            project_size_cr=float(data.get("project_size_cr", 0.0)),
            cost_band=str(data.get("cost_band", "Standard (150-1000Cr)")),
            stage_bracket=str(data.get("stage_bracket", "Mid (25-75%)")),
            implementing_agency=str(data.get("implementing_agency", "")),
            state=str(data.get("state", "")),
            contract_type=str(data.get("contract_type", "EPC")),
        )


@dataclass
class PrecedentProvenance:
    """Audit lineage tracking source investigations, evidence, and independent corroborations."""
    source_investigation_ids: list[str] = field(default_factory=list)
    source_project_codes: list[str] = field(default_factory=list)
    source_evidence_ids: list[str] = field(default_factory=list)
    independence_group_ids: list[str] = field(default_factory=list)
    validation_history: list[dict] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    last_validated_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "source_investigation_ids": list(self.source_investigation_ids),
            "source_project_codes": list(self.source_project_codes),
            "source_evidence_ids": list(self.source_evidence_ids),
            "independence_group_ids": list(self.independence_group_ids),
            "validation_history": self.validation_history,
            "created_at": self.created_at,
            "last_validated_at": self.last_validated_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> PrecedentProvenance:
        if not data:
            return cls()
        return cls(
            source_investigation_ids=list(data.get("source_investigation_ids", [])),
            source_project_codes=list(data.get("source_project_codes", [])),
            source_evidence_ids=list(data.get("source_evidence_ids", [])),
            independence_group_ids=list(data.get("independence_group_ids", [])),
            validation_history=list(data.get("validation_history", [])),
            created_at=float(data.get("created_at", time.time())),
            last_validated_at=float(data.get("last_validated_at", time.time())),
        )


@dataclass
class Precedent:
    """The fundamental durable unit of validated institutional knowledge."""
    id: str
    title: str
    event_pattern: dict = field(default_factory=dict)
    pattern_fingerprint: PatternFingerprint = field(default_factory=PatternFingerprint)
    context: PrecedentContext = field(default_factory=PrecedentContext)
    
    # Evidentiary & Causal Signatures
    evidence_pattern: list[str] = field(default_factory=list)
    hypothesis_pattern: list[str] = field(default_factory=list)
    root_cause: str = ""
    root_cause_confidence: float = 0.50

    # Intervention & Outcome Learning
    intervention: dict = field(default_factory=dict)
    intervention_class: str = "CATCH_UP_PLAN"
    expected_outcome: dict = field(default_factory=dict)
    observed_outcome: dict = field(default_factory=dict)

    # Evaluated Effectiveness & Epistemic Trust
    outcome_quality: float = 0.50
    intervention_effectiveness: float = 0.50
    attribution_class: str = "INCONCLUSIVE"
    memory_reliability: float = 0.80
    transferability_score: float = 0.70

    # Traceability & Provenance
    source_investigation_id: str = ""
    source_project_id: str = ""
    provenance: PrecedentProvenance = field(default_factory=PrecedentProvenance)
    created_at: float = field(default_factory=time.time)
    last_validated_at: float = field(default_factory=time.time)
    status: PrecedentStatus = "VALIDATED"

    # Multi-Application Empirical Counters
    application_count: int = 1
    success_count: int = 1
    failure_count: int = 0

    # Counterexample metadata (prevents confirmation bias)
    is_counterexample: bool = False
    counterexample_for_hypotheses: list[str] = field(default_factory=list)
    why_relevant: str = ""
    important_differences: str = ""
    usage_guidance: str = ""

    @property
    def track_record(self) -> float:
        """Laplace-smoothed Bayesian success probability."""
        return (self.success_count + 1.0) / (self.success_count + self.failure_count + 2.0)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "event_pattern": self.event_pattern,
            "pattern_fingerprint": self.pattern_fingerprint.to_dict(),
            "context": self.context.to_dict(),
            "evidence_pattern": list(self.evidence_pattern),
            "hypothesis_pattern": list(self.hypothesis_pattern),
            "root_cause": self.root_cause,
            "root_cause_confidence": round(self.root_cause_confidence, 3),
            "intervention": self.intervention,
            "intervention_class": self.intervention_class,
            "expected_outcome": self.expected_outcome,
            "observed_outcome": self.observed_outcome,
            "outcome_quality": round(self.outcome_quality, 3),
            "intervention_effectiveness": round(self.intervention_effectiveness, 3),
            "attribution_class": self.attribution_class,
            "memory_reliability": round(self.memory_reliability, 3),
            "transferability_score": round(self.transferability_score, 3),
            "source_investigation_id": self.source_investigation_id,
            "source_project_id": self.source_project_id,
            "provenance": self.provenance.to_dict(),
            "created_at": self.created_at,
            "last_validated_at": self.last_validated_at,
            "status": self.status,
            "application_count": self.application_count,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "is_counterexample": self.is_counterexample,
            "counterexample_for_hypotheses": list(self.counterexample_for_hypotheses),
            "why_relevant": self.why_relevant,
            "important_differences": self.important_differences,
            "usage_guidance": self.usage_guidance,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Precedent:
        if not data:
            return cls(id="UNKNOWN", title="Unknown")
        pf_data = data.get("pattern_fingerprint") or {}
        ctx_data = data.get("context") or {}
        prov_data = data.get("provenance") or {}

        pf = PatternFingerprint.from_dict(pf_data) if isinstance(pf_data, dict) else pf_data
        ctx = PrecedentContext.from_dict(ctx_data) if isinstance(ctx_data, dict) else ctx_data
        prov = PrecedentProvenance.from_dict(prov_data) if isinstance(prov_data, dict) else prov_data

        return cls(
            id=str(data.get("id", "")),
            title=str(data.get("title", "")),
            event_pattern=dict(data.get("event_pattern", {})),
            pattern_fingerprint=pf,
            context=ctx,
            evidence_pattern=list(data.get("evidence_pattern", [])),
            hypothesis_pattern=list(data.get("hypothesis_pattern", [])),
            root_cause=str(data.get("root_cause", "")),
            root_cause_confidence=float(data.get("root_cause_confidence", 0.50)),
            intervention=dict(data.get("intervention", {})),
            intervention_class=str(data.get("intervention_class", "CATCH_UP_PLAN")),
            expected_outcome=dict(data.get("expected_outcome", {})),
            observed_outcome=dict(data.get("observed_outcome", {})),
            outcome_quality=float(data.get("outcome_quality", 0.50)),
            intervention_effectiveness=float(data.get("intervention_effectiveness", 0.50)),
            attribution_class=data.get("attribution_class", "INCONCLUSIVE"),
            memory_reliability=float(data.get("memory_reliability", 0.80)),
            transferability_score=float(data.get("transferability_score", 0.70)),
            source_investigation_id=str(data.get("source_investigation_id", "")),
            source_project_id=str(data.get("source_project_id", "")),
            provenance=prov,
            created_at=float(data.get("created_at", time.time())),
            last_validated_at=float(data.get("last_validated_at", time.time())),
            status=data.get("status", "VALIDATED"),
            application_count=int(data.get("application_count", 1)),
            success_count=int(data.get("success_count", 1)),
            failure_count=int(data.get("failure_count", 0)),
            is_counterexample=bool(data.get("is_counterexample", False)),
            counterexample_for_hypotheses=list(data.get("counterexample_for_hypotheses", [])),
            why_relevant=str(data.get("why_relevant", "")),
            important_differences=str(data.get("important_differences", "")),
            usage_guidance=str(data.get("usage_guidance", "")),
        )


@dataclass
class PrecedentBundle:
    """Tri-perspective retrieval bundle providing supporting, failed, and counterexample precedents."""
    target_project_code: str
    target_pattern: PatternFingerprint
    supporting_precedents: list[Precedent] = field(default_factory=list)
    failed_precedents: list[Precedent] = field(default_factory=list)
    counterexamples: list[Precedent] = field(default_factory=list)
    relevance_explanations: list[dict] = field(default_factory=list)
    recommended_hypotheses: list[str] = field(default_factory=list)
    recommended_tools: list[str] = field(default_factory=list)
    recommendation_guidance: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "target_project_code": self.target_project_code,
            "target_pattern": self.target_pattern.to_dict(),
            "supporting_precedents": [p.to_dict() for p in self.supporting_precedents],
            "failed_precedents": [p.to_dict() for p in self.failed_precedents],
            "counterexamples": [p.to_dict() for p in self.counterexamples],
            "relevance_explanations": self.relevance_explanations,
            "recommended_hypotheses": list(self.recommended_hypotheses),
            "recommended_tools": list(self.recommended_tools),
            "recommendation_guidance": list(self.recommendation_guidance),
            "total_precedents_evaluated": (len(self.supporting_precedents) +
                                           len(self.failed_precedents) +
                                           len(self.counterexamples)),
        }


@dataclass
class InvestigationMemory:
    """Historical audit and replay model for a completed investigation."""
    investigation_id: str
    project_code: str
    project_name: str
    timestamp: float
    trigger_events: list[dict]
    facts: list[dict]
    evidence_items: list[dict]
    hypotheses: list[dict]
    tools_invoked: list[str]
    decision_trace: list[dict]
    confidence_score: float
    termination_reason: str
    selected_recommendation: Optional[dict] = None

    def to_dict(self) -> dict:
        return {
            "investigation_id": self.investigation_id,
            "project_code": self.project_code,
            "project_name": self.project_name,
            "timestamp": self.timestamp,
            "trigger_events": self.trigger_events,
            "facts": self.facts,
            "evidence_items": self.evidence_items,
            "hypotheses": self.hypotheses,
            "tools_invoked": self.tools_invoked,
            "decision_trace": self.decision_trace,
            "confidence_score": round(self.confidence_score, 3),
            "termination_reason": self.termination_reason,
            "selected_recommendation": self.selected_recommendation,
        }

    @classmethod
    def from_dict(cls, data: dict) -> InvestigationMemory:
        if not data:
            return cls(
                investigation_id="", project_code="", project_name="", timestamp=time.time(),
                trigger_events=[], facts=[], evidence_items=[], hypotheses=[],
                tools_invoked=[], decision_trace=[], confidence_score=0.0,
                termination_reason="unknown"
            )
        return cls(
            investigation_id=str(data.get("investigation_id", "")),
            project_code=str(data.get("project_code", "")),
            project_name=str(data.get("project_name", "")),
            timestamp=float(data.get("timestamp", time.time())),
            trigger_events=list(data.get("trigger_events", [])),
            facts=list(data.get("facts", [])),
            evidence_items=list(data.get("evidence_items", [])),
            hypotheses=list(data.get("hypotheses", [])),
            tools_invoked=list(data.get("tools_invoked", [])),
            decision_trace=list(data.get("decision_trace", [])),
            confidence_score=float(data.get("confidence_score", 0.0)),
            termination_reason=str(data.get("termination_reason", "")),
            selected_recommendation=data.get("selected_recommendation"),
        )
