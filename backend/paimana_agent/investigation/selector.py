"""Dynamic Information-Seeking Tool Selector & Planner.

Implements uncertainty-driven tool selection by evaluating candidate utilities,
monitoring operational phases, and maintaining full audit trails.
"""
from __future__ import annotations
import logging
from typing import Any, Optional
from .candidate import ToolCandidate, ToolSelectionRecord
from .evidence_need import EvidenceNeed
from .gap_analyzer import EvidenceGapAnalyzer
from .utility import ToolUtilityEvaluator
from .budget import InvestigationBudget, InvestigationPhase, ConvergenceDetector

logger = logging.getLogger("paimana_agent.investigation.selector")


class DynamicInformationSeekingSelector:
    """Selects optimal next investigation tool based on uncertainty reduction and utility."""

    def __init__(self,
                 utility_evaluator: Optional[ToolUtilityEvaluator] = None,
                 gap_analyzer: Optional[EvidenceGapAnalyzer] = None):
        self.utility_eval = utility_evaluator or ToolUtilityEvaluator()
        self.gap_analyzer = gap_analyzer or EvidenceGapAnalyzer()

    def select_next_step(self, state: Any, p: dict, feats: dict,
                         event_types: list[str], registry: Any,
                         budget: Optional[InvestigationBudget] = None,
                         caller_authorization: str = "read_only",
                         store: Optional[Any] = None,
                         model: Optional[Any] = None) -> tuple[Optional[str], list[ToolCandidate], bool, Optional[str], str, str]:
        """Evaluates tools and returns (selected_tool_name, candidates, is_terminated, stop_reason, thought, goal)."""
        # 1. Update and analyze evidence needs
        all_needs = self.gap_analyzer.analyze_needs(state, p, feats, event_types)
        state.evidence_needs = all_needs
        open_needs = [n for n in all_needs if n.status == "OPEN"]

        # 2. Determine investigation phase
        used_tools = getattr(state, "tools_used", [])
        if len(used_tools) == 0:
            phase = InvestigationPhase.ORIENTATION
        else:
            hypotheses = getattr(state, "hypotheses", [])
            active_h = [h for h in hypotheses if getattr(h, "status", "").lower() in ["active", "supported", "primary"]]
            if len(active_h) >= 2:
                c1 = getattr(active_h[0], "confidence_score", getattr(active_h[0], "confidence", 0.5))
                c2 = getattr(active_h[1], "confidence_score", getattr(active_h[1], "confidence", 0.5))
                if isinstance(c1, str):
                    c1 = 0.85 if c1 == "HIGH" else (0.50 if c1 == "MEDIUM" else 0.20)
                if isinstance(c2, str):
                    c2 = 0.85 if c2 == "HIGH" else (0.50 if c2 == "MEDIUM" else 0.20)
                if abs(c1 - c2) < 0.20:
                    phase = InvestigationPhase.DISCRIMINATION
                elif c1 >= 0.60:
                    phase = InvestigationPhase.VALIDATION
                else:
                    phase = InvestigationPhase.DECISION_SUPPORT
            elif len(used_tools) >= 3:
                phase = InvestigationPhase.DECISION_SUPPORT
            else:
                phase = InvestigationPhase.DISCRIMINATION

        state.investigation_phase = phase

        # 3. Evaluate each tool in the registry
        tools_dict = getattr(registry, "_tools", {})
        candidates: list[ToolCandidate] = []
        for t_name, t_def in tools_dict.items():
            cand = self.utility_eval.evaluate_candidate(
                tool_def=t_def,
                state=state,
                open_needs=open_needs,
                caller_authorization=caller_authorization,
                store_available=(store is not None),
                model_available=(model is not None or "feats" in t_def.prerequisites),
            )
            try:
                from ..governance.budget import ResourceEstimator, get_tool_cost_profile
                prof = get_tool_cost_profile(t_name)
                cand.estimated_financial_cost = prof.estimated_cost
                cand.resource_adjusted_value = ResourceEstimator.calculate_resource_adjusted_value(
                    tool_name=t_name,
                    expected_information_gain=cand.expected_information_gain,
                    decision_relevance=1.0,
                    evidence_quality=cand.source_authority,
                    budget=budget,
                )
                if budget and not budget.can_afford(estimated_cost=prof.estimated_cost, estimated_latency_ms=prof.estimated_latency_ms):
                    cand.is_affordable = False
            except Exception:
                pass
            candidates.append(cand)

        # Sort candidates: eligible first, then by net_utility descending
        candidates.sort(key=lambda c: (c.eligible, c.net_utility), reverse=True)
        state.tool_candidates = candidates

        # 4. Check convergence / termination policy
        detector = getattr(state, "_convergence_detector", None)
        if detector is None:
            detector = ConvergenceDetector(budget=budget)
            try:
                state._convergence_detector = detector
            except Exception:
                pass
        else:
            detector.budget = budget

        is_terminated, stop_reason, explanation = detector.check_termination(state, candidates, open_needs)
        if is_terminated:
            thought = f"Investigation stopping: {explanation}"
            goal = "Finalize Investigation"
            return None, candidates, True, stop_reason, thought, goal

        # 5. Select best eligible candidate
        eligible = [c for c in candidates if c.eligible]
        if not eligible or eligible[0].net_utility <= 0.0:
            return None, candidates, True, "NO_HIGH_VALUE_TOOL_REMAINING", "No high-value tools remaining.", "Finalize Investigation"

        best_cand = eligible[0]
        selected_tool = best_cand.tool_name
        step_num = len(used_tools) + 1

        # 6. Formulate goal & thought strings
        goal = self._determine_goal(selected_tool, step_num, phase, event_types, state)
        thought = (
            f"Phase [{phase}]: Selected '{selected_tool}' (utility={best_cand.net_utility:.3f}, "
            f"gain={best_cand.expected_information_gain:.2f}, disc={best_cand.discrimination_power:.2f}, "
            f"authority={best_cand.source_authority:.2f}) to resolve: {best_cand.target_needs or 'anomaly context'}."
        )

        # Record tool selection in audit history
        record = ToolSelectionRecord(
            step=step_num,
            phase=phase,
            selected_tool=selected_tool,
            net_utility=best_cand.net_utility,
            candidates_evaluated=[c.to_dict() for c in candidates],
            evidence_needs_addressed=best_cand.target_needs,
            selection_rationale=best_cand.selection_rationale,
        )
        if hasattr(state, "tool_selection_history"):
            state.tool_selection_history.append(record)

        return selected_tool, candidates, False, None, thought, goal

    def _determine_goal(self, tool_name: str, step: int, phase: str,
                        event_types: list[str], state: Any) -> str:
        """Constructs descriptive, standardized goal names for backwards-compatibility."""
        if step == 1:
            if tool_name == "financial_velocity":
                return "Primary Anomaly Triage: Financial Velocity"
            elif tool_name == "milestone_audit":
                return "Primary Anomaly Triage: Milestone Audit"
            elif tool_name == "project_history":
                return "Primary Anomaly Triage: Project History"
            else:
                return f"Primary Anomaly Triage: {tool_name.replace('_', ' ').title()}"

        if tool_name == "financial_velocity":
            return "Cross-Verification: Financial Velocity Audit"
        elif tool_name == "milestone_audit":
            return "Cross-Verification: Milestone Timeline Slippage"
        elif tool_name == "peer_intelligence":
            return "Contextual Peer & Agency Benchmarking"
        elif tool_name == "memory_retrieval":
            return "Precedent Learning: Memory Retrieval"
        elif tool_name == "project_history":
            if getattr(state, "contradictions", []):
                return "Disambiguation: Project History Analysis"
            return "Historical Trajectory Analysis"
        elif tool_name == "shap_attribution":
            return "Explainability: SHAP Feature Attribution"
        return f"Investigation Step: {tool_name.replace('_', ' ').title()}"
