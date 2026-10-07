"""Tool Registry & Specialist Investigation Capabilities.

Provides a formal, decoupled tool registry where every investigation capability is defined with:
  - name & purpose
  - input/output schemas
  - authorization level
  - failure & retry policy
  - structured evidence generation
  - MCP (Model Context Protocol) manifest export compatibility
"""
from __future__ import annotations
import math
import time
import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from pathlib import Path
import sys

# Ensure Peer_Intelligence is discoverable
_current_file = Path(__file__).resolve()
_paimana_agent_v3_dir = _current_file.parent.parent.parent
_peer_intel_dir = _paimana_agent_v3_dir / "Peer_Intelligence"
if _peer_intel_dir.exists() and str(_peer_intel_dir) not in sys.path:
    sys.path.insert(0, str(_peer_intel_dir))

from .store import Store
from .shap_explain import shap_summary_lines, shap_top_features
from .memory import PrecedentMemoryStore, MemoryRetriever, PolicyMemoryStore

logger = logging.getLogger("paimana_agent.tools")

_default_precedent_store = PrecedentMemoryStore()
_default_policy_store = PolicyMemoryStore()


from .reliability.models import ToolResult, ToolResultStatus


@dataclass
class ToolDescriptor:
    """Rich metadata describing specialist tool capabilities and operational profile."""
    name: str
    purpose: str
    capabilities: list[str] = field(default_factory=list)
    evidence_types_generated: list[str] = field(default_factory=list)
    hypothesis_domains: list[str] = field(default_factory=list)
    source_authority: float = 0.80
    typical_latency_ms: float = 20.0
    execution_cost: float = 0.10
    freshness_half_life_days: float = 30.0
    discrimination_targets: list[tuple[str, str]] = field(default_factory=list)
    prerequisites: list[str] = field(default_factory=list)
    authorization_required: str = "read_only"
    historical_reliability: float = 0.98
    source_system: str = "PAIMANA"

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "purpose": self.purpose,
            "capabilities": list(self.capabilities),
            "evidence_types_generated": list(self.evidence_types_generated),
            "hypothesis_domains": list(self.hypothesis_domains),
            "source_authority": self.source_authority,
            "typical_latency_ms": self.typical_latency_ms,
            "execution_cost": self.execution_cost,
            "freshness_half_life_days": self.freshness_half_life_days,
            "discrimination_targets": [list(t) for t in self.discrimination_targets],
            "prerequisites": list(self.prerequisites),
            "authorization_required": self.authorization_required,
            "historical_reliability": self.historical_reliability,
            "source_system": self.source_system,
        }


@dataclass
class ToolDefinition:
    """Standardized tool specification compatible with internal supervisor & MCP."""
    name: str
    purpose: str
    input_schema: dict = field(default_factory=dict)
    output_schema: dict = field(default_factory=dict)
    execute_fn: Callable[..., ToolResult] = field(default=lambda **kw: ToolResult(tool_name="generic", status="SUCCESS"))
    authorization_required: str = "read_only"
    failure_policy: str = "mark_gap_and_continue"  # retry, mark_gap_and_continue, fallback
    # Dynamic Tool Selection & Capability Descriptors
    capabilities: list[str] = field(default_factory=list)
    evidence_types_generated: list[str] = field(default_factory=list)
    hypothesis_domains: list[str] = field(default_factory=list)
    source_authority: float = 0.80
    typical_latency_ms: float = 20.0
    execution_cost: float = 0.10
    freshness_half_life_days: float = 30.0
    discrimination_targets: list[tuple[str, str]] = field(default_factory=list)
    prerequisites: list[str] = field(default_factory=list)
    historical_reliability: float = 0.98
    source_system: str = "PAIMANA"
    descriptor: Optional[ToolDescriptor] = None
    reliability_profile: Optional[Any] = None
    circuit_breaker: Optional[Any] = None

    def __post_init__(self):
        if self.descriptor is None:
            self.descriptor = ToolDescriptor(
                name=self.name,
                purpose=self.purpose,
                capabilities=list(self.capabilities),
                evidence_types_generated=list(self.evidence_types_generated),
                hypothesis_domains=list(self.hypothesis_domains),
                source_authority=self.source_authority,
                typical_latency_ms=self.typical_latency_ms,
                execution_cost=self.execution_cost,
                freshness_half_life_days=self.freshness_half_life_days,
                discrimination_targets=list(self.discrimination_targets),
                prerequisites=list(self.prerequisites),
                authorization_required=self.authorization_required,
                historical_reliability=self.historical_reliability,
                source_system=self.source_system,
            )

    def execute(self, **kwargs) -> ToolResult:
        t0 = time.time()
        try:
            res = self.execute_fn(**kwargs)
            res.execution_time_ms = (time.time() - t0) * 1000.0
            return res
        except Exception as exc:
            logger.error(f"Tool {self.name} failed during execution: {exc}", exc_info=True)
            return ToolResult(
                tool_name=self.name,
                status="FAILURE",
                error=str(exc),
                summary=f"Execution error in {self.name}: {exc}",
                execution_time_ms=(time.time() - t0) * 1000.0
            )

    def to_mcp_tool(self) -> dict:
        """Converts internal tool definition to standard Model Context Protocol (MCP) tool schema."""
        return {
            "name": self.name,
            "description": self.purpose,
            "inputSchema": self.input_schema,
            "capabilities": self.capabilities,
            "evidence_types": self.evidence_types_generated,
            "source_authority": self.source_authority,
            "cost": self.execution_cost,
        }


# ============================================================================
# Specialist Tool Implementations
# ============================================================================

def _exec_financial_velocity(p: dict, feats: Optional[dict] = None, **kwargs) -> ToolResult:
    feats = feats or {}
    cost = float(p.get("original_cost_cr") or 0.0)
    rev_cost = float(p.get("revised_cost_cr") or cost or 0.0)
    spent = float(p.get("cumulative_expenditure_cr") or 0.0)
    prog = float(p.get("physical_progress_pct") or 0.0)

    spend_pct = (spent / cost * 100.0) if cost > 0 else 0.0
    gap = spend_pct - prog
    cost_growth_pct = ((rev_cost - cost) / cost * 100.0) if cost > 0 and rev_cost > cost else 0.0

    data = {
        "cumulative_expenditure_cr": spent,
        "original_cost_cr": cost,
        "revised_cost_cr": rev_cost,
        "physical_progress_pct": prog,
        "spend_pct_of_original": round(spend_pct, 1),
        "progress_expenditure_gap_pct": round(gap, 1),
        "cost_growth_pct": round(cost_growth_pct, 1),
        "burn_rate_anomaly": gap > 15.0,
    }

    if gap > 20.0:
        summary = (f"Severe financial decoupling: {spend_pct:.1f}% funds expended (Rs {spent:,.1f} Cr) "
                   f"vs only {prog:.1f}% physical work built (gap: +{gap:.1f} pts).")
    elif gap > 10.0:
        summary = f"Moderate spend lead: expenditure is {gap:.1f} pts ahead of physical progress."
    elif gap < -10.0:
        summary = f"Progress lead: physical completion ({prog:.1f}%) is ahead of recorded disbursements ({spend_pct:.1f}%)."
    else:
        summary = f"Balanced burn velocity: spend ({spend_pct:.1f}%) aligns closely with physical progress ({prog:.1f}%)."

    return ToolResult(tool_name="financial_velocity", status="SUCCESS", data=data, summary=summary)


def _exec_milestone_audit(p: dict, feats: Optional[dict] = None, **kwargs) -> ToolResult:
    feats = feats or {}
    orig_date = p.get("original_completion_date", "")
    rev_date = p.get("revised_completion_date", "") or orig_date
    slip = float(feats.get("completion_delay_months", 0.0))
    if math.isnan(slip):
        slip = 0.0
    
    age = feats.get("project_age_months", float("nan"))
    planned_dur = feats.get("planned_duration_months", float("nan"))
    ratio = feats.get("age_to_planned_ratio", float("nan"))
    prog = float(p.get("physical_progress_pct") or 0.0)

    data = {
        "original_completion_date": orig_date,
        "revised_completion_date": rev_date,
        "schedule_slippage_months": round(slip, 1),
        "project_age_months": age if not math.isnan(age) else None,
        "planned_duration_months": planned_dur if not math.isnan(planned_dur) else None,
        "age_to_planned_ratio": round(ratio, 2) if not math.isnan(ratio) else None,
        "physical_progress_pct": prog,
        "is_delayed": slip > 0 or (ratio > 1.0 if not math.isnan(ratio) else False),
    }

    if slip > 0 and ratio > 1.0:
        summary = (f"Critical schedule slippage: completion target deferred by {slip:.0f} months "
                   f"(from {orig_date} to {rev_date}); project has consumed {ratio*100:.0f}% of planned duration with only {prog:.0f}% progress.")
    elif slip > 0:
        summary = f"Milestone date deferred: completion pushed back {slip:.0f} months (target: {rev_date})."
    elif ratio > 1.0:
        summary = f"Time budget overrun: elapsed duration ({ratio*100:.0f}%) exceeds sanctioned lifespan without official date revision."
    else:
        summary = f"Milestone timeline intact: sanctioned target is {orig_date}, duration consumed is on schedule."

    return ToolResult(tool_name="milestone_audit", status="SUCCESS", data=data, summary=summary)


def _exec_project_history(store: Store, project_code: str, **kwargs) -> ToolResult:
    if not store:
        return ToolResult(tool_name="project_history", status="UNAVAILABLE", error="Database store unavailable", summary="No store configured")
    
    preds = store.prediction_history(project_code, limit=10)
    issues = store.list_issues(project_code, limit=10)
    
    risk_history = [{"month": p.get("report_month", "N/A"), "tier": p.get("tier"), "score": round(p.get("risk_score", 0))} for p in preds]
    
    score_jump = 0.0
    if len(preds) >= 2:
        score_jump = preds[-1].get("risk_score", 0) - preds[-2].get("risk_score", 0)

    data = {
        "snapshots_evaluated": len(preds),
        "risk_history": risk_history,
        "recent_score_jump": round(score_jump, 1),
        "detected_issues": [i.get("issue") for i in issues],
    }

    if score_jump >= 8.0:
        summary = f"Accelerating risk trajectory: score jumped +{score_jump:.1f} pts in latest evaluation cycle across {len(preds)} recorded snapshots."
    elif len(preds) > 1:
        summary = f"Stable/gradual trajectory: {len(preds)} historical snapshots recorded, previous score was {preds[-2].get('risk_score', 0):.0f}."
    else:
        summary = "Initial project snapshot: baseline entry with no prior multi-month trajectory."

    return ToolResult(tool_name="project_history", status="SUCCESS", data=data, summary=summary)


def _exec_peer_intelligence(store: Store, project_code: str, sector: str,
                           original_cost_cr: float, physical_progress_pct: float,
                           implementing_agency: str = "", ref_stats: Optional[dict] = None,
                           **kwargs) -> ToolResult:
    """[LEGACY FALLBACK PEER ADAPTER] Basic SQLite peer query.

    NOTE: Canonical peer intelligence capabilities are provided by the specialized
    Peer Intelligence agentic suite via `peer.tools_adapter.make_peer_tool_definitions()`,
    which registers cohort_intelligence, statistical_benchmark, detect_peer_anomalies,
    analyze_trajectory_intelligence, and analyze_domain_context.
    """
    prog = physical_progress_pct
    stage = "Early (<25%)" if prog < 25 else "Mid (25-75%)" if prog <= 75 else "Late (>75%)"
    cost_band = "Mega (>1000Cr)" if original_cost_cr >= 1000 else "Standard (150-1000Cr)"
    
    # Check SQLite live agent memory peers
    n_peers = 0
    n_comp = 0
    comp_cost_rev = 0
    comp_slip = 0
    agency_peers = 0

    if store:
        peers = store.peers(sector, exclude_code=project_code)
        n_peers = len(peers)
        for p in peers:
            p_prog = p.get("physical_progress_pct", 0)
            p_stage = "Early (<25%)" if p_prog < 25 else "Mid (25-75%)" if p_prog <= 75 else "Late (>75%)"
            p_agency = p.get("implementing_agency", "")
            if p_stage == stage:
                n_comp += 1
                if p.get("cost_overrun_pct", 0) > 5.0:
                    comp_cost_rev += 1
                if p.get("slippage_months", 0) > 0:
                    comp_slip += 1
                if implementing_agency and p_agency and implementing_agency.lower() in p_agency.lower():
                    agency_peers += 1

    # Sector national reference stats fallback
    sector_stats = (ref_stats or {}).get("sector_stats", {}).get(sector, {})
    national_cost_freq = sector_stats.get("cost_overrun_pct", 0.0)
    national_slip_freq = sector_stats.get("slippage_pct", 0.0)
    national_mean_overrun = sector_stats.get("mean_cost_overrun_pct", 0.0)

    data = {
        "sector": sector,
        "stage_bracket": stage,
        "cost_band": cost_band,
        "n_peers_seen": n_peers,
        "n_comparable": n_comp,
        "same_agency_count": agency_peers if agency_peers > 0 else None,
        "comparable_with_cost_revision": comp_cost_rev,
        "comparable_with_slippage": comp_slip,
        "sector_national_baseline": {
            "cost_overrun_frequency_pct": national_cost_freq,
            "slippage_frequency_pct": national_slip_freq,
            "mean_cost_overrun_pct": national_mean_overrun,
        } if sector_stats else None,
    }

    if n_comp >= 3:
        summary = (f"{comp_cost_rev}/{n_comp} comparable {sector} projects in {stage} stage "
                   f"experienced cost revisions ({comp_cost_rev/n_comp*100:.0f}%), and {comp_slip}/{n_comp} had slippage.")
    elif sector_stats:
        summary = (f"Sector baseline for {sector}: {national_cost_freq:.0f}% of national projects experience cost revisions "
                   f"(mean: +{national_mean_overrun:.1f}%), and {national_slip_freq:.0f}% experience timeline slippage.")
    else:
        summary = f"Early stage {sector} cohort baseline active."

    data["note"] = summary
    data["summary"] = summary
    data["source"] = f"Agent memory ({cost_band} cohort)"
    return ToolResult(tool_name="peer_intelligence", status="SUCCESS", data=data, summary=summary)


def _exec_memory_retrieval(store: Store, project_code: str, triggering_event_types: Optional[list[str]] = None, **kwargs) -> ToolResult:
    if not store:
        return ToolResult(tool_name="memory_retrieval", status="UNAVAILABLE", error="Store unavailable")

    precedents = store.find_precedents(project_code, limit=10)
    global_precedents = store.find_precedents(code=None, limit=20)
    
    succ = []
    unsucc = []
    for pr in (precedents + global_precedents):
        out = (pr.get("outcome") or "").lower()
        if any(w in out for w in ["resumed", "resolved", "completed", "positive", "improved", "recovered", "cleared", "frozen"]):
            succ.append(pr)
        elif any(w in out for w in ["failed", "stalled", "deteriorated", "worsened", "rejected", "unresolved"]):
            unsucc.append(pr)

    # Hybrid Institutional Memory Retrieval
    getter = getattr(store, "get_project", getattr(store, "latest_snapshot", lambda c: None))
    p = getter(project_code) or kwargs.get("project") or {"project_code": project_code}
    retriever = MemoryRetriever(_default_precedent_store)
    bundle = retriever.retrieve(target_project=p, active_hypotheses=kwargs.get("active_hypotheses"))

    sector = p.get("sector") or "General Infrastructure"
    contract = p.get("contract_type") or "EPC"
    applicable_constraints = _default_policy_store.get_applicable_constraints(sector, contract)

    data = {
        "project_precedents_count": len(precedents),
        "total_historical_precedents": len(global_precedents),
        "successful_precedents": succ[:3],
        "unsuccessful_precedents": unsucc[:3],
        "confidence_boost": 1 if succ else 0,
        "precedent_bundle": bundle.to_dict(),
        "supporting_precedents": [pr.to_dict() for pr in bundle.supporting_precedents],
        "counterexamples": [cx.to_dict() for cx in bundle.counterexamples],
        "failed_precedents": [fp.to_dict() for fp in bundle.failed_precedents],
        "policy_constraints": [c.description for c in applicable_constraints],
        "recommended_hypotheses": bundle.recommended_hypotheses,
        "recommended_tools": bundle.recommended_tools,
        "recommendation_guidance": bundle.recommendation_guidance,
    }

    if succ:
        summary = f"Validated learning precedent found: past action '{succ[0].get('action')[:60]}...' yielded positive outcome '{succ[0].get('outcome')[:60]}'."
    elif bundle.supporting_precedents:
        top_p = bundle.supporting_precedents[0]
        summary = f"Institutional precedent retrieved: '{top_p.title}' from {top_p.source_project_id or top_p.id}. Guidance: {top_p.usage_guidance or top_p.root_cause}"
    elif unsucc or bundle.failed_precedents:
        fail_p = unsucc[0].get('action') if unsucc else bundle.failed_precedents[0].title
        summary = f"Cautionary precedent detected: past action '{fail_p[:60]}...' was recorded as unsuccessful."
    else:
        summary = "No prior recorded intervention outcomes for this specific anomaly pattern."

    return ToolResult(tool_name="memory_retrieval", status="SUCCESS", data=data, summary=summary)


def _exec_shap_attribution(model: Any, feats: dict, feature_cols: Optional[list] = None,
                          background: Optional[Any] = None, rule_drivers: Optional[list[str]] = None,
                          **kwargs) -> ToolResult:
    rule_drivers = rule_drivers or []
    if model is None or background is None or not feature_cols:
        return ToolResult(
            tool_name="shap_attribution",
            status="PARTIAL",
            data={
                "shap_lines": [],
                "fallback_drivers": rule_drivers,
                "evidence_type": "MODEL_DERIVED",
                "is_causal_proof": False,
                "causal_disclaimer": "SHAP reflects permutation feature importance within the predictive ML model and does not establish ground-truth causal transmission without independent physical verification."
            },
            summary="SHAP background reference pending; deterministic rule drivers active."
        )

    try:
        top = shap_top_features(model, feats, feature_cols, background, top_n=3)
        lines = shap_summary_lines(top)
        return ToolResult(
            tool_name="shap_attribution",
            status="SUCCESS",
            data={
                "shap_features": top,
                "shap_lines": lines,
                "evidence_type": "MODEL_DERIVED",
                "is_causal_proof": False,
                "causal_disclaimer": "SHAP reflects permutation feature importance within the predictive ML model and does not establish ground-truth causal transmission without independent physical verification."
            },
            summary="SHAP permutation feature attributions (model-derived, non-causal): " + "; ".join(lines[:2])
        )
    except Exception as e:
        return ToolResult(
            tool_name="shap_attribution",
            status="PARTIAL",
            error=str(e),
            data={
                "shap_lines": [],
                "fallback_drivers": rule_drivers,
                "evidence_type": "MODEL_DERIVED",
                "is_causal_proof": False,
                "causal_disclaimer": "SHAP reflects permutation feature importance within the predictive ML model and does not establish ground-truth causal transmission."
            },
            summary=f"SHAP estimation fallback: {e}"
        )


# ============================================================================
# Tool Registry
# ============================================================================

class ToolRegistry:
    """Central registry of investigation tools with standardized interfaces & MCP exports."""

    def __init__(self, enable_recovery: bool = True):
        self._tools: dict[str, ToolDefinition] = {}
        self.enable_recovery = enable_recovery
        self._recovery_manager: Optional[Any] = None
        self._register_default_tools()

    def get_recovery_manager(self):
        if self._recovery_manager is None:
            from .reliability.recovery_manager import RecoveryManager
            self._recovery_manager = RecoveryManager()
        return self._recovery_manager

    def register(self, tool_def: ToolDefinition):
        self._tools[tool_def.name] = tool_def
        if self.enable_recovery:
            rm = self.get_recovery_manager()
            tool_def.circuit_breaker = rm.get_circuit_breaker(tool_def.name)
            tool_def.reliability_profile = rm.get_profile(tool_def.name)

    def get(self, name: str) -> Optional[ToolDefinition]:
        return self._tools.get(name)

    def get_circuit_breaker(self, tool_name: str):
        return self.get_recovery_manager().get_circuit_breaker(tool_name)

    def get_reliability_profile(self, tool_name: str):
        return self.get_recovery_manager().get_profile(tool_name)

    def list_tools(self) -> list[dict]:
        return [{"name": t.name, "purpose": t.purpose, "authorization": t.authorization_required} for t in self._tools.values()]

    def execute(
        self,
        tool_name: str,
        budget: Optional[Any] = None,
        expected_project_code: Optional[str] = None,
        context: Optional[dict] = None,
        **kwargs
    ) -> ToolResult:
        tool = self._tools.get(tool_name)
        if not tool:
            return ToolResult(
                tool_name=tool_name,
                status=ToolResultStatus.SOURCE_UNAVAILABLE.value,
                error=f"Tool '{tool_name}' is not registered in ToolRegistry",
                summary=f"Unrecognized tool: {tool_name}",
                useful_evidence=False,
            )
        if self.enable_recovery:
            rm = self.get_recovery_manager()
            return rm.execute_with_recovery(
                tool_name=tool_name,
                execute_fn=tool.execute,
                kwargs=kwargs,
                tool_registry=self,
                budget=budget,
                expected_project_code=expected_project_code,
                context=context,
            )
        return tool.execute(**kwargs)

    def export_mcp_manifest(self) -> list[dict]:
        """Exports all registered tools as Model Context Protocol (MCP) compliant definitions."""
        return [t.to_mcp_tool() for t in self._tools.values()]

    def export_tools_manifest(self) -> list[dict]:
        """Exports tool specifications for LLM agent planning."""
        return self.export_mcp_manifest()

    def _register_default_tools(self):
        self.register(ToolDefinition(
            name="financial_velocity",
            purpose="Audits project expenditure vs physical progress to detect disbursement decoupling or abnormal burn rates.",
            input_schema={"type": "object", "properties": {"p": {"type": "object"}, "feats": {"type": "object"}}, "required": ["p"]},
            output_schema={"type": "object", "properties": {"progress_expenditure_gap_pct": {"type": "number"}, "burn_rate_anomaly": {"type": "boolean"}}},
            execute_fn=_exec_financial_velocity,
            capabilities=["audit_spend_progress_decoupling", "detect_burn_rate_anomaly", "verify_disbursement_rate"],
            evidence_types_generated=["financial_audit", "burn_rate", "disbursement_velocity"],
            hypothesis_domains=["front_loaded_billing", "underreported_cost_escalation", "reporting_discrepancy"],
            source_authority=0.92,
            typical_latency_ms=15.0,
            execution_cost=0.05,
            freshness_half_life_days=30.0,
            discrimination_targets=[("front_loaded_billing", "chronic_schedule_delay"), ("front_loaded_billing", "reporting_discrepancy"), ("underreported_cost_escalation", "reporting_discrepancy")],
            prerequisites=["p"],
            authorization_required="read_only",
            historical_reliability=0.99,
            source_system="CUF_FINANCE",
        ))

        self.register(ToolDefinition(
            name="milestone_audit",
            purpose="Audits original vs revised completion milestone targets, schedule slippage, and lifespan ratios.",
            input_schema={"type": "object", "properties": {"p": {"type": "object"}, "feats": {"type": "object"}}, "required": ["p"]},
            output_schema={"type": "object", "properties": {"schedule_slippage_months": {"type": "number"}, "is_delayed": {"type": "boolean"}}},
            execute_fn=_exec_milestone_audit,
            capabilities=["audit_milestone_schedule_slippage", "evaluate_elapsed_duration_ratio", "detect_contractor_mobilization_delays"],
            evidence_types_generated=["schedule_milestone", "timeline_slippage", "duration_ratio"],
            hypothesis_domains=["chronic_schedule_delay", "unrealistic_original_dpr_timeline", "land_acquisition_stalling"],
            source_authority=0.90,
            typical_latency_ms=12.0,
            execution_cost=0.05,
            freshness_half_life_days=30.0,
            discrimination_targets=[("chronic_schedule_delay", "unrealistic_original_dpr_timeline"), ("chronic_schedule_delay", "front_loaded_billing")],
            prerequisites=["p"],
            authorization_required="read_only",
            historical_reliability=0.99,
            source_system="CUF_MILESTONE",
        ))

        self.register(ToolDefinition(
            name="project_history",
            purpose="Audits multi-month risk score trajectory, previous accelerations, and detected issue logs.",
            input_schema={"type": "object", "properties": {"store": {"type": "object"}, "project_code": {"type": "string"}}, "required": ["project_code"]},
            output_schema={"type": "object", "properties": {"risk_history": {"type": "array"}, "recent_score_jump": {"type": "number"}}},
            execute_fn=_exec_project_history,
            capabilities=["audit_multi_month_risk_trajectory", "detect_sudden_risk_score_jumps", "inspect_historical_issue_log"],
            evidence_types_generated=["trajectory_history", "risk_jump", "issue_log"],
            hypothesis_domains=["chronic_schedule_delay", "underreported_cost_escalation", "reporting_discrepancy"],
            source_authority=0.85,
            typical_latency_ms=35.0,
            execution_cost=0.15,
            freshness_half_life_days=60.0,
            discrimination_targets=[("reporting_discrepancy", "chronic_schedule_delay"), ("underreported_cost_escalation", "front_loaded_billing")],
            prerequisites=["store", "project_code"],
            authorization_required="read_only",
            historical_reliability=0.97,
            source_system="PAIMANA_STORE",
        ))

        self.register(ToolDefinition(
            name="peer_intelligence",
            purpose="Benchmarks project against comparable peers (sector, cost scale, progress stage, agency) & national baselines.",
            input_schema={"type": "object", "properties": {"sector": {"type": "string"}, "original_cost_cr": {"type": "number"}, "physical_progress_pct": {"type": "number"}}, "required": ["sector"]},
            output_schema={"type": "object", "properties": {"n_comparable": {"type": "integer"}, "stage_bracket": {"type": "string"}}},
            execute_fn=_exec_peer_intelligence,
            capabilities=["benchmark_against_comparable_sector_peers", "evaluate_agency_track_record", "compare_with_national_baselines"],
            evidence_types_generated=["peer_baseline", "cohort_benchmark", "national_stats"],
            hypothesis_domains=["unrealistic_original_dpr_timeline", "chronic_schedule_delay", "land_acquisition_stalling"],
            source_authority=0.80,
            typical_latency_ms=50.0,
            execution_cost=0.20,
            freshness_half_life_days=90.0,
            discrimination_targets=[("unrealistic_original_dpr_timeline", "chronic_schedule_delay"), ("land_acquisition_stalling", "chronic_schedule_delay")],
            prerequisites=["sector"],
            authorization_required="read_only",
            historical_reliability=0.95,
            source_system="PEER_DB",
        ))

        self.register(ToolDefinition(
            name="memory_retrieval",
            purpose="Retrieves past intervention outcomes and learning precedents to calibrate confidence and recommendations.",
            input_schema={"type": "object", "properties": {"project_code": {"type": "string"}, "triggering_event_types": {"type": "array"}}, "required": ["project_code"]},
            output_schema={"type": "object", "properties": {"successful_precedents": {"type": "array"}, "confidence_boost": {"type": "integer"}}},
            execute_fn=_exec_memory_retrieval,
            capabilities=["retrieve_precedent_intervention_outcomes", "check_cautionary_failed_actions", "calibrate_recommendation_confidence"],
            evidence_types_generated=["precedent_memory", "intervention_outcome", "learning_calibration"],
            hypothesis_domains=["chronic_schedule_delay", "front_loaded_billing", "underreported_cost_escalation"],
            source_authority=0.85,
            typical_latency_ms=40.0,
            execution_cost=0.15,
            freshness_half_life_days=180.0,
            discrimination_targets=[],
            prerequisites=["store", "project_code"],
            authorization_required="read_only",
            historical_reliability=0.96,
            source_system="MEMORY_STORE",
        ))

        self.register(ToolDefinition(
            name="shap_attribution",
            purpose="Computes model-agnostic SHAP permutation feature attributions for risk score explainability.",
            input_schema={"type": "object", "properties": {"model": {"type": "object"}, "feats": {"type": "object"}}, "required": ["feats"]},
            output_schema={"type": "object", "properties": {"shap_lines": {"type": "array"}}},
            execute_fn=_exec_shap_attribution,
            capabilities=["compute_feature_attributions", "explain_ml_model_risk_contributors", "quantify_risk_driver_weights"],
            evidence_types_generated=["model_attribution", "shap_values", "risk_drivers"],
            hypothesis_domains=["underreported_cost_escalation", "chronic_schedule_delay", "front_loaded_billing"],
            source_authority=0.75,
            typical_latency_ms=120.0,
            execution_cost=0.35,
            freshness_half_life_days=30.0,
            discrimination_targets=[("underreported_cost_escalation", "reporting_discrepancy")],
            prerequisites=["model", "feats"],
            authorization_required="read_only",
            historical_reliability=0.92,
            source_system="XGB_MODEL",
        ))

        # Register Peer Intelligence agentic specialized tools
        try:
            from peer.tools_adapter import make_peer_tool_definitions
            for peer_tool_def in make_peer_tool_definitions():
                self.register(peer_tool_def)
        except Exception as e:
            logger.warning(f"Could not register Peer Intelligence tools: {e}")
