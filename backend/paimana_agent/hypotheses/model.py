"""First-class Hypothesis Data Model for PAIMANA Agentic Layer.

Supports full lifecycle tracking: seeded vs agent-generated, candidate vs supported vs rejected,
explanatory mechanisms, predicted observations, discriminating evidence, parent-child branching,
and auditable rejection reasons.
"""
from __future__ import annotations
import time
from dataclasses import dataclass, field
from typing import Literal, Optional


HypothesisSource = Literal["seeded", "agent_generated", "human_added"]
HypothesisStatus = Literal["candidate", "active", "supported", "weakened", "rejected", "unresolved", "PRIMARY", "COMPETING"]


@dataclass
class Hypothesis:
    """Causal hypothesis entity with full evidentiary provenance and lifecycle tracking."""
    id: str
    statement: str
    source: HypothesisSource = "seeded"
    status: HypothesisStatus = "active"
    support_evidence_ids: list[str] = field(default_factory=list)
    contradiction_evidence_ids: list[str] = field(default_factory=list)
    predicted_observations: list[str] = field(default_factory=list)
    discriminating_evidence: list[str] = field(default_factory=list)
    supporting_score: float = 0.0
    contradicting_score: float = 0.0
    confidence: float = 0.5
    parent_hypothesis_id: Optional[str] = None
    created_at_iteration: int = 0
    last_updated_iteration: int = 0
    rejection_reason: Optional[str] = None
    mechanism: str = ""
    falsification_condition: str = ""

    # Legacy compatibility fields
    prior_prob: float = 0.25
    posterior_prob: float = 0.25
    net_score: float = 0.0

    def __init__(
        self,
        id: Optional[str] = None,
        statement: Optional[str] = None,
        name: Optional[str] = None,
        hypothesis: Optional[str] = None,
        source: HypothesisSource = "seeded",
        status: HypothesisStatus = "active",
        support_evidence_ids: Optional[list[str]] = None,
        contradiction_evidence_ids: Optional[list[str]] = None,
        supporting_evidence_ids: Optional[list[str]] = None,
        contradicting_evidence_ids: Optional[list[str]] = None,
        predicted_observations: Optional[list[str]] = None,
        discriminating_evidence: Optional[list[str]] = None,
        supporting_score: float = 0.0,
        contradicting_score: float = 0.0,
        confidence: Any = 0.5,
        parent_hypothesis_id: Optional[str] = None,
        created_at_iteration: int = 0,
        last_updated_iteration: int = 0,
        rejection_reason: Optional[str] = None,
        mechanism: str = "",
        falsification_condition: str = "",
        prior_prob: float = 0.25,
        posterior_prob: float = 0.25,
        net_score: float = 0.0,
    ):
        self.id = id or name or f"H_{int(time.time()*1000)%10000}"
        self.statement = statement or hypothesis or ""
        self.source = source
        self.status = status
        self.support_evidence_ids = support_evidence_ids or supporting_evidence_ids or []
        self.contradiction_evidence_ids = contradiction_evidence_ids or contradicting_evidence_ids or []
        self.predicted_observations = predicted_observations or []
        self.discriminating_evidence = discriminating_evidence or []
        self.supporting_score = supporting_score
        self.contradicting_score = contradicting_score
        
        # Normalize confidence if string ("HIGH", "MEDIUM", "LOW")
        if isinstance(confidence, str):
            c_map = {"HIGH": 0.85, "MEDIUM": 0.55, "LOW": 0.25}
            self.confidence = c_map.get(confidence.upper(), 0.5)
        else:
            self.confidence = float(confidence)

        self.parent_hypothesis_id = parent_hypothesis_id
        self.created_at_iteration = created_at_iteration
        self.last_updated_iteration = last_updated_iteration
        self.rejection_reason = rejection_reason
        self.mechanism = mechanism
        self.falsification_condition = falsification_condition
        self.prior_prob = prior_prob
        self.posterior_prob = posterior_prob
        self.net_score = net_score

    # Backward compatibility properties
    @property
    def name(self) -> str:
        return self.id

    @name.setter
    def name(self, val: str):
        self.id = val

    @property
    def hypothesis(self) -> str:
        return self.statement

    @hypothesis.setter
    def hypothesis(self, val: str):
        self.statement = val

    @property
    def supporting_evidence_ids(self) -> list[str]:
        return self.support_evidence_ids

    @supporting_evidence_ids.setter
    def supporting_evidence_ids(self, val: list[str]):
        self.support_evidence_ids = val

    @property
    def contradicting_evidence_ids(self) -> list[str]:
        return self.contradiction_evidence_ids

    @contradicting_evidence_ids.setter
    def contradicting_evidence_ids(self, val: list[str]):
        self.contradiction_evidence_ids = val

    def to_dict(self) -> dict:
        if isinstance(self.confidence, str):
            conf_str = self.confidence
            conf_num = 0.85 if self.confidence.upper() == "HIGH" else (0.50 if self.confidence.upper() == "MEDIUM" else 0.20)
        else:
            conf_num = float(self.confidence)
            conf_str = "HIGH" if conf_num >= 0.70 else ("MEDIUM" if conf_num >= 0.40 else "LOW")

        return {
            "id": self.id,
            "name": self.id,
            "statement": self.statement,
            "hypothesis": self.statement,
            "source": self.source,
            "status": self.status,
            "confidence": conf_str,
            "confidence_score": round(conf_num, 3),
            "prior_prob": round(self.prior_prob, 3),
            "posterior_prob": round(self.posterior_prob, 3),
            "supporting_score": round(self.supporting_score, 3),
            "contradicting_score": round(self.contradicting_score, 3),
            "net_score": round(self.net_score, 2),
            "support_evidence_ids": list(self.support_evidence_ids),
            "supporting_evidence_ids": list(self.support_evidence_ids),
            "contradiction_evidence_ids": list(self.contradiction_evidence_ids),
            "contradicting_evidence_ids": list(self.contradiction_evidence_ids),
            "supporting_inferences": list(self.support_evidence_ids),
            "predicted_observations": list(self.predicted_observations),
            "discriminating_evidence": list(self.discriminating_evidence),
            "falsification_condition": self.falsification_condition,
            "parent_hypothesis_id": self.parent_hypothesis_id,
            "created_at_iteration": self.created_at_iteration,
            "last_updated_iteration": self.last_updated_iteration,
            "rejection_reason": self.rejection_reason,
            "mechanism": self.mechanism,
        }
