"""Ranking Policy definition with explicit, versioned multi-criteria weights and hard constraint gates."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any


@dataclass
class RankingPolicy:
    """Explicit, versioned weighting and constraint policy for candidate ranking."""
    policy_name: str = "standard"
    policy_version: str = "v4.0"

    # Multi-Criteria Weights (Must sum to 1.0)
    w_benefit: float = 0.25
    w_cost: float = 0.15
    w_risk: float = 0.25
    w_evidence: float = 0.20
    w_authority: float = 0.15

    # Hard Constraint Thresholds (Gates applied before/during ranking)
    min_evidence_strength: float = 0.20
    max_implementation_risk: float = 0.70
    min_authority_score: float = 0.30
    min_utility_score: float = 0.20

    def __post_init__(self):
        total = self.w_benefit + self.w_cost + self.w_risk + self.w_evidence + self.w_authority
        if abs(total - 1.0) > 1e-4:
            # Normalize to 1.0
            self.w_benefit /= total
            self.w_cost /= total
            self.w_risk /= total
            self.w_evidence /= total
            self.w_authority /= total

    @classmethod
    def get_policy(cls, action_class: str = "standard") -> "RankingPolicy":
        """Factory for action-class-specific ranking policies."""
        ac = action_class.lower()
        if ac in ["early_warning", "data_quality"]:
            return cls(
                policy_name="early_warning",
                policy_version="v4.0",
                w_benefit=0.15,
                w_cost=0.25,
                w_risk=0.15,
                w_evidence=0.30,
                w_authority=0.15,
                min_evidence_strength=0.15,
                max_implementation_risk=0.50,
            )
        elif ac in ["escalation", "statutory"]:
            return cls(
                policy_name="escalation",
                policy_version="v4.0",
                w_benefit=0.15,
                w_cost=0.10,
                w_risk=0.30,
                w_evidence=0.20,
                w_authority=0.25,
                min_evidence_strength=0.30,
                max_implementation_risk=0.65,
                min_authority_score=0.45,
            )
        elif ac in ["financial", "billing"]:
            return cls(
                policy_name="financial",
                policy_version="v4.0",
                w_benefit=0.30,
                w_cost=0.25,
                w_risk=0.15,
                w_evidence=0.20,
                w_authority=0.10,
            )
        return cls()

    def to_dict(self) -> dict[str, Any]:
        return {
            "policy_name": self.policy_name,
            "policy_version": self.policy_version,
            "weights": {
                "benefit": round(self.w_benefit, 3),
                "cost": round(self.w_cost, 3),
                "risk": round(self.w_risk, 3),
                "evidence": round(self.w_evidence, 3),
                "authority": round(self.w_authority, 3),
            },
            "constraints": {
                "min_evidence_strength": self.min_evidence_strength,
                "max_implementation_risk": self.max_implementation_risk,
                "min_authority_score": self.min_authority_score,
                "min_utility_score": self.min_utility_score,
            },
        }
