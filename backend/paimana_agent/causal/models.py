"""First-Class Causal Reasoning Data Models.

Defines the formal structures for moving from correlation to disciplined causal testing:
- CausalClaimLevel: Explicit levels from Observation (0) to Intervention-Supported (5).
- CausalClaim: Comprehensive causal hypothesis tracking temporal, mechanistic, and alternative support.
- CausalMechanism: Multi-step intermediate transmission chains and falsification criteria.
- TemporalRelation: Temporal consistency and precedence validation.
- Confounder: Common cause tracking and confounding penalty.
- CounterfactualProxy: Natural comparison groups and counterfactual approximations.
- CausalGraph: Explicit project-specific causal network with actionable nodes.
"""
from __future__ import annotations
import time
from dataclasses import dataclass, field
from typing import Any, Literal, Optional

CausalClaimLevel = Literal[
    "LEVEL_0_OBSERVATION",            # Directly observed metric
    "LEVEL_1_ASSOCIATION",            # Co-movement / correlation without causal claim
    "LEVEL_2_TEMPORAL_ASSOCIATION",   # Precedence established (cause occurred before effect)
    "LEVEL_3_MECHANISTIC_SUPPORT",    # Plausible domain mechanism links cause to effect
    "LEVEL_4_STRONG_CAUSAL_SUPPORT",   # Multi-source independent evidence + alternatives disfavored
    "LEVEL_5_INTERVENTION_SUPPORTED"  # Targeted intervention shifted cause and effect followed
]

CausalClaimStatus = Literal[
    "CANDIDATE",
    "PLAUSIBLE",
    "SUPPORTED",
    "WEAKENED",
    "REJECTED",
    "UNRESOLVED"
]

CausalEvidenceType = Literal[
    "OBSERVATION",
    "TEMPORAL",
    "MECHANISTIC",
    "COMPARATIVE",
    "INTERVENTIONAL",
    "COUNTERFACTUAL_PROXY",
    "EXPERT_ASSESSMENT",
    "MODEL_DERIVED",           # E.g. SHAP - explains model prediction, NOT ground-truth causality
    "HISTORICAL_PRECEDENT"
]

CausalConclusionStatus = Literal[
    "PRIMARY_CAUSAL_EXPLANATION",
    "ALTERNATIVE_CAUSAL_EXPLANATION",
    "UNRESOLVED_CAUSAL_CONFLICT",
    "INSUFFICIENT_CAUSAL_EVIDENCE"
]


@dataclass
class TemporalRelation:
    """Explicit temporal ordering between candidate cause, intermediate nodes, and effect."""
    cause_event: str
    intermediate_events: list[str] = field(default_factory=list)
    effect_event: str = ""
    cause_timestamp: Optional[float] = None
    effect_timestamp: Optional[float] = None
    lag_days: float = 0.0
    temporal_consistency: bool = True     # True iff cause preceded effect with plausible lag
    inconsistency_reason: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "cause_event": self.cause_event,
            "intermediate_events": list(self.intermediate_events),
            "effect_event": self.effect_event,
            "cause_timestamp": self.cause_timestamp,
            "effect_timestamp": self.effect_timestamp,
            "lag_days": round(self.lag_days, 1),
            "temporal_consistency": self.temporal_consistency,
            "inconsistency_reason": self.inconsistency_reason,
        }


@dataclass
class Confounder:
    """Common cause variable that simultaneously influences candidate cause and effect."""
    id: str
    variable: str
    affects_cause: bool = True
    affects_effect: bool = True
    evidence_ids: list[str] = field(default_factory=list)
    confidence: float = 0.50
    description: str = ""
    resolved: bool = False
    resolution_evidence_needed: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "variable": self.variable,
            "affects_cause": self.affects_cause,
            "affects_effect": self.affects_effect,
            "evidence_ids": list(self.evidence_ids),
            "confidence": round(self.confidence, 3),
            "description": self.description,
            "resolved": self.resolved,
            "resolution_evidence_needed": self.resolution_evidence_needed,
        }


@dataclass
class CounterfactualProxy:
    """Comparison group or baseline approximating what would happen in the absence of cause."""
    question: str
    proxy_type: str  # "unaffected_workfront", "same_contractor_elsewhere", "pre_issue_baseline", "comparable_peer"
    expected_outcome_without_cause: str
    observed_proxy_outcome: str
    supports_causality: bool
    notes: str = ""

    def to_dict(self) -> dict:
        return {
            "question": self.question,
            "proxy_type": self.proxy_type,
            "expected_outcome_without_cause": self.expected_outcome_without_cause,
            "observed_proxy_outcome": self.observed_proxy_outcome,
            "supports_causality": self.supports_causality,
            "notes": self.notes,
        }


@dataclass
class CausalMechanism:
    """Multi-step intermediate chain explaining how a root cause transmits to the observed outcome."""
    id: str
    name: str
    cause: str
    intermediate_variables: list[str]
    effect: str
    predicted_observations: list[str] = field(default_factory=list)
    falsifying_observations: list[str] = field(default_factory=list)
    actionable_node: str = ""
    actionable_stakeholder: str = "Executing Agency"
    links_verified: dict[str, bool] = field(default_factory=dict)
    is_validated: bool = False

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "cause": self.cause,
            "intermediate_variables": list(self.intermediate_variables),
            "effect": self.effect,
            "predicted_observations": list(self.predicted_observations),
            "falsifying_observations": list(self.falsifying_observations),
            "actionable_node": self.actionable_node,
            "actionable_stakeholder": self.actionable_stakeholder,
            "links_verified": dict(self.links_verified),
            "is_validated": self.is_validated,
        }


@dataclass
class CausalClaim:
    """A formal causal hypothesis with multi-dimensional support and explicit claim levels."""
    id: str
    effect: str
    proposed_cause: str
    mechanism_id: Optional[str] = None
    mechanism: Optional[CausalMechanism] = None

    # Evidentiary Tracking
    evidence_for_ids: list[str] = field(default_factory=list)
    evidence_against_ids: list[str] = field(default_factory=list)

    # Component Scores [0.0, 1.0]
    temporal_support: float = 0.50
    mechanistic_support: float = 0.50
    independent_evidence_score: float = 0.50
    alternative_cause_penalty: float = 0.0
    confounder_penalty: float = 0.0
    contradiction_penalty: float = 0.0

    # Composite Causal Support & Level
    causal_support_score: float = 0.50
    causal_level: CausalClaimLevel = "LEVEL_1_ASSOCIATION"
    causal_support_bracket: str = "MODERATE"  # STRONG, MODERATE, LOW, INSUFFICIENT
    status: CausalClaimStatus = "CANDIDATE"

    # Context & Alternatives
    unresolved_confounders: list[str] = field(default_factory=list)
    falsification_notes: list[str] = field(default_factory=list)
    actionable_intervention: Optional[str] = None
    responsible_authority: Optional[str] = None
    counterfactual_notes: list[str] = field(default_factory=list)
    hypothesis_id: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "hypothesis_id": self.hypothesis_id,
            "effect": self.effect,
            "proposed_cause": self.proposed_cause,
            "mechanism_id": self.mechanism_id,
            "mechanism": self.mechanism.to_dict() if self.mechanism else None,
            "evidence_for_ids": list(self.evidence_for_ids),
            "evidence_against_ids": list(self.evidence_against_ids),
            "temporal_support": round(self.temporal_support, 3),
            "mechanistic_support": round(self.mechanistic_support, 3),
            "independent_evidence_score": round(self.independent_evidence_score, 3),
            "alternative_cause_penalty": round(self.alternative_cause_penalty, 3),
            "confounder_penalty": round(self.confounder_penalty, 3),
            "contradiction_penalty": round(self.contradiction_penalty, 3),
            "causal_support_score": round(self.causal_support_score, 3),
            "causal_level": self.causal_level,
            "causal_support_bracket": self.causal_support_bracket,
            "status": self.status,
            "unresolved_confounders": list(self.unresolved_confounders),
            "falsification_notes": list(self.falsification_notes),
            "actionable_intervention": self.actionable_intervention,
            "responsible_authority": self.responsible_authority,
            "counterfactual_notes": list(self.counterfactual_notes),
        }


@dataclass
class CausalGraphNode:
    """A variable node in the project causal graph."""
    name: str
    variable_type: str  # "cause", "intermediate", "effect", "confounder"
    observed_value: Any = None
    evidence_ids: list[str] = field(default_factory=list)
    is_actionable: bool = False
    action_description: str = ""

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "variable_type": self.variable_type,
            "observed_value": self.observed_value,
            "evidence_ids": list(self.evidence_ids),
            "is_actionable": self.is_actionable,
            "action_description": self.action_description,
        }


@dataclass
class CausalGraphEdge:
    """A directed causal connection between variables."""
    source: str
    target: str
    mechanism: str = ""
    weight: float = 0.50
    is_verified: bool = False
    evidence_ids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "target": self.target,
            "mechanism": self.mechanism,
            "weight": round(self.weight, 3),
            "is_verified": self.is_verified,
            "evidence_ids": list(self.evidence_ids),
        }


@dataclass
class CausalGraph:
    """Project-specific directed causal network."""
    project_code: str
    nodes: dict[str, CausalGraphNode] = field(default_factory=dict)
    edges: list[CausalGraphEdge] = field(default_factory=list)
    cycles_detected: bool = False
    is_valid: bool = True

    def add_node(self, node: CausalGraphNode) -> None:
        self.nodes[node.name] = node

    def add_edge(self, edge: CausalGraphEdge) -> None:
        self.edges.append(edge)

    def to_dict(self) -> dict:
        return {
            "project_code": self.project_code,
            "nodes": {k: v.to_dict() for k, v in self.nodes.items()},
            "edges": [e.to_dict() for e in self.edges],
            "cycles_detected": self.cycles_detected,
            "is_valid": self.is_valid,
        }
