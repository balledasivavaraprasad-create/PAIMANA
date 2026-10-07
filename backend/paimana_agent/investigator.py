"""Agentic Investigation Layer (PAIMANA Continuous Monitoring v3+).

Provides an observation-driven stateful Supervisor Agent, formal tool registry,
evidence model, contradiction handling, and recommendation validation.
"""
from __future__ import annotations
from typing import Optional, Any

from .store import Store
from .tracer import AgentTracer
from .tools import ToolRegistry, _exec_financial_velocity, _exec_milestone_audit, _exec_project_history, _exec_peer_intelligence, _exec_memory_retrieval, _exec_shap_attribution
from .supervisor import SupervisorAgent

_default_registry = ToolRegistry()
_default_tracer = AgentTracer()
_default_supervisor = SupervisorAgent(tool_registry=_default_registry, tracer=_default_tracer)


# ============================================================================
# Backward-Compatible Tool Helper Functions
# ============================================================================

def tool_project_history(store: Store, code: str) -> dict:
    res = _exec_project_history(store=store, project_code=code)
    data = res.data
    data["summary"] = res.summary
    data["tool"] = "get_project_history"
    return data


def tool_milestone_audit(p: dict, feats: Optional[dict] = None) -> dict:
    res = _exec_milestone_audit(p=p, feats=feats)
    data = res.data
    data["summary"] = res.summary
    data["tool"] = "milestone_audit"
    return data


def tool_financial_velocity(p: dict, feats: Optional[dict] = None) -> dict:
    res = _exec_financial_velocity(p=p, feats=feats)
    data = res.data
    data["summary"] = res.summary
    data["tool"] = "financial_velocity_audit"
    return data


def tool_peer_intelligence(store: Store, code: str, sector: str, cost_cr: float,
                           progress_pct: float = 0.0, agency: str = "",
                           ref_stats: Optional[dict] = None) -> dict:
    res = _exec_peer_intelligence(
        store=store, project_code=code, sector=sector,
        original_cost_cr=cost_cr, physical_progress_pct=progress_pct,
        implementing_agency=agency, ref_stats=ref_stats
    )
    data = res.data
    data["summary"] = res.summary
    data["note"] = res.summary
    data["source"] = f"Agent memory ({data.get('cost_band')} cohort)"
    return data


def tool_past_interventions_and_learning(store: Store, code: str, triggering_event_types: list[str]) -> dict:
    res = _exec_memory_retrieval(store=store, project_code=code, triggering_event_types=triggering_event_types)
    data = res.data
    data["summary"] = res.summary
    return data


def tool_shap_and_drivers(model: Any, feats: dict, feature_cols: Optional[list] = None,
                          background: Optional[Any] = None, drivers: Optional[list[str]] = None) -> dict:
    res = _exec_shap_attribution(model=model, feats=feats, feature_cols=feature_cols, background=background, rule_drivers=drivers)
    data = res.data
    data["summary"] = res.summary
    return data


# ============================================================================
# Main Entry Point for Agentic Investigation
# ============================================================================

def investigate(store: Store, p: dict, res: dict, drivers: list[str], events: list[dict],
                model=None, feats: Optional[dict] = None, feature_cols: Optional[list] = None,
                background=None, event_id: Optional[int] = None,
                ref_stats: Optional[dict] = None, supervisor: Optional[SupervisorAgent] = None) -> dict:
    """Invokes the stateful Supervisor Agent to conduct a dynamic, observation-driven investigation."""
    sup = supervisor or _default_supervisor
    return sup.run_investigation(
        store=store, p=p, res=res, drivers=drivers, events=events,
        model=model, feats=feats, feature_cols=feature_cols, background=background,
        event_id=event_id, ref_stats=ref_stats
    )
