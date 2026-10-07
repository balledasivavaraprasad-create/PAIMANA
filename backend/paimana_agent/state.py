"""Investigation State, Structured Evidence Model, and Hypothesis Tracking.

Defines the state structures maintained throughout an agentic investigation:
  - Fact: Ground-truth metrics from CUF submissions.
  - Inference: Derived analytical signals.
  - Hypothesis: Competing causal explanations with supporting & contradicting evidence links.
  - Contradiction: Explicit conflict between metrics, tools, or observations.
  - RecommendationCandidate: Structured candidate actions evaluated by the validation layer.
  - InvestigationState: Complete accumulator state used across the supervisor reasoning loop.
"""
from __future__ import annotations
import time
import math
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class Fact:
    """Ground-truth observed data directly from validated project records."""
    statement: str
    source: str
    metric: str
    value: Any
    verified: bool = True
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "statement": self.statement,
            "source": self.source,
            "metric": self.metric,
            "value": self.value,
            "verified": self.verified,
            "timestamp": self.timestamp,
        }


@dataclass
class Inference:
    """Analytical deduction derived from one or more observed facts."""
    statement: str
    derived_from: list[str]
    analytical_significance: str
    confidence_weight: float = 1.0
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "statement": self.statement,
            "derived_from": self.derived_from,
            "analytical_significance": self.analytical_significance,
            "confidence_weight": self.confidence_weight,
            "timestamp": self.timestamp,
        }


@dataclass
class ToolExecutionRecord:
    """Rich audit record for an individual tool invocation, supporting multiple parameterized runs."""
    call_id: str
    tool_name: str
    parameters: dict
    result_summary: str
    result_data: Any
    status: str = "success"  # success, error, partial
    latency_ms: float = 0.0
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "call_id": self.call_id,
            "tool_name": self.tool_name,
            "parameters": self.parameters,
            "result_summary": self.result_summary,
            "status": self.status,
            "latency_ms": self.latency_ms,
            "timestamp": self.timestamp,
        }


from .evidence.model import Evidence, EvidenceGroup, SourceLineage, ConfidenceUpdate
from .hypotheses.model import Hypothesis
from .recommendations.candidate import RecommendationCandidate
from .recommendations.selector import RecommendationDecision
from .investigation.evidence_need import EvidenceNeed
from .investigation.candidate import ToolCandidate, ToolSelectionRecord
from .investigation.budget import InvestigationBudget, InvestigationPhase


@dataclass
class Contradiction:
    """Explicitly recorded conflict between observations, tools, or historical memory."""
    metric_or_claim: str
    source_a: str
    value_a: Any
    source_b: str
    value_b: Any
    impact_on_hypotheses: str
    resolution_strategy: str = "investigate_further"
    resolved: bool = False
    severity: str = "MEDIUM"  # LOW, MEDIUM, HIGH, CRITICAL
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "metric_or_claim": self.metric_or_claim,
            "source_a": self.source_a,
            "value_a": self.value_a,
            "source_b": self.source_b,
            "value_b": self.value_b,
            "impact_on_hypotheses": self.impact_on_hypotheses,
            "resolution_strategy": self.resolution_strategy,
            "resolved": self.resolved,
            "severity": self.severity,
            "timestamp": self.timestamp,
        }


@dataclass
class InvestigationState:
    """Complete accumulator state maintained during an agentic investigation."""
    objective: str
    project_code: str
    project_name: str
    triggering_events: list[dict] = field(default_factory=list)
    
    # First-Class Evidence, Provenance Lineage & Independence Groups
    facts: list[Fact] = field(default_factory=list)
    inferences: list[Inference] = field(default_factory=list)
    evidence_items: list[Evidence] = field(default_factory=list)
    unexplained_evidence: list[Evidence] = field(default_factory=list)
    partially_explained_evidence: list[Evidence] = field(default_factory=list)
    contradicted_evidence: list[Evidence] = field(default_factory=list)
    evidence_groups: dict[str, EvidenceGroup] = field(default_factory=dict)
    source_lineage: dict[str, SourceLineage] = field(default_factory=dict)
    confidence_history: list[ConfidenceUpdate] = field(default_factory=list)
    hypotheses: list[Hypothesis] = field(default_factory=list)
    contradictions: list[Contradiction] = field(default_factory=list)
    evidence_gaps: list[str] = field(default_factory=list)
    evidence_graph: list[dict] = field(default_factory=list)  # (source, relation, target, weight)
    
    # Hypothesis Generation Audit Trail
    hypothesis_generation_events: list[dict] = field(default_factory=list)
    generated_hypothesis_count: int = 0
    rejected_hypothesis_count: int = 0
    investigation_outcome: str = "INSUFFICIENT_EVIDENCE"  # ROOT_CAUSE_SUPPORTED, ROOT_CAUSE_PARTIALLY_SUPPORTED, MULTIPLE_PLAUSIBLE_CAUSES, INSUFFICIENT_EVIDENCE, CONTRADICTORY_EVIDENCE

    # Tool Execution & Observations
    tools_used: list[str] = field(default_factory=list)
    tool_executions: list[ToolExecutionRecord] = field(default_factory=list)
    observations: dict[str, Any] = field(default_factory=dict)
    
    # Dynamic Reasoning Trace
    investigation_steps: list[dict] = field(default_factory=list)
    decision_trace: list[dict] = field(default_factory=list)
    
    # Grounded Multi-Dimensional Confidence (Separated Root Cause vs Recommendation)
    evidence_confidence: str = "LOW"  # HIGH, MEDIUM, LOW
    confidence_score: float = 0.2
    root_cause_confidence: float = 0.2
    recommendation_confidence: float = 0.2
    confidence_reasons: list[str] = field(default_factory=list)
    confidence_breakdown: dict[str, float] = field(default_factory=lambda: {
        "evidence_quality": 0.2,
        "evidence_independence": 0.2,
        "hypothesis_agreement": 0.2,
        "recency": 0.2,
        "contradiction_penalty": 0.0,
    })
    tool_budget: int = 5
    termination_reason: str = "IN_PROGRESS"
    
    # Dynamic Tool Selection & Uncertainty Acquisition State
    evidence_needs: list[EvidenceNeed] = field(default_factory=list)
    tool_candidates: list[ToolCandidate] = field(default_factory=list)
    tool_selection_history: list[ToolSelectionRecord] = field(default_factory=list)
    tool_results_quality: dict[str, float] = field(default_factory=dict)
    evidence_coverage: dict = field(default_factory=dict)
    investigation_budget: Optional[InvestigationBudget] = None
    investigation_phase: str = "ORIENTATION"

    # Recommendations
    candidate_recommendations: list[RecommendationCandidate] = field(default_factory=list)
    selected_recommendation: Optional[RecommendationCandidate] = None
    recommendation_alternatives: list[RecommendationCandidate] = field(default_factory=list)
    recommendation_decision: Optional[RecommendationDecision] = None

    # Institutional Memory & Precedent Learning
    retrieved_precedents: list[dict] = field(default_factory=list)
    retrieved_counterexamples: list[dict] = field(default_factory=list)
    retrieved_failures: list[dict] = field(default_factory=list)
    policy_constraints: list[str] = field(default_factory=list)
    memory_decision_trace: list[dict] = field(default_factory=list)
    precedent_bundle: Optional[dict] = None

    # Disciplined Causal Reasoning & Mechanism Verification
    causal_claims: list[dict] = field(default_factory=list)
    causal_mechanisms: list[dict] = field(default_factory=list)
    causal_graph: Optional[dict] = None
    confounders: list[dict] = field(default_factory=list)
    counterfactual_inquiries: list[dict] = field(default_factory=list)
    causal_decision_trace: Optional[dict] = None
    causal_conclusion_status: str = "INSUFFICIENT_CAUSAL_EVIDENCE"
    leading_causal_claim: Optional[dict] = None
    retained_causal_alternatives: list[dict] = field(default_factory=list)

    # Multidimensional Convergence & Termination Management
    convergence_state: Optional[Any] = None
    convergence_history: list[Any] = field(default_factory=list)
    termination_record: Optional[Any] = None
    reopen_triggers: list[Any] = field(default_factory=list)

    # Resource Governance & Budget Management
    budget_manager: Optional[Any] = None
    governance_trace: Optional[Any] = None
    degradation_level: str = "LEVEL_1_NORMAL"
    quality_tier: str = "TIER_1_FULL"

    # Phase 12 Governance & Human Approval Lockdown
    governance_approval_request: Optional[Any] = None
    governance_approval_record: Optional[Any] = None
    governance_execution_record: Optional[Any] = None
    governance_audit_trail: list[Any] = field(default_factory=list)

    @property
    def is_converged(self) -> bool:
        if self.convergence_state:
            return getattr(self.convergence_state, "is_converged", False)
        return self.termination_reason == "SUFFICIENT_EVIDENCE"

    @property
    def evidence(self) -> list[Evidence]:
        return self.evidence_items

    def add_fact(self, statement: str, source: str, metric: str, value: Any, verified: bool = True) -> Fact:
        f = Fact(statement=statement, source=source, metric=metric, value=value, verified=verified)
        self.facts.append(f)
        return f

    def add_evidence(self, ev: Evidence) -> Evidence:
        """Adds a first-class Evidence instance, updates lineage, and aggregates independence groups."""
        self.evidence_items.append(ev)
        
        # Track Source Lineage
        self.source_lineage[ev.id] = SourceLineage(
            evidence_id=ev.id,
            source_system=getattr(ev, "source_system", "PAIMANA"),
            source_record_id=getattr(ev, "source_record_id", None),
            source_field=getattr(ev, "source_field", None),
            parent_evidence_ids=list(getattr(ev, "parent_evidence_ids", [])),
            transformation_chain=list(getattr(ev, "transformation_chain", [])),
            lineage_quality=0.85 if getattr(ev, "parent_evidence_ids", []) else 1.0
        )

        # Track and Aggregate Independence Group
        gid = getattr(ev, "independence_group_id", getattr(ev, "independence_group", "default"))
        if gid not in self.evidence_groups:
            self.evidence_groups[gid] = EvidenceGroup(
                group_id=gid,
                source_system=getattr(ev, "source_system", "PAIMANA"),
                base_authority=getattr(ev, "authority_score", 0.8),
                group_freshness=getattr(ev, "freshness", 1.0)
            )

        grp = self.evidence_groups[gid]
        if getattr(ev, "evidence_type", "direct_observation") == "derived_metric":
            if ev.id not in grp.derived_evidence_ids:
                grp.derived_evidence_ids.append(ev.id)
        else:
            if ev.id not in grp.primary_evidence_ids:
                grp.primary_evidence_ids.append(ev.id)

        grp.base_authority = max(grp.base_authority, getattr(ev, "authority_score", 0.8))
        grp.group_freshness = min(grp.group_freshness, getattr(ev, "freshness", 1.0))
        grp.effective_group_weight = min(1.0, grp.base_authority + min(0.35, 0.10 * len(grp.derived_evidence_ids)))
        return ev

    def get_evidence_quality_dashboard(self) -> dict:
        """Assembles comprehensive evidence quality metrics via the canonical EvidenceConfidenceEngine."""
        from .evidence import EvidenceConfidenceEngine
        return EvidenceConfidenceEngine.build_dashboard(self)

    def add_inference(self, statement: str, derived_from: list[str], significance: str, weight: float = 1.0) -> Inference:
        inf = Inference(statement=statement, derived_from=derived_from, analytical_significance=significance, confidence_weight=weight)
        self.inferences.append(inf)
        return inf

    def add_contradiction(self, metric: str, src_a: str, val_a: Any, src_b: str, val_b: Any, impact: str, severity: str = "MEDIUM") -> Contradiction:
        c = Contradiction(metric_or_claim=metric, source_a=src_a, value_a=val_a, source_b=src_b, value_b=val_b, impact_on_hypotheses=impact, severity=severity)
        self.contradictions.append(c)
        return c

    def get_convergence_dashboard(self) -> dict:
        """Assembles executive convergence dashboard metrics."""
        from .investigation.convergence import TerminationTraceBuilder
        if self.convergence_state:
            best_cand = self.tool_candidates[0] if self.tool_candidates else None
            return TerminationTraceBuilder.build_convergence_dashboard(self.convergence_state, best_cand)
        return {
            "status": self.termination_reason or "IN_PROGRESS",
            "is_converged": self.is_converged,
            "evidence_coverage_pct": 50.0,
            "hypothesis_separation_pct": 20.0,
            "hypothesis_stability_pct": 50.0,
            "contradiction_resolution_pct": 100.0 if not self.contradictions else 50.0,
            "causal_support_pct": 30.0,
            "decision_readiness_pct": 40.0,
            "expected_information_gain": {"next_best_tool": "None", "expected_gain": 0.0, "threshold": 0.04},
            "explanation": "Convergence evaluation pending.",
            "unresolved_contradictions": len(self.contradictions),
        }

    def get_governance_dashboard(self) -> dict[str, Any]:
        """Returns the resource health, budget consumption, and governance status dashboard."""
        if self.budget_manager:
            return self.budget_manager.get_dashboard()
        if self.investigation_budget:
            from .governance.budget.governance_trace import GovernanceTraceBuilder
            return GovernanceTraceBuilder.build_dashboard(self.investigation_budget)
        return {
            "resource_pressure": 0.0,
            "resource_pressure_label": "NORMAL",
            "tool_calls_progress": "0 / 5",
            "cost_progress": "$0.00 / $1.50",
            "is_exhausted": False,
        }

    def add_evidence_relation(self, source: str, relation: str, target: str, weight: float = 1.0):
        """Builds relational evidence graph: (source, SUPPORTS|WEAKENS|FALSIFIES, target)."""
        rel = {
            "source": source,
            "relation": relation,
            "target": target,
            "weight": weight,
            "timestamp": time.time(),
        }
        self.evidence_graph.append(rel)

    def record_tool_execution(self, call_id: str, tool_name: str, parameters: dict,
                              summary: str, data: Any, status: str = "success", latency_ms: float = 0.0) -> ToolExecutionRecord:
        exec_status = "PARTIAL" if status == "PARTIAL_SUCCESS" else status
        rec = ToolExecutionRecord(
            call_id=call_id,
            tool_name=tool_name,
            parameters=parameters,
            result_summary=summary,
            result_data=data,
            status=exec_status,
            latency_ms=latency_ms,
        )
        self.tool_executions.append(rec)
        if tool_name not in self.tools_used:
            self.tools_used.append(tool_name)
        self.observations[tool_name] = data
        return rec

    def add_evidence_gap(self, gap_description: str):
        if gap_description not in self.evidence_gaps:
            self.evidence_gaps.append(gap_description)

    def resolve_evidence_gap(self, gap_description: str):
        if gap_description in self.evidence_gaps:
            self.evidence_gaps.remove(gap_description)

    def get_observation(self, tool_name: str) -> Optional[Any]:
        return self.observations.get(tool_name)

    def to_dict(self) -> dict:
        return {
            "objective": self.objective,
            "project_code": self.project_code,
            "project_name": self.project_name,
            "triggering_events": [e.get("type", str(e)) for e in self.triggering_events],
            "facts": [f.to_dict() for f in self.facts],
            "inferences": [i.to_dict() for i in self.inferences],
            "evidence": [e.to_dict() for e in self.evidence_items],
            "evidence_items": [e.to_dict() for e in self.evidence_items],
            "unexplained_evidence": [e.to_dict() for e in self.unexplained_evidence],
            "hypotheses": [h.to_dict() for h in self.hypotheses],
            "hypothesis_generation_events": self.hypothesis_generation_events,
            "generated_hypothesis_count": self.generated_hypothesis_count,
            "rejected_hypothesis_count": self.rejected_hypothesis_count,
            "investigation_outcome": self.investigation_outcome,
            "contradictions": [c.to_dict() for c in self.contradictions],
            "evidence_gaps": self.evidence_gaps,
            "evidence_graph": self.evidence_graph,
            "tools_used": self.tools_used,
            "tool_executions": [t.to_dict() for t in self.tool_executions],
            "confidence": self.evidence_confidence,
            "confidence_score": round(self.confidence_score, 3),
            "root_cause_confidence": round(self.root_cause_confidence, 3),
            "recommendation_confidence": round(self.recommendation_confidence, 3),
            "confidence_reasons": self.confidence_reasons,
            "confidence_breakdown": {k: round(v, 3) for k, v in self.confidence_breakdown.items()},
            "termination_reason": self.termination_reason,
            "steps_count": len(self.investigation_steps),
            "evidence_needs": [n.to_dict() for n in self.evidence_needs],
            "tool_candidates": [c.to_dict() for c in self.tool_candidates],
            "tool_selection_history": [s.to_dict() for s in self.tool_selection_history],
            "investigation_phase": self.investigation_phase,
            "investigation_budget": self.investigation_budget.to_dict() if self.investigation_budget else None,
            "candidate_recommendations": [c.to_dict() for c in self.candidate_recommendations],
            "selected_recommendation": self.selected_recommendation.to_dict() if self.selected_recommendation else None,
            "recommendation_alternatives": [c.to_dict() for c in self.recommendation_alternatives],
            "recommendation_decision": self.recommendation_decision.to_dict() if self.recommendation_decision else None,
            "retrieved_precedents": self.retrieved_precedents,
            "retrieved_counterexamples": self.retrieved_counterexamples,
            "retrieved_failures": self.retrieved_failures,
            "policy_constraints": self.policy_constraints,
            "memory_decision_trace": self.memory_decision_trace,
            "precedent_bundle": self.precedent_bundle,
            "causal_claims": self.causal_claims,
            "causal_mechanisms": self.causal_mechanisms,
            "causal_graph": self.causal_graph,
            "confounders": self.confounders,
            "counterfactual_inquiries": self.counterfactual_inquiries,
            "causal_decision_trace": self.causal_decision_trace,
            "causal_conclusion_status": self.causal_conclusion_status,
            "leading_causal_claim": self.leading_causal_claim,
            "retained_causal_alternatives": self.retained_causal_alternatives,
            "convergence_state": self.convergence_state.to_dict() if self.convergence_state else None,
            "termination_record": self.termination_record.to_dict() if self.termination_record else None,
            "degradation_level": self.degradation_level,
            "quality_tier": self.quality_tier,
            "governance_trace": self.governance_trace.to_dict() if hasattr(self.governance_trace, "to_dict") else self.governance_trace,
            "governance_dashboard": self.get_governance_dashboard(),
            "governance_approval_request": self.governance_approval_request.to_dict() if hasattr(self.governance_approval_request, "to_dict") else self.governance_approval_request,
            "governance_approval_record": self.governance_approval_record.to_dict() if hasattr(self.governance_approval_record, "to_dict") else self.governance_approval_record,
            "governance_execution_record": self.governance_execution_record.to_dict() if hasattr(self.governance_execution_record, "to_dict") else self.governance_execution_record,
            "governance_audit_trail": [a.to_dict() if hasattr(a, "to_dict") else a for a in self.governance_audit_trail],
        }
