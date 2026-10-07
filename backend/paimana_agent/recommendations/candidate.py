"""First-class RecommendationCandidate entity with structured provenance, multi-criteria metrics, and decision tracing."""
from __future__ import annotations
from dataclasses import dataclass, field
import time
from typing import Any, Optional


@dataclass
class RecommendationCandidate:
    """A first-class, structured recommendation candidate evaluated through multi-criteria ranking."""
    id: str = ""
    title: str = ""
    action_type: str = "PRIMARY_RECOVERY"

    description: str = ""
    rationale: str = ""

    hypothesis_ids: list[str] = field(default_factory=list)
    evidence_ids: list[str] = field(default_factory=list)

    expected_benefit: float = 0.50
    expected_cost: float = 0.30
    expected_risk_reduction: float = 0.50
    implementation_risk: float = 0.20
    evidence_strength: float = 0.50
    authority_score: float = 0.80

    feasibility: Optional[float] = 0.85
    time_to_impact: Optional[float] = 30.0
    confidence: float = 0.50

    responsible_stakeholder: str = "Project Director"
    urgency: str = "MEDIUM"
    approval_class: str = "managerial"
    constraints: list[str] = field(default_factory=list)

    tradeoffs: str = ""
    risks: str = ""
    uncertainty: str = "LOW"
    precedent_outcome: Optional[str] = None
    expected_impact: str = ""

    score_breakdown: dict[str, Any] = field(default_factory=dict)
    validation_status: str = "VALID"
    validation_reasons: list[str] = field(default_factory=list)
    utility_score: float = 0.50
    confidence_adjusted_score: float = 0.50
    rank: Optional[int] = None
    is_dominated: bool = False

    generated_by: str = "playbook"
    generation_version: str = "v4.0"
    created_at: float = field(default_factory=time.time)

    def __init__(
        self,
        id: str = "",
        title: str = "",
        action_type: str = "PRIMARY_RECOVERY",
        description: str = "",
        rationale: str = "",
        hypothesis_ids: Optional[list[str]] = None,
        evidence_ids: Optional[list[str]] = None,
        expected_benefit: float = 0.50,
        expected_cost: float = 0.30,
        expected_risk_reduction: float = 0.50,
        implementation_risk: float = 0.20,
        evidence_strength: float = 0.50,
        authority_score: float = 0.80,
        feasibility: Optional[float] = 0.85,
        time_to_impact: Optional[float] = 30.0,
        confidence: float = 0.50,
        responsible_stakeholder: str = "Project Director",
        urgency: str = "MEDIUM",
        approval_class: str = "managerial",
        constraints: Optional[list[str]] = None,
        tradeoffs: str = "",
        risks: str = "",
        uncertainty: str = "LOW",
        precedent_outcome: Optional[str] = None,
        expected_impact: str = "",
        score_breakdown: Optional[dict[str, Any]] = None,
        validation_status: str = "VALID",
        validation_reasons: Optional[list[str]] = None,
        utility_score: float = 0.50,
        confidence_adjusted_score: float = 0.50,
        rank: Optional[int] = None,
        is_dominated: bool = False,
        generated_by: str = "playbook",
        generation_version: str = "v4.0",
        created_at: Optional[float] = None,
        # Backward-compatible kwargs
        action: Optional[str] = None,
        justification: Optional[str] = None,
        candidate_type: Optional[str] = None,
        supporting_evidence: Optional[list[str]] = None,
        validated: Optional[bool] = None,
        **kwargs: Any
    ):
        self.id = id or f"REC-{int(time.time()*1000)%100000:05d}"
        self.title = title or (action or "Operational Intervention")
        self.action_type = candidate_type or action_type
        self.description = description or self.title
        self.rationale = rationale or (justification or "")
        self.hypothesis_ids = list(hypothesis_ids or [])
        self.evidence_ids = list(evidence_ids if evidence_ids is not None else (supporting_evidence or []))
        self.expected_benefit = expected_benefit
        self.expected_cost = expected_cost
        self.expected_risk_reduction = expected_risk_reduction
        self.implementation_risk = implementation_risk
        self.evidence_strength = evidence_strength
        self.authority_score = authority_score
        self.feasibility = feasibility
        self.time_to_impact = time_to_impact
        self.confidence = confidence
        self.responsible_stakeholder = responsible_stakeholder
        self.urgency = urgency
        self.approval_class = approval_class
        self.constraints = list(constraints or [])
        self.tradeoffs = tradeoffs
        self.risks = risks
        self.uncertainty = uncertainty
        self.precedent_outcome = precedent_outcome
        self.expected_impact = expected_impact
        self.score_breakdown = score_breakdown or {}
        if validated is not None:
            self.validation_status = "VALID" if validated else "REJECTED"
        else:
            self.validation_status = validation_status
        self.validation_reasons = list(validation_reasons or [])
        self.utility_score = utility_score
        self.confidence_adjusted_score = confidence_adjusted_score
        self.rank = rank
        self.is_dominated = is_dominated
        self.generated_by = generated_by
        self.generation_version = generation_version
        self.created_at = created_at or time.time()

    # ------------------------------------------------------------------------
    # Backward Compatibility Aliases
    # ------------------------------------------------------------------------
    @property
    def action(self) -> str:
        return self.title

    @action.setter
    def action(self, val: str):
        self.title = val

    @property
    def justification(self) -> str:
        return self.rationale

    @justification.setter
    def justification(self, val: str):
        self.rationale = val

    @property
    def candidate_type(self) -> str:
        return self.action_type

    @candidate_type.setter
    def candidate_type(self, val: str):
        self.action_type = val

    @property
    def supporting_evidence(self) -> list[str]:
        return self.evidence_ids

    @supporting_evidence.setter
    def supporting_evidence(self, val: list[str]):
        self.evidence_ids = val

    @property
    def validated(self) -> bool:
        return self.validation_status == "VALID"

    @validated.setter
    def validated(self, val: bool):
        if val:
            self.validation_status = "VALID"
        elif self.validation_status == "VALID":
            self.validation_status = "REJECTED"

    def to_dict(self) -> dict[str, Any]:
        """Serializes candidate into full auditable dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "action": self.title,
            "action_type": self.action_type,
            "candidate_type": self.action_type,
            "description": self.description,
            "rationale": self.rationale,
            "justification": self.rationale,
            "hypothesis_ids": list(self.hypothesis_ids),
            "evidence_ids": list(self.evidence_ids),
            "supporting_evidence": list(self.evidence_ids),
            "responsible_stakeholder": self.responsible_stakeholder,
            "urgency": self.urgency,
            "approval_class": self.approval_class,
            "expected_benefit": round(self.expected_benefit, 3),
            "expected_cost": round(self.expected_cost, 3),
            "cost_score": round(max(0.0, 1.0 - self.expected_cost), 3),
            "expected_risk_reduction": round(self.expected_risk_reduction, 3),
            "implementation_risk": round(self.implementation_risk, 3),
            "risk_score": round(self.expected_risk_reduction * (1.0 - self.implementation_risk), 3),
            "evidence_strength": round(self.evidence_strength, 3),
            "authority_score": round(self.authority_score, 3),
            "feasibility": round(self.feasibility, 3) if self.feasibility is not None else None,
            "time_to_impact": self.time_to_impact,
            "confidence": round(self.confidence, 3),
            "constraints": list(self.constraints),
            "tradeoffs": self.tradeoffs,
            "risks": self.risks,
            "uncertainty": self.uncertainty,
            "precedent_outcome": self.precedent_outcome,
            "expected_impact": self.expected_impact,
            "score_breakdown": self.score_breakdown,
            "validation_status": self.validation_status,
            "validation_reasons": list(self.validation_reasons),
            "validated": self.validated,
            "utility_score": round(self.utility_score, 3),
            "confidence_adjusted_score": round(self.confidence_adjusted_score, 3),
            "rank": self.rank,
            "is_dominated": self.is_dominated,
            "generated_by": self.generated_by,
            "generation_version": self.generation_version,
            "created_at": self.created_at,
        }
