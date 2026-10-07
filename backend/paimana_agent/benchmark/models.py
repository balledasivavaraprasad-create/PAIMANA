"""Data models for Phase 14 — Agent Quality Benchmark.

Defines benchmark case specifications, ground-truth targets, dimensional evaluation
results, and the aggregate Agent Benchmark Report.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Any, Optional, Set


class BenchmarkDimension(str, Enum):
    """The 10 canonical quality dimensions for agent evaluation."""
    HYPOTHESIS_QUALITY = "hypothesis_quality"
    CAUSAL_REASONING = "causal_reasoning"
    TOOL_SELECTION = "tool_selection"
    CONVERGENCE = "convergence"
    RECOMMENDATION_QUALITY = "recommendation_quality"
    PEER_INTELLIGENCE = "peer_intelligence"
    MEMORY_USEFULNESS = "memory_usefulness"
    FALSE_ESCALATION = "false_escalation"
    UNSUPPORTED_CLAIMS = "unsupported_claims"
    RESOURCE_EFFICIENCY = "resource_efficiency"


@dataclass
class BenchmarkCase:
    """Specification of a known ground-truth benchmark scenario."""
    case_id: str
    title: str
    description: str
    project_data: Dict[str, Any]
    event_type: str
    report_month: str = "2026-03"

    # Ground Truth Targets
    ground_truth_root_cause: str = ""
    ground_truth_causal_level: int = 3
    has_confounders: bool = False
    expected_confounders: List[str] = field(default_factory=list)
    punitive_action_warranted: bool = False
    is_benign_artifact: bool = False
    relevant_tools: List[str] = field(default_factory=list)
    prohibited_actions: List[str] = field(default_factory=list)  # Historically failed actions
    expected_recommendation_type: str = ""
    peer_cohort_filters: Dict[str, Any] = field(default_factory=dict)
    max_budget_steps: int = 6

    def to_dict(self) -> Dict[str, Any]:
        return {
            "case_id": self.case_id,
            "title": self.title,
            "description": self.description,
            "event_type": self.event_type,
            "ground_truth_root_cause": self.ground_truth_root_cause,
            "ground_truth_causal_level": self.ground_truth_causal_level,
            "has_confounders": self.has_confounders,
            "punitive_action_warranted": self.punitive_action_warranted,
            "is_benign_artifact": self.is_benign_artifact,
            "relevant_tools": self.relevant_tools,
            "prohibited_actions": self.prohibited_actions,
            "expected_recommendation_type": self.expected_recommendation_type,
        }


@dataclass
class DimensionScore:
    """Quantitative evaluation for a single quality dimension."""
    dimension: BenchmarkDimension
    score: float  # [0.0, 1.0] (1.0 = optimal)
    passed: bool
    details: Dict[str, Any] = field(default_factory=dict)
    narrative: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "dimension": self.dimension.value,
            "score": round(self.score, 4),
            "passed": self.passed,
            "details": self.details,
            "narrative": self.narrative,
        }


@dataclass
class CaseEvaluationResult:
    """Evaluation result of an agent on a single benchmark case."""
    case_id: str
    agent_type: str  # "V3_AUTONOMOUS" or "BASELINE_HEURISTIC"
    dimension_scores: Dict[BenchmarkDimension, DimensionScore] = field(default_factory=dict)
    tools_used: List[str] = field(default_factory=list)
    steps_executed: int = 0
    top_hypothesis: str = ""
    causal_level: int = 0
    confounders_detected: List[str] = field(default_factory=list)
    recommended_action: str = ""
    is_escalated: bool = False
    has_unsupported_claim: bool = False
    execution_time_sec: float = 0.0

    @property
    def composite_case_score(self) -> float:
        if not self.dimension_scores:
            return 0.0
        return sum(d.score for d in self.dimension_scores.values()) / len(self.dimension_scores)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "case_id": self.case_id,
            "agent_type": self.agent_type,
            "composite_case_score": round(self.composite_case_score, 4),
            "tools_used": self.tools_used,
            "steps_executed": self.steps_executed,
            "top_hypothesis": self.top_hypothesis,
            "causal_level": self.causal_level,
            "confounders_detected": self.confounders_detected,
            "recommended_action": self.recommended_action,
            "is_escalated": self.is_escalated,
            "has_unsupported_claim": self.has_unsupported_claim,
            "scores": {d.value: s.to_dict() for d, s in self.dimension_scores.items()},
        }


@dataclass
class AgentBenchmarkReport:
    """Aggregate benchmark report comparing V3+ Autonomous Agent vs Baseline."""
    timestamp: float
    total_cases: int
    v3_case_results: List[CaseEvaluationResult]
    baseline_case_results: List[CaseEvaluationResult]

    # Aggregate Dimension Scores [0.0, 1.0]
    v3_dimension_scores: Dict[BenchmarkDimension, float] = field(default_factory=dict)
    baseline_dimension_scores: Dict[BenchmarkDimension, float] = field(default_factory=dict)
    dimension_deltas: Dict[BenchmarkDimension, float] = field(default_factory=dict)

    # High-Level Metrics
    v3_aqi: float = 0.0          # Agent Quality Index [0, 100]
    baseline_aqi: float = 0.0    # Baseline Quality Index [0, 100]
    net_improvement: float = 0.0 # Delta AQI
    verdict: str = "PENDING"
    executive_summary: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "total_cases": self.total_cases,
            "v3_aqi": round(self.v3_aqi, 2),
            "baseline_aqi": round(self.baseline_aqi, 2),
            "net_improvement": round(self.net_improvement, 2),
            "verdict": self.verdict,
            "executive_summary": self.executive_summary,
            "dimensions": {
                d.value: {
                    "v3_score": round(self.v3_dimension_scores.get(d, 0.0), 3),
                    "baseline_score": round(self.baseline_dimension_scores.get(d, 0.0), 3),
                    "delta": round(self.dimension_deltas.get(d, 0.0), 3),
                }
                for d in BenchmarkDimension
            },
            "cases_evaluated": [c.to_dict() for c in self.v3_case_results],
        }
