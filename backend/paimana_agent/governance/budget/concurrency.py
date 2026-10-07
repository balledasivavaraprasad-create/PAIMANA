"""Investigation Priority and Concurrency Definitions."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class InvestigationPriority:
    """Multi-factor priority classification for portfolio-wide resource scheduling."""
    severity: str = "MEDIUM"
    project_impact: float = 0.50          # Cost scale / critical economic corridor weight
    urgency: str = "MEDIUM"               # LOW, MEDIUM, HIGH, CRITICAL
    evidence_criticality: float = 0.50    # Whether critical contractual deadlines loom

    @property
    def priority_score(self) -> float:
        """Calculates normalized composite priority score [0.0, 1.0]."""
        sev_weights = {"CRITICAL": 1.0, "HIGH": 0.75, "MEDIUM": 0.50, "LOW": 0.25}
        urg_weights = {"CRITICAL": 1.0, "HIGH": 0.80, "MEDIUM": 0.50, "LOW": 0.20}

        s_w = sev_weights.get(self.severity.upper(), 0.50)
        u_w = urg_weights.get(self.urgency.upper(), 0.50)

        score = (
            0.40 * s_w +
            0.30 * u_w +
            0.15 * min(1.0, max(0.0, self.project_impact)) +
            0.15 * min(1.0, max(0.0, self.evidence_criticality))
        )
        return round(score, 3)

    def to_dict(self) -> dict[str, Any]:
        return {
            "severity": self.severity,
            "project_impact": self.project_impact,
            "urgency": self.urgency,
            "evidence_criticality": self.evidence_criticality,
            "priority_score": self.priority_score,
        }
