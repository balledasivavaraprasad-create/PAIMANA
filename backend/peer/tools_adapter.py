"""Tool Adapters conforming to PAIMANA Tool Registry (MCP-Compatible).

Wraps the 6 peer intelligence capabilities into standard ToolDefinition & ToolResult
contracts compatible with paimana_agent.tools.ToolRegistry and the Dynamic Supervisor Agent:
1. peer_discovery
2. peer_benchmark
3. peer_deviation
4. peer_trajectory
5. peer_outlier
6. peer_cohort_health
7. peer_intelligence (drop-in comprehensive upgrade)
"""
from __future__ import annotations

import sys
from pathlib import Path
import time
from typing import Any, Dict, List, Optional

# Ensure paimana_agent package directory is on sys.path
_current_file = Path(__file__).resolve()
_paimana_agent_v3_dir = _current_file.parent.parent.parent
_paimana_agent_pkg_dir = _paimana_agent_v3_dir / "paimana_agent"
if _paimana_agent_pkg_dir.exists() and str(_paimana_agent_pkg_dir) not in sys.path:
    sys.path.insert(0, str(_paimana_agent_pkg_dir))

from .schemas import CohortDiscoveryResult, PeerBenchmarkResult, PeerDeviationResult
from .service import PeerIntelligenceService

try:
    from paimana_agent.tools import ToolDefinition, ToolResult
except ImportError:
    # Standalone fallback dataclasses if imported outside agent package
    from dataclasses import dataclass, field

    @dataclass
    class ToolResult:
        tool_name: str
        status: str
        data: dict = field(default_factory=dict)
        summary: str = ""
        evidence_items: list[dict] = field(default_factory=list)
        error: Optional[str] = None
        execution_time_ms: float = 0.0

        def to_dict(self) -> dict:
            return {
                "tool": self.tool_name,
                "status": self.status,
                "data": self.data,
                "summary": self.summary,
                "evidence_items": self.evidence_items,
                "error": self.error,
                "execution_time_ms": self.execution_time_ms,
            }

    @dataclass
    class ToolDefinition:
        name: str
        purpose: str
        input_schema: dict
        output_schema: dict
        execute_fn: Any
        authorization_required: str = "read_only"
        failure_policy: str = "mark_gap_and_continue"

        def execute(self, **kwargs) -> ToolResult:
            t0 = time.time()
            res = self.execute_fn(**kwargs)
            res.execution_time_ms = (time.time() - t0) * 1000.0
            return res


def _resolve_service(default_svc: Optional[PeerIntelligenceService], kwargs: dict) -> PeerIntelligenceService:
    """Dynamically resolves or creates a PeerIntelligenceService for the passed store."""
    store = kwargs.get("store")
    if store is not None:
        from .repository import SQLiteProjectRepository, ProjectRepository
        if isinstance(store, ProjectRepository):
            repo = store
        else:
            repo = SQLiteProjectRepository(store)
        return PeerIntelligenceService(repository=repo)
    if default_svc is not None:
        return default_svc
    from .repository import InMemoryProjectRepository
    return PeerIntelligenceService(repository=InMemoryProjectRepository())


def _resolve_p(p: Optional[Dict[str, Any]], kwargs: dict) -> Dict[str, Any]:
    """Ensures a project dictionary is present, resolving from store or kwargs without demo defaults."""
    if p is not None and isinstance(p, dict) and p:
        return dict(p)
    if "p" in kwargs and isinstance(kwargs["p"], dict) and kwargs["p"]:
        return dict(kwargs["p"])

    # Attempt resolution from store via project_code if available
    code = str(kwargs.get("project_code", "")).strip()
    store = kwargs.get("store")
    if code and store is not None:
        getter = getattr(store, "latest_snapshot", getattr(store, "get_project", None))
        if getter:
            stored_p = getter(code)
            if stored_p and isinstance(stored_p, dict):
                return dict(stored_p)

    cost = kwargs.get("original_cost_cr") or kwargs.get("original_cost") or kwargs.get("cost")
    prog = kwargs.get("physical_progress_pct") or kwargs.get("physical_progress") or kwargs.get("progress")

    return {
        "project_code": code,
        "project_name": str(kwargs.get("project_name", code or "Unknown Project")).strip(),
        "sector": str(kwargs.get("sector", "")).strip(),
        "original_cost_cr": float(cost) if cost is not None else 0.0,
        "physical_progress_pct": float(prog) if prog is not None else 0.0,
        "implementing_agency": str(kwargs.get("implementing_agency", kwargs.get("agency", ""))).strip(),
    }


def make_peer_tool_definitions(service: Optional[PeerIntelligenceService] = None) -> List[ToolDefinition]:
    """Builds and returns formal ToolDefinitions for the supervisor registry."""

    # 1. Peer Discovery
    def _exec_discovery(p: Optional[Dict[str, Any]] = None, min_similarity: Optional[float] = None, max_peers: Optional[int] = None, **kwargs) -> ToolResult:
        p = _resolve_p(p, kwargs)
        svc = _resolve_service(service, kwargs)
        context = kwargs.get("context")
        if context is None and (kwargs.get("hypothesis_id") or kwargs.get("investigation_question") or kwargs.get("investigation_type")):
            from .discovery import PeerInvestigationContext
            context = PeerInvestigationContext(
                target_project_id=str(p.get("project_code", "")),
                investigation_question=kwargs.get("investigation_question"),
                hypothesis_id=kwargs.get("hypothesis_id"),
                investigation_type=kwargs.get("investigation_type"),
                as_of_date=kwargs.get("as_of_date"),
                max_peers=max_peers or 10,
                min_similarity=min_similarity or 0.50,
            )
        res = svc.peer_discovery(p, min_similarity=min_similarity, max_peers=max_peers, context=context)
        evidence = [{
            "type": "PEER_COHORT_DISCOVERED",
            "statement": f"Identified {res.cohort_size} comparable peers for {res.target_project_name} (Cohort Quality: {res.quality.value})",
            "source": "peer_discovery",
            "peer_codes": [peer.peer_code for peer in res.peers],
        }]
        if context is not None and "selection_dossier" in res.source_lineage:
            dossier = res.source_lineage["selection_dossier"]
            evidence.append({
                "type": "PEER_DISCOVERY_STRATEGY",
                "statement": f"Strategy: {dossier.get('strategy_id')} ({dossier.get('investigation_type')}) - {dossier.get('narrative_explanation', '')}",
                "source": "peer_discovery",
            })
        summary = (
            f"Peer cohort: {res.cohort_size} comparable projects in sector '{p.get('sector')}' "
            f"(Quality: {res.quality.value}, Avg Similarity: {res.average_similarity:.2f})."
        )
        return ToolResult(tool_name="peer_discovery", status="SUCCESS" if res.is_sufficient else "PARTIAL",
                          data=res.to_dict(), summary=summary, evidence_items=evidence)

    # 2. Peer Benchmark
    def _exec_benchmark(p: Optional[Dict[str, Any]] = None, metrics: Optional[List[str]] = None, **kwargs) -> ToolResult:
        p = _resolve_p(p, kwargs)
        svc = _resolve_service(service, kwargs)
        res = svc.peer_benchmark(p, metrics=metrics)
        evidence = []
        for m, dist in res.distributions.items():
            evidence.append({
                "type": "PEER_BENCHMARK",
                "statement": f"Peer cohort median for {m} is {dist.median:.2f} (IQR: {dist.p25:.2f} - {dist.p75:.2f})",
                "source": "peer_benchmark",
            })
        summary = f"Peer statistical benchmarks computed across {len(res.distributions)} metrics."
        return ToolResult(tool_name="peer_benchmark", status="SUCCESS" if res.is_sufficient else "PARTIAL",
                          data=res.to_dict(), summary=summary, evidence_items=evidence)

    # 3. Peer Deviation
    def _exec_deviation(p: Optional[Dict[str, Any]] = None, metrics: Optional[List[str]] = None, **kwargs) -> ToolResult:
        p = _resolve_p(p, kwargs)
        svc = _resolve_service(service, kwargs)
        res = svc.peer_deviation(p, metrics=metrics)
        evidence = []
        for m, dev in res.deviations.items():
            if dev.is_significant:
                evidence.append({
                    "type": "PEER_DEVIATION",
                    "statement": dev.interpretation,
                    "direction": dev.direction.value,
                    "percentile_rank": dev.percentile_rank,
                    "source": "peer_deviation",
                })
        return ToolResult(tool_name="peer_deviation", status="SUCCESS" if res.is_sufficient else "PARTIAL",
                          data=res.to_dict(), summary=res.summary, evidence_items=evidence)

    # 4. Peer Trajectory
    def _exec_trajectory(p: Optional[Dict[str, Any]] = None, window_snapshots: int = 6, **kwargs) -> ToolResult:
        p = _resolve_p(p, kwargs)
        code = str(p.get("project_code", kwargs.get("project_code", ""))).strip()
        svc = _resolve_service(service, kwargs)
        res = svc.peer_trajectory(code, window_snapshots=window_snapshots)
        evidence = []
        for m, comp in res.comparisons.items():
            if comp.status == "OK":
                evidence.append({
                    "type": "PEER_TRAJECTORY_DELTA",
                    "statement": comp.summary,
                    "direction": comp.direction.value,
                    "source": "peer_trajectory",
                })
        return ToolResult(tool_name="peer_trajectory", status="SUCCESS" if res.is_sufficient_history else "PARTIAL",
                          data=res.to_dict(), summary=res.summary, evidence_items=evidence)

    # 5. Peer Outlier
    def _exec_outlier(p: Optional[Dict[str, Any]] = None, **kwargs) -> ToolResult:
        p = _resolve_p(p, kwargs)
        svc = _resolve_service(service, kwargs)
        res = svc.peer_outlier(p)
        evidence = []
        for m, ev in res.evaluations.items():
            evidence.append({
                "type": "PEER_OUTLIER_EVALUATION",
                "statement": ev.distinction_explanation,
                "is_outlier": ev.is_peer_outlier,
                "severity": ev.severity.value,
                "absolute_risk": ev.absolute_risk_level,
                "peer_relative_risk": ev.peer_relative_risk_level,
                "source": "peer_outlier",
            })
        return ToolResult(tool_name="peer_outlier", status="SUCCESS" if res.is_sufficient else "PARTIAL",
                          data=res.to_dict(), summary=res.summary, evidence_items=evidence)

    # 6. Peer Cohort Health
    def _exec_health(p: Optional[Dict[str, Any]] = None, **kwargs) -> ToolResult:
        p = _resolve_p(p, kwargs)
        svc = _resolve_service(service, kwargs)
        data = svc.peer_cohort_health(p)
        summary = f"Peer cohort health: {data['cohort_size']} peers, Quality: {data['cohort_quality']}, Avg Similarity: {data['average_similarity']:.2f}"
        return ToolResult(tool_name="peer_cohort_health", status="SUCCESS" if data["is_sufficient"] else "PARTIAL",
                          data=data, summary=summary)

    # 7. Comprehensive Master Tool
    def _exec_comprehensive(p: Optional[Dict[str, Any]] = None, metrics: Optional[List[str]] = None, **kwargs) -> ToolResult:
        p = _resolve_p(p, kwargs)
        svc = _resolve_service(service, kwargs)
        report = svc.get_comprehensive_peer_intelligence(p, metrics=metrics)
        health = report.get("cohort_health", {})

        # Compute legacy backwards-compatible attributes
        prog = float(p.get("physical_progress_pct", 0.0) or 0.0)
        stage = "Early (<25%)" if prog < 25 else "Mid (25-75%)" if prog <= 75 else "Late (>75%)"
        cost_val = float(p.get("original_cost_cr", 0.0) or 0.0)
        cost_band = "Mega (>1000Cr)" if cost_val >= 1000 else "Standard (150-1000Cr)"
        agency = str(p.get("implementing_agency", ""))
        sector = str(p.get("sector", "Unknown"))

        peers_list = report.get("discovery", {}).get("peers", [])
        n_comp = len(peers_list)
        agency_peers = sum(1 for peer in peers_list
                           if agency and agency.lower() in str(peer.get("implementing_agency", "")).lower())
        comp_cost_rev = sum(1 for peer in peers_list
                            if float(peer.get("cost_overrun_pct", 0.0) or 0.0) > 5.0)
        comp_slip = sum(1 for peer in peers_list
                        if float(peer.get("slippage_months", 0.0) or peer.get("schedule_slippage_months", 0.0) or 0.0) > 0)

        ref_stats = kwargs.get("ref_stats")
        sector_stats = (ref_stats or {}).get("sector_stats", {}).get(sector, {})
        national_cost_freq = float(sector_stats.get("cost_overrun_pct", 0.0) or 0.0)
        national_slip_freq = float(sector_stats.get("slippage_pct", 0.0) or 0.0)
        national_mean_overrun = float(sector_stats.get("mean_cost_overrun_pct", 0.0) or 0.0)

        report["sector"] = sector
        report["stage_bracket"] = stage
        report["cost_band"] = cost_band
        report["n_peers_seen"] = health.get("cohort_size", n_comp)
        report["n_comparable"] = n_comp
        report["same_agency_count"] = agency_peers if agency_peers > 0 else None
        report["comparable_with_cost_revision"] = comp_cost_rev
        report["comparable_with_slippage"] = comp_slip
        report["sector_national_baseline"] = {
            "cost_overrun_frequency_pct": national_cost_freq,
            "slippage_frequency_pct": national_slip_freq,
            "mean_cost_overrun_pct": national_mean_overrun,
        } if sector_stats else None
        report["source"] = f"Agent memory ({cost_band} cohort)"

        dev_sum = report.get("deviations", {}).get("summary", "")
        out_sum = report.get("outliers", {}).get("summary", "")
        summary = (
            f"Peer Intelligence for {report.get('target_code', p.get('project_code', ''))}: "
            f"{health.get('cohort_size', 0)} peers ({health.get('cohort_quality', 'UNKNOWN')}). "
            f"Deviations: {dev_sum} | Outlier: {out_sum}"
        )
        report["note"] = summary
        report["summary"] = summary

        is_suff = health.get("is_sufficient", True)
        return ToolResult(
            tool_name="peer_intelligence",
            status="SUCCESS" if is_suff else "PARTIAL",
            data=report,
            summary=summary,
            evidence_items=report.get("domain_context", {}).get("evidence_items", [])
        )

    # 8. Cohort Intelligence (CI-10)
    def _exec_cohort_intelligence(p: Optional[Dict[str, Any]] = None, metrics: Optional[List[str]] = None, **kwargs) -> ToolResult:
        p = _resolve_p(p, kwargs)
        svc = _resolve_service(service, kwargs)
        res = svc.analyze_cohort_intelligence(p, metrics=metrics)
        summary = (
            f"Cohort Intelligence: Quality is {res.quality.overall_quality.value} (score: {res.quality.overall_score:.2f}). "
            f"Heterogeneity: {res.heterogeneity.overall_level} | Recommendation: {res.recommendation.value}"
        )
        return ToolResult(tool_name="cohort_intelligence", status="SUCCESS",
                          data=res.to_dict(), summary=summary, evidence_items=res.evidence)

    # 9. Statistical Benchmark (SB-12)
    def _exec_statistical_benchmark(p: Optional[Dict[str, Any]] = None, metrics: Optional[List[str]] = None, **kwargs) -> ToolResult:
        p = _resolve_p(p, kwargs)
        svc = _resolve_service(service, kwargs)
        res = svc.statistical_benchmark(p, metrics=metrics, **kwargs)
        summary = (
            f"Statistical Benchmarking: Evaluated {len(res.benchmarks)} metrics across cohort of {res.cohort_size} peers."
        )
        return ToolResult(tool_name="statistical_benchmark", status="SUCCESS" if res.cohort_size >= 3 else "PARTIAL",
                          data=res.to_dict(), summary=summary, evidence_items=res.evidence_items)

    # 10. Peer Anomaly & Outlier Detection (DO-12)
    def _exec_detect_peer_anomalies(p: Optional[Dict[str, Any]] = None, metrics: Optional[List[str]] = None, **kwargs) -> ToolResult:
        p = _resolve_p(p, kwargs)
        svc = _resolve_service(service, kwargs)
        res = svc.detect_peer_anomalies(p, metrics=metrics, **kwargs)
        summary = (
            f"Peer Anomaly Detection: Evaluated {len(res.metrics_evaluated)} metrics. "
            f"Overall Severity: {res.overall_severity.value}. Outlier: {res.overall_is_outlier}."
        )
        return ToolResult(tool_name="detect_peer_anomalies", status="SUCCESS" if res.cohort_size >= 3 else "PARTIAL",
                          data=res.to_dict(), summary=summary, evidence_items=res.evidence_items)

    # 11. Trajectory Intelligence (TI-14)
    def _exec_trajectory_intelligence(p: Optional[Dict[str, Any]] = None, metrics: Optional[List[str]] = None, **kwargs) -> ToolResult:
        p = _resolve_p(p, kwargs)
        code = str(p.get("project_code", kwargs.get("project_code", ""))).strip()
        svc = _resolve_service(service, kwargs)
        res = svc.analyze_trajectory_intelligence(code, metrics=metrics, target_project=p, **kwargs)
        summary = (
            f"Trajectory Intelligence for {code}: Regime={res.execution_regime.current_regime.value}, "
            f"Reliability={res.overall_reliability.value}. Findings={len(res.findings)}."
        )
        return ToolResult(tool_name="analyze_trajectory_intelligence", status="SUCCESS" if res.snapshots_analyzed >= 2 else "PARTIAL",
                          data=res.to_dict(), summary=summary, evidence_items=res.evidence_items)

    # 12. Domain Intelligence (DSI-01 to DSI-14)
    def _exec_domain_context(p: Optional[Dict[str, Any]] = None, question: Optional[str] = None, hypothesis: Optional[str] = None, **kwargs) -> ToolResult:
        p = _resolve_p(p, kwargs)
        svc = _resolve_service(service, kwargs)
        res = svc.analyze_domain_context(p, question=question, hypothesis=hypothesis, **kwargs)
        summary = (
            f"Domain Context for {res.project_code} ({res.profile.sector.value}): "
            f"Constraints={len(res.key_constraints)}, Data Gaps={len(res.data_gaps)}, "
            f"Strategies={len(res.investigation_strategies)}."
        )
        return ToolResult(
            tool_name="analyze_domain_context",
            status="SUCCESS",
            data=res.to_dict(),
            summary=summary,
            evidence_items=res.evidence_items,
        )

    return [
        ToolDefinition(
            name="peer_discovery",
            purpose="Identifies comparable peer projects with transparent similarity explanations.",
            input_schema={"type": "object", "properties": {"p": {"type": "object"}}},
            output_schema={"type": "object"},
            execute_fn=_exec_discovery,
            capabilities=["peer_cohort_discovery", "similarity_filtering", "cohort_identification"],
            evidence_types_generated=["peer_cohort", "comparable_projects"],
            hypothesis_domains=["chronic_schedule_delay", "unrealistic_original_dpr_timeline"],
            source_authority=0.85,
            typical_latency_ms=25.0,
            execution_cost=0.10,
            freshness_half_life_days=90.0,
            source_system="PAIMANA_PEER_DB",
        ),
        ToolDefinition(
            name="peer_benchmark",
            purpose="Calculates robust statistical baselines (medians/IQR) across peer cohort.",
            input_schema={"type": "object", "properties": {"p": {"type": "object"}}},
            output_schema={"type": "object"},
            execute_fn=_exec_benchmark,
            capabilities=["statistical_benchmarks", "metric_distributions", "cohort_percentiles"],
            evidence_types_generated=["peer_benchmark", "statistical_distribution"],
            hypothesis_domains=["chronic_schedule_delay", "underreported_cost_escalation"],
            source_authority=0.85,
            typical_latency_ms=25.0,
            execution_cost=0.10,
            freshness_half_life_days=90.0,
            source_system="PAIMANA_PEER_DB",
        ),
        ToolDefinition(
            name="peer_deviation",
            purpose="Evaluates target project performance deviations against peer medians.",
            input_schema={"type": "object", "properties": {"p": {"type": "object"}}},
            output_schema={"type": "object"},
            execute_fn=_exec_deviation,
            capabilities=["performance_deviation", "percentile_ranking", "peer_relative_divergence"],
            evidence_types_generated=["peer_deviation", "relative_performance"],
            hypothesis_domains=["chronic_schedule_delay", "front_loaded_billing"],
            source_authority=0.85,
            typical_latency_ms=25.0,
            execution_cost=0.10,
            freshness_half_life_days=90.0,
            source_system="PAIMANA_PEER_DB",
        ),
        ToolDefinition(
            name="peer_trajectory",
            purpose="Compares historical monthly change rates between target and peer cohort.",
            input_schema={"type": "object", "properties": {"p": {"type": "object"}}},
            output_schema={"type": "object"},
            execute_fn=_exec_trajectory,
            capabilities=["historical_velocity_comparison", "monthly_drift_tracking", "cohort_trajectory_analysis"],
            evidence_types_generated=["peer_trajectory", "temporal_drift"],
            hypothesis_domains=["chronic_schedule_delay", "reporting_discrepancy"],
            source_authority=0.85,
            typical_latency_ms=30.0,
            execution_cost=0.12,
            freshness_half_life_days=60.0,
            source_system="PAIMANA_PEER_DB",
        ),
        ToolDefinition(
            name="peer_outlier",
            purpose="Identifies peer-relative anomalies while separating absolute risk from peer context.",
            input_schema={"type": "object", "properties": {"p": {"type": "object"}}},
            output_schema={"type": "object"},
            execute_fn=_exec_outlier,
            capabilities=["peer_relative_outliers", "anomaly_classification", "multivariate_outliers"],
            evidence_types_generated=["peer_outlier", "relative_anomaly"],
            hypothesis_domains=["chronic_schedule_delay", "land_acquisition_stalling"],
            source_authority=0.85,
            typical_latency_ms=25.0,
            execution_cost=0.10,
            freshness_half_life_days=90.0,
            source_system="PAIMANA_PEER_DB",
        ),
        ToolDefinition(
            name="peer_cohort_health",
            purpose="Evaluates cohort size, similarity strength, and data completeness.",
            input_schema={"type": "object", "properties": {"p": {"type": "object"}}},
            output_schema={"type": "object"},
            execute_fn=_exec_health,
            capabilities=["cohort_data_completeness", "similarity_strength", "cohort_health_scoring"],
            evidence_types_generated=["cohort_health", "data_quality"],
            hypothesis_domains=["chronic_schedule_delay"],
            source_authority=0.85,
            typical_latency_ms=20.0,
            execution_cost=0.08,
            freshness_half_life_days=90.0,
            source_system="PAIMANA_PEER_DB",
        ),
        ToolDefinition(
            name="peer_intelligence",
            purpose="Comprehensive peer cohort discovery, benchmarking, deviation, trajectory, and outlier analysis.",
            input_schema={"type": "object", "properties": {"p": {"type": "object"}, "sector": {"type": "string"}, "original_cost_cr": {"type": "number"}, "physical_progress_pct": {"type": "number"}}},
            output_schema={"type": "object", "properties": {"n_comparable": {"type": "integer"}, "stage_bracket": {"type": "string"}}},
            execute_fn=_exec_comprehensive,
            capabilities=["benchmark_against_comparable_sector_peers", "evaluate_agency_track_record", "compare_with_national_baselines", "comprehensive_peer_intelligence"],
            evidence_types_generated=["peer_baseline", "cohort_benchmark", "national_stats", "peer_cohort"],
            hypothesis_domains=["unrealistic_original_dpr_timeline", "chronic_schedule_delay", "land_acquisition_stalling"],
            source_authority=0.85,
            typical_latency_ms=45.0,
            execution_cost=0.18,
            freshness_half_life_days=90.0,
            source_system="PAIMANA_PEER_DB",
        ),
        ToolDefinition(
            name="cohort_intelligence",
            purpose="Evaluates multidimensional cohort quality, distribution shape, heterogeneity, subgroups, and refinement recommendations.",
            input_schema={"type": "object", "properties": {"p": {"type": "object"}}},
            output_schema={"type": "object"},
            execute_fn=_exec_cohort_intelligence,
            capabilities=["multidimensional_cohort_quality", "heterogeneity_assessment"],
            evidence_types_generated=["cohort_quality", "distribution_shape"],
            hypothesis_domains=["chronic_schedule_delay"],
            source_authority=0.85,
            typical_latency_ms=30.0,
            execution_cost=0.12,
            freshness_half_life_days=90.0,
            source_system="PAIMANA_PEER_DB",
        ),
        ToolDefinition(
            name="statistical_benchmark",
            purpose="Computes robust reference profiles, bootstrap confidence intervals, and empirical percentiles across peer cohorts.",
            input_schema={"type": "object", "properties": {"p": {"type": "object"}}},
            output_schema={"type": "object"},
            execute_fn=_exec_statistical_benchmark,
            capabilities=["bootstrap_confidence_intervals", "empirical_percentiles"],
            evidence_types_generated=["statistical_profiles"],
            hypothesis_domains=["chronic_schedule_delay"],
            source_authority=0.85,
            typical_latency_ms=30.0,
            execution_cost=0.12,
            freshness_half_life_days=90.0,
            source_system="PAIMANA_PEER_DB",
        ),
        ToolDefinition(
            name="detect_peer_anomalies",
            purpose="Performs multi-method, contextual, multivariate, and temporal anomaly detection across peer cohorts.",
            input_schema={"type": "object", "properties": {"p": {"type": "object"}}},
            output_schema={"type": "object"},
            execute_fn=_exec_detect_peer_anomalies,
            capabilities=["multivariate_anomaly_detection", "contextual_outliers"],
            evidence_types_generated=["peer_anomalies"],
            hypothesis_domains=["chronic_schedule_delay", "front_loaded_billing"],
            source_authority=0.85,
            typical_latency_ms=35.0,
            execution_cost=0.15,
            freshness_half_life_days=90.0,
            source_system="PAIMANA_PEER_DB",
        ),
        ToolDefinition(
            name="analyze_trajectory_intelligence",
            purpose="Performs rolling velocity, acceleration, stagnation, recovery, and regime-shift analysis across historical snapshots.",
            input_schema={"type": "object", "properties": {"p": {"type": "object"}}},
            output_schema={"type": "object"},
            execute_fn=_exec_trajectory_intelligence,
            capabilities=["regime_shift_analysis", "stagnation_recovery_detection"],
            evidence_types_generated=["trajectory_intelligence"],
            hypothesis_domains=["chronic_schedule_delay"],
            source_authority=0.85,
            typical_latency_ms=35.0,
            execution_cost=0.15,
            freshness_half_life_days=60.0,
            source_system="PAIMANA_PEER_DB",
        ),
        ToolDefinition(
            name="analyze_domain_context",
            purpose="Analyzes domain-specific infrastructure operational realities, land acquisition, clearances, utilities, terrain, and dependency bottlenecks.",
            input_schema={"type": "object", "properties": {"p": {"type": "object"}}},
            output_schema={"type": "object"},
            execute_fn=_exec_domain_context,
            capabilities=["domain_operational_realities", "bottleneck_analysis"],
            evidence_types_generated=["domain_context", "clearance_dependencies"],
            hypothesis_domains=["land_acquisition_stalling", "chronic_schedule_delay"],
            source_authority=0.85,
            typical_latency_ms=25.0,
            execution_cost=0.10,
            freshness_half_life_days=90.0,
            source_system="PAIMANA_PEER_DB",
        ),
    ]

