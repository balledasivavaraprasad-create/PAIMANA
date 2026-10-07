"""Supervisor Agent & Stateful Dynamic Investigation Engine.

Canonical Authoritative Investigation Pipeline:
  event → evidence → hypothesis → causal reasoning → tool → convergence → recommendation

Authoritative Subsystems & Canonical Objects:
  1. Monitoring & Events   -> Event detection, severity classification, trigger filtering.
  2. Investigation State   -> paimana_agent.state.InvestigationState (canonical state accumulator)
  3. Budget Governance     -> paimana_agent.governance.budget.models.InvestigationBudget (canonical budget)
  4. Evidence Ingestion    -> paimana_agent.evidence.model.Evidence (canonical evidence unit)
  5. Hypothesis Tracking   -> paimana_agent.hypotheses.model.Hypothesis (canonical hypothesis)
  6. Causal Reasoning      -> paimana_agent.causal.models.CausalClaim (canonical causal claim)
  7. Tool Selection        -> paimana_agent.investigation.selector.DynamicInformationSeekingSelector
  8. Tool Execution        -> paimana_agent.reliability.models.ToolResult (canonical execution result)
  9. Convergence Detection -> paimana_agent.investigation.convergence.ConvergenceEngine
 10. Recommendations       -> paimana_agent.recommendations.candidate.RecommendationCandidate (canonical candidate)
 11. Institutional Memory  -> paimana_agent.memory.models.Precedent (canonical precedent record)
"""
from __future__ import annotations
import json
import logging
import math
import time
import urllib.request
from typing import Any, Optional

from .store import Store
from .tracer import AgentTracer
from .state import (
    InvestigationState, Fact, Inference, Hypothesis, Contradiction,
    RecommendationCandidate, ToolExecutionRecord, Evidence
)
from .tools import ToolRegistry, ToolResult
from .evidence import (
    EvidenceNormalizer, ExplanatoryCoverageEvaluator,
    EvidenceConfidenceEngine, GroundedConfidenceResult
)
from .hypotheses import HypothesisManager, HypothesisGenerator, HypothesisValidator, HypothesisScorer
from .recommendations import (
    RecommendationCandidate, CandidateGenerator, CandidateValidator,
    CandidateDeduplicator, CandidateScorer, RankingPolicy,
    pareto_filter, RecommendationSelector, RecommendationDecision,
    RecommendationGenerator, RecommendationValidator, RecommendationScorer
)
from .investigation import (
    EvidenceNeed, ToolCandidate, ToolSelectionRecord,
    EvidenceGapAnalyzer, HypothesisDiscriminator, ToolUtilityEvaluator,
    InvestigationBudget, InvestigationPhase, ConvergenceDetector,
    DynamicInformationSeekingSelector
)

logger = logging.getLogger("paimana_agent.supervisor")


class LLMSupervisorPlanner:
    """[OPTIONAL LLM PLANNER] High-level LLM planner that inspects evidence gaps and selects tools.

    Falls back to DynamicInformationSeekingSelector when unavailable or unconfigured.
    """

    def __init__(self, llm_cfg: Optional[dict] = None):
        self.cfg = llm_cfg or {}
        self.enabled = bool(self.cfg.get("enabled", False))
        self.url = self.cfg.get("url", "http://localhost:11434/api/generate")
        self.model = self.cfg.get("model", "llama3.1:8b")
        self.timeout = float(self.cfg.get("timeout", 15))

    def plan_next_step(self, state: InvestigationState, tools_info: list[dict],
                       budget_left: int) -> Optional[tuple[str, str, str, bool, Optional[str]]]:
        """Queries LLM for next tool decision. Returns None if disabled or failed."""
        if not self.enabled:
            return None

        prompt = self._build_prompt(state, tools_info, budget_left)
        try:
            req_data = json.dumps({
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "format": "json"
            }).encode("utf-8")
            req = urllib.request.Request(self.url, data=req_data, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                raw = json.loads(resp.read().decode("utf-8"))
                content = raw.get("response", "{}")
                decision = json.loads(content)
                action = decision.get("action", "").upper()
                thought = decision.get("thought", "LLM reasoning plan")
                goal = decision.get("goal", "Gather discriminating evidence")
                
                if action == "CONCLUDE":
                    return None, thought, goal, True, "SUFFICIENT_EVIDENCE"
                tool_name = decision.get("tool_name")
                if tool_name and tool_name in [t["name"] for t in tools_info]:
                    return tool_name, thought, goal, False, None
        except Exception as ex:
            logger.debug(f"LLM planner unavailable or parse error ({ex}); using dynamic gap planner.")
        return None

    def _build_prompt(self, state: InvestigationState, tools_info: list[dict], budget_left: int) -> str:
        prompt_data = {
            "objective": state.objective,
            "project_code": state.project_code,
            "tools_budget_remaining": budget_left,
            "tools_already_used": state.tools_used,
            "grounded_facts": [f.to_dict() for f in state.facts],
            "evidence_items": [e.to_dict() for e in state.evidence_items],
            "unexplained_evidence": [e.to_dict() for e in state.unexplained_evidence],
            "active_evidence_gaps": state.evidence_gaps,
            "competing_hypotheses": [h.to_dict() for h in state.hypotheses],
            "contradictions": [c.to_dict() for c in state.contradictions],
            "relational_evidence_graph": state.evidence_graph,
            "available_tools": tools_info,
        }
        return (
            "You are the Lead Project Monitoring Supervisor Agent for MoSPI infrastructure projects.\n"
            "Your task is to conduct an evidence-driven, causal investigation. You must answer four questions:\n"
            "1. Grounded Observations ('What do we know?'): Inspect established facts and tool outputs.\n"
            "2. Active Gaps ('What don't we know?'): Identify missing data required to evaluate root cause.\n"
            "3. Discrimination ('What would change our mind?'): Evaluate falsification conditions and discriminating evidence for competing hypotheses.\n"
            "4. Optimal Action: Select the single most discriminating tool to resolve the dominant evidence gap or distinguish top hypotheses, or CONCLUDE if evidence is sufficient.\n"
            "Output JSON with keys: 'action' ('EXECUTE_TOOL' or 'CONCLUDE'), 'tool_name', 'thought', 'goal', 'target_evidence_gap'.\n"
            f"Context: {json.dumps(prompt_data)}"
        )


class DynamicEvidenceGapPlanner:
    """[LEGACY FALLBACK PLANNER] Deterministic rule-based evidence-gap planner.

    NOTE: Marked as legacy fallback. Canonical tool selection is performed by
    DynamicInformationSeekingSelector, which evaluates information gain,
    evidence gaps, and tool reliability profiles.
    """

    def plan_next_step(self, state: InvestigationState, p: dict, feats: dict,
                       event_types: list[str]) -> tuple[Optional[str], str, str, bool, Optional[str]]:
        used = set(state.tools_used)
        fin_obs = state.observations.get("financial_velocity")
        mile_obs = state.observations.get("milestone_audit")
        hist_obs = state.observations.get("project_history")

        # Step 1: Initial anomaly triage if no tools used yet
        if not used:
            if "COST_PROGRESS_MISMATCH" in event_types or feats.get("progress_expenditure_gap_pct", 0) > 15:
                return (
                    "financial_velocity",
                    "Trigger indicates severe cost-progress mismatch. Dynamically selecting financial velocity tool to audit spend vs physical progress.",
                    "Primary Anomaly Triage: Financial Velocity",
                    False,
                    None
                )
            elif "MILESTONE_DELAYED" in event_types or "PROGRESS_STALLED" in event_types:
                return (
                    "milestone_audit",
                    "Trigger indicates schedule slippage or stalling. Dynamically selecting milestone audit tool to evaluate timeline.",
                    "Primary Anomaly Triage: Milestone Audit",
                    False,
                    None
                )
            elif "RISK_ACCELERATING" in event_types:
                return (
                    "project_history",
                    "Trigger indicates rapid risk score acceleration. Dynamically selecting project history tool to inspect trajectory.",
                    "Primary Anomaly Triage: Project History",
                    False,
                    None
                )
            else:
                return (
                    "financial_velocity",
                    "No specific trigger anomaly indicated. Starting baseline financial velocity audit.",
                    "Baseline Anomaly Triage",
                    False,
                    None
                )

        # Step 2: Cross-Verification between physical and financial reality
        if fin_obs and "milestone_audit" not in used:
            gap = fin_obs.get("progress_expenditure_gap_pct", 0.0)
            return (
                "milestone_audit",
                f"Financial audit observed a {gap:.1f}% spend lead. Now probing milestone timeline to determine whether civil delays accompany the financial gap.",
                "Cross-Verification: Milestone Timeline Slippage",
                False,
                None
            )

        if mile_obs and "financial_velocity" not in used:
            slip = mile_obs.get("schedule_slippage_months", 0.0)
            return (
                "financial_velocity",
                f"Milestone audit observed {slip:.0f} months slippage. Probing financial velocity to evaluate expenditure rate.",
                "Cross-Verification: Financial Velocity Audit",
                False,
                None
            )

        # Step 3: Peer Cohort & Implementing Agency Baseline
        if "peer_intelligence" not in used:
            return (
                "peer_intelligence",
                "Benchmarking project metrics against comparable peer cohort (sector, cost scale, stage, and implementing agency).",
                "Contextual Peer & Agency Benchmarking",
                False,
                None
            )

        # Step 4: Closed-Loop Precedent Learning Retrieval
        if "memory_retrieval" not in used and state.hypotheses:
            return (
                "memory_retrieval",
                "Primary hypothesis established. Querying project memory learning loop for precedent intervention outcomes.",
                "Precedent Learning: Memory Retrieval",
                False,
                None
            )

        # Step 5: Disambiguate Contradictions via History
        if state.contradictions and "project_history" not in used:
            return (
                "project_history",
                "Contradiction detected between progress rate and schedule milestone. Probing project history to analyze multi-month trajectory.",
                "Disambiguation: Project History Analysis",
                False,
                None
            )

        # Step 6: Model Explainability
        if "shap_attribution" not in used and feats:
            return (
                "shap_attribution",
                "Executing SHAP permutation attribution to verify model risk contributors.",
                "Explainability: SHAP Feature Attribution",
                False,
                None
            )

        # If all necessary discriminating evidence collected
        return (
            None,
            "Evidence collection complete. Sufficient observations gathered to support findings.",
            "Conclusion",
            True,
            "SUFFICIENT_EVIDENCE"
        )


class SupervisorAgent:
    """Stateful Supervisor Agent that dynamically plans and conducts investigations based on observations."""

    def __init__(self, tool_registry: Optional[ToolRegistry] = None,
                 tracer: Optional[AgentTracer] = None,
                 llm_cfg: Optional[dict] = None):
        self.registry = tool_registry or ToolRegistry()
        self.tracer = tracer or AgentTracer()
        self.llm_planner = LLMSupervisorPlanner(llm_cfg)
        self.gap_planner = DynamicEvidenceGapPlanner()
        self.info_selector = DynamicInformationSeekingSelector()
        self.normalizer = EvidenceNormalizer()
        self.coverage_eval = ExplanatoryCoverageEvaluator()
        self.hypo_manager = HypothesisManager(generator=HypothesisGenerator(llm_cfg))
        self.rec_gen = CandidateGenerator()
        self.rec_val = CandidateValidator()
        self.rec_dedup = CandidateDeduplicator()
        self.rec_scorer = CandidateScorer()
        self.rec_selector = RecommendationSelector()
        self.confidence_engine = EvidenceConfidenceEngine()

    def run_investigation(self, store: Store, p: dict, res: dict, drivers: list[str],
                          events: list[dict], model: Any = None, feats: Optional[dict] = None,
                          feature_cols: Optional[list] = None, background: Any = None,
                          event_id: Optional[int] = None, ref_stats: Optional[dict] = None,
                          max_steps: int = 5) -> dict:
        """Executes the stateful investigation loop."""
        code = res["project_code"]
        p_name = res.get("project_name", code)
        event_types = [e["type"] for e in events]
        feats = feats or {}

        objective = f"Diagnose risk drivers and determine optimal intervention for project {code} (triggers: {', '.join(event_types) or 'general review'})"

        # Initialize Risk-Calibrated Budget Policy & Governance Manager
        from .governance.budget import BudgetPolicy, BudgetManager
        severity = "MEDIUM"
        if events:
            severities = [str(e.get("severity", "MEDIUM")).upper() for e in events]
            if "CRITICAL" in severities:
                severity = "CRITICAL"
            elif "HIGH" in severities:
                severity = "HIGH"
            elif "LOW" in severities and len(severities) == 1:
                severity = "LOW"

        budget_policy = BudgetPolicy.for_severity(severity)
        budget = budget_policy.create_budget(investigation_id=f"inv_{code}_{int(time.time())}")
        if max_steps != 5:
            budget.max_tool_calls = max_steps
            budget.max_iterations = max_steps + 2

        budget_mgr = BudgetManager(budget=budget, policy=budget_policy, investigation_id=budget.investigation_id)

        # Initialize State & Dynamic Budget
        state = InvestigationState(
            objective=objective,
            project_code=code,
            project_name=p_name,
            triggering_events=events,
            tool_budget=budget.max_tool_calls,
            investigation_budget=budget,
        )
        state.budget_manager = budget_mgr

        # Initialize Risk-Calibrated Convergence Policy & Detector
        from .investigation.convergence import ConvergencePolicy
        policy = ConvergencePolicy.for_severity(severity)
        state._convergence_detector = ConvergenceDetector(budget=budget, policy=policy)

        # --------------------------------------------------------------------
        # Stage 1: Event & State Initialization
        # --------------------------------------------------------------------
        self.tracer.trace_investigation_start(code, objective, event_types)

        # Baseline Ground-Truth Facts
        state.add_fact(
            statement=f"Sanctioned original cost is Rs {p.get('original_cost_cr', 0):,.1f} Cr; cumulative expenditure is Rs {p.get('cumulative_expenditure_cr', 0):,.1f} Cr.",
            source="CUF Financial Ledger", metric="cumulative_expenditure_cr", value=p.get("cumulative_expenditure_cr")
        )
        state.add_fact(
            statement=f"Certified physical progress is {p.get('physical_progress_pct', 0):.1f}%.",
            source="CUF Monthly Progress Report", metric="physical_progress_pct", value=p.get("physical_progress_pct")
        )
        state.add_fact(
            statement=f"Original completion target was {p.get('original_completion_date')}; current target is {p.get('revised_completion_date') or p.get('original_completion_date')}.",
            source="CUF Milestone Schedule", metric="completion_date", value=p.get("revised_completion_date") or p.get("original_completion_date")
        )

        # --------------------------------------------------------------------
        # Stage 2: Canonical Evidence Ingestion (Baseline Facts Normalization)
        # --------------------------------------------------------------------
        baseline_evidence = self.normalizer.normalize_baseline_facts(p)
        for ev in baseline_evidence:
            state.add_evidence(ev)

        # --------------------------------------------------------------------
        # Stage 3: Competing Hypothesis Tracking (Seeding Initial Causal Models)
        # --------------------------------------------------------------------
        state.hypotheses = self.hypo_manager.seed_initial_hypotheses(event_types, feats, state.evidence_items)

        # Initial Explanatory Coverage Check
        cov = self.coverage_eval.evaluate_coverage(state.evidence_items, state.hypotheses)
        state.unexplained_evidence = cov["unexplained_evidence"]
        state.partially_explained_evidence = cov["partially_explained_evidence"]
        state.contradicted_evidence = cov["contradicted_evidence"]

        # Initialize structured evidence gaps
        state.add_evidence_gap("Verify physical progress vs cumulative expenditure velocity")
        state.add_evidence_gap("Verify milestone slippage and completion revisions")
        state.add_evidence_gap("Benchmark against sector and agency peer baselines")
        state.add_evidence_gap("Query precedent memory for tested intervention outcomes")

        # --------------------------------------------------------------------
        # Stage 4: Initial Causal Reasoning & Mechanism Verification
        # --------------------------------------------------------------------
        self._run_causal_evaluation(state, p, feats, ref_stats)

        # --------------------------------------------------------------------
        # Stage 5: Dynamic Information-Seeking Tool Selection & Convergence Loop
        # --------------------------------------------------------------------
        step = 0
        while step < state.tool_budget:
            step += 1

            # 5a. Information-Seeking Tool Selection & Convergence Evaluation
            next_tool, thought, goal, is_sufficient, stop_reason = self._plan_next_step(state, p, feats, event_types, store=store, model=model)

            if is_sufficient or next_tool is None:
                state.termination_reason = stop_reason or "SUFFICIENT_EVIDENCE"
                state.investigation_steps.append({
                    "step": step,
                    "goal": goal or "Finalize Investigation",
                    "thought": thought,
                    "tool_selected": "conclude",
                    "selected_tools": [],
                    "observation": f"Investigation concluded: {state.termination_reason}",
                    "evidence_sufficiency": "Complete",
                    "is_sufficient": True,
                })
                self.tracer.trace_supervisor_decision(step, thought, None)
                break

            self.tracer.trace_supervisor_decision(step, thought, next_tool)

            # 5b. Tool Resource Reservation & Justified Expansion
            reservation = None
            if hasattr(state, "budget_manager") and state.budget_manager:
                is_emergency = bool(state.contradictions) or (getattr(state, "investigation_phase", "") == "DISCRIMINATION" and len(state.tools_used) >= state.tool_budget - 1)
                reservation = state.budget_manager.reserve(next_tool, is_emergency=is_emergency)
                if reservation is None and state.investigation_budget and not state.investigation_budget.can_afford():
                    # Attempt justified expansion
                    active_h = [h for h in state.hypotheses if getattr(h, "status", "").lower() in ["active", "supported", "primary"]]
                    top_h = active_h[0] if active_h else None
                    top_conf = getattr(top_h, "confidence", 0.5) if top_h else 0.5
                    uncertainty = 1.0 - (float(top_conf) if not isinstance(top_conf, str) else 0.5)
                    cand = next((c for c in getattr(state, "tool_candidates", []) if getattr(c, "tool_name", "") == next_tool), None)
                    gain = getattr(cand, "expected_information_gain", 0.12)
                    
                    exp_req = state.budget_manager.request_budget_expansion(
                        reason=f"Decisive tool '{next_tool}' requires resource envelope expansion under high uncertainty ({uncertainty:.2f}).",
                        requested_resources={"tool_calls": 1, "cost": 0.20, "latency_ms": 3000.0},
                        current_uncertainty=uncertainty,
                        expected_information_gain=gain,
                    )
                    if exp_req.status in ["APPROVED", "EMERGENCY_GRANTED", "PARTIAL"]:
                        state.tool_budget = state.investigation_budget.max_tool_calls
                        reservation = state.budget_manager.reserve(next_tool, is_emergency=True)

            # Tool Execution & Latency Auditing
            tool_args = self._prepare_tool_args(next_tool, store, p, feats, event_types, model, feature_cols, background, drivers, ref_stats)
            t0 = time.time()
            result: ToolResult = self.registry.execute(
                next_tool,
                budget=state.investigation_budget,
                expected_project_code=p.get("project_code"),
                **tool_args
            )
            latency_ms = (time.time() - t0) * 1000.0

            # Tool Resource Settlement
            cost = getattr(result, "execution_cost", 0.05)
            if reservation and hasattr(state, "budget_manager") and state.budget_manager:
                state.budget_manager.settle(
                    reservation_id=reservation.reservation_id,
                    actual_latency_ms=latency_ms,
                    actual_cost=cost,
                    tool_name=next_tool,
                )
            elif state.investigation_budget:
                state.investigation_budget.record_call(latency_ms=latency_ms, cost=cost)

            if result.status != "SUCCESS" and result.status != "PARTIAL_SUCCESS":
                state.add_evidence_gap(f"Tool {next_tool} execution failed: {result.error or result.summary}")

            self.tracer.trace_tool_execution(next_tool, result.status, latency_ms, result.summary, result.error)

            # Record tool execution in rich audit history & state
            call_id = f"exec_{step}_{next_tool}"
            state.record_tool_execution(
                call_id=call_id,
                tool_name=next_tool,
                parameters={k: str(v) for k, v in tool_args.items() if k not in ["store", "model", "background", "ref_stats"]},
                summary=result.summary,
                data=result.data,
                status=result.status,
                latency_ms=latency_ms,
            )

            # 5c. Tool Evidence Normalization & Lineage Tracking
            if getattr(result, "is_usable_evidence", True) and result.is_success:
                new_ev_list = self.normalizer.normalize_tool_result(next_tool, result.data, p, feats)
                if getattr(result, "substitution_metadata", None):
                    disc = result.substitution_metadata.get("authority_discount", 1.0)
                    same_lineage = result.substitution_metadata.get("same_underlying_lineage", False)
                    for ev in new_ev_list:
                        ev.authority_score = round(ev.authority_score * disc, 3)
                        if same_lineage:
                            ev.independence_group_id = f"SUB_{result.substitution_metadata.get('primary_tool')}_{ev.independence_group_id}"
                if getattr(result, "status", "") == "PARTIAL_SUCCESS":
                    comp = getattr(result, "completeness_score", 0.7)
                    for ev in new_ev_list:
                        ev.reliability = round(ev.reliability * comp, 3)
                if getattr(result, "status", "") == "STALE_RESULT":
                    fresh = getattr(result, "freshness_score", 0.5)
                    for ev in new_ev_list:
                        ev.freshness_score = fresh
                for ev in new_ev_list:
                    state.add_evidence(ev)

                # 5d. Observation Inferences, Contradiction Detection & Evidence Relations
                self._process_observation(state, next_tool, result, p, feats)

            # Explanatory Coverage Evaluation
            cov = self.coverage_eval.evaluate_coverage(state.evidence_items, state.hypotheses)
            state.unexplained_evidence = cov["unexplained_evidence"]
            state.partially_explained_evidence = cov["partially_explained_evidence"]
            state.contradicted_evidence = cov["contradicted_evidence"]

            # 5e. Hypothesis Update & Independent Corroboration Scoring
            state.hypotheses = self.hypo_manager.process_iteration(
                hypotheses=state.hypotheses,
                evidence_items=state.evidence_items,
                unexplained_evidence=state.unexplained_evidence,
                has_contradictions=bool(state.contradictions),
                project_context=p,
                iteration=step,
                converged=cov["is_coverage_complete"],
                confidence_history=state.confidence_history
            )
            state.hypothesis_generation_events = list(self.hypo_manager.generation_events)
            state.generated_hypothesis_count = self.hypo_manager._total_generated_count
            state.rejected_hypothesis_count = self.hypo_manager._total_rejected_count

            # Update Hypotheses & Multi-Dimensional Grounded Confidence
            self._update_hypotheses_and_confidence(state, p, feats, ref_stats)

            # 5f. Live Causal Reasoning & Confounder Verification
            self._run_causal_evaluation(state, p, feats, ref_stats)

            # Determine Investigation Outcome
            active_h = [h for h in state.hypotheses if getattr(h, "status", "").lower() in ["active", "supported", "primary"]]
            top_h = active_h[0] if active_h else (state.hypotheses[0] if state.hypotheses else None)
            raw_top_conf = getattr(top_h, "confidence", 0.0) if top_h else 0.0
            if isinstance(raw_top_conf, str):
                top_conf = 0.85 if raw_top_conf.upper() == "HIGH" else (0.50 if raw_top_conf.upper() == "MEDIUM" else 0.20)
            else:
                top_conf = float(raw_top_conf)

            if top_conf >= 0.70 and getattr(top_h, "status", "").lower() in ["supported", "primary"]:
                state.investigation_outcome = "ROOT_CAUSE_SUPPORTED"
            elif top_conf >= 0.45:
                def get_h_conf(hypo):
                    c = getattr(hypo, "confidence", 0.0)
                    return 0.85 if c == "HIGH" else (0.50 if c == "MEDIUM" else (0.20 if c == "LOW" else float(c)))
                if len(active_h) >= 2 and abs(get_h_conf(active_h[0]) - get_h_conf(active_h[1])) < 0.10:
                    state.investigation_outcome = "MULTIPLE_PLAUSIBLE_CAUSES"
                else:
                    state.investigation_outcome = "ROOT_CAUSE_PARTIALLY_SUPPORTED"
            elif state.contradictions:
                state.investigation_outcome = "CONTRADICTORY_EVIDENCE"
            else:
                state.investigation_outcome = "INSUFFICIENT_EVIDENCE"

            state.investigation_steps.append({
                "step": step,
                "goal": goal,
                "thought": thought,
                "tool_selected": f"tool_{next_tool}",
                "selected_tools": [f"tool_{next_tool}", next_tool],
                "observation": result.summary,
                "evidence_sufficiency": "Sufficient" if state.confidence_score >= 0.7 else "Preliminary (requires further evidence)",
                "is_sufficient": state.confidence_score >= 0.7,
            })

            if step >= state.tool_budget and state.termination_reason == "IN_PROGRESS":
                state.termination_reason = "TOOL_LIMIT_REACHED"

        # --------------------------------------------------------------------
        # Stage 6: Final Causal Mechanism Verification
        # --------------------------------------------------------------------
        self._run_causal_evaluation(state, p, feats, ref_stats)

        # --------------------------------------------------------------------
        # Stage 7: Actionable Recommendation Synthesis & Validation
        # --------------------------------------------------------------------
        self._synthesize_and_validate_recommendations(state, p, feats, store)

        # --------------------------------------------------------------------
        # Stage 8: Comprehensive Report Assembly & Closed-Loop Precedent Learning
        # --------------------------------------------------------------------
        report = self._build_final_report(state, res, event_id, store)
        return report

    def _init_competing_hypotheses(self, state: InvestigationState, event_types: list[str], feats: dict):
        """Initializes the 4 competing causal hypotheses (delegates to hypothesis manager)."""
        state.hypotheses = self.hypo_manager.seed_initial_hypotheses(event_types, feats, state.evidence_items)

    def _plan_next_step(self, state: InvestigationState, p: dict, feats: dict,
                        event_types: list[str], store: Optional[Store] = None,
                        model: Any = None) -> tuple[Optional[str], str, str, bool, Optional[str]]:
        """Dual-mode planner: attempts LLM planning first, falls back to dynamic information-seeking selector."""
        fn = getattr(self.registry, "export_tools_manifest", getattr(self.registry, "export_mcp_manifest", getattr(self.registry, "list_tools", None)))
        tools_info = fn() if fn else []
        budget_left = state.tool_budget - len(state.tools_used)

        # 1. Attempt LLM-driven planning
        llm_decision = self.llm_planner.plan_next_step(state, tools_info, budget_left)
        if llm_decision is not None:
            return llm_decision

        # 2. Dynamic uncertainty-driven information-seeking selector
        if hasattr(self, "info_selector"):
            selected_tool, candidates, is_term, stop_reason, thought, goal = self.info_selector.select_next_step(
                state=state, p=p, feats=feats, event_types=event_types,
                registry=self.registry, budget=state.investigation_budget,
                caller_authorization="read_only", store=store, model=model
            )
            return selected_tool, thought, goal, is_term, stop_reason

        # 3. Intelligent evidence-gap driven planning fallback
        return self.gap_planner.plan_next_step(state, p, feats, event_types)

    def _prepare_tool_args(self, tool_name: str, store: Store, p: dict, feats: dict,
                           event_types: list[str], model: Any, feature_cols: Optional[list],
                           background: Any, drivers: list[str], ref_stats: Optional[dict]) -> dict:
        if tool_name == "financial_velocity":
            return {"p": p, "feats": feats}
        elif tool_name == "milestone_audit":
            return {"p": p, "feats": feats}
        elif tool_name == "project_history":
            return {"store": store, "project_code": p.get("project_code", "")}
        elif tool_name == "peer_intelligence" or tool_name.startswith("peer_") or tool_name in ["cohort_intelligence", "statistical_benchmark", "detect_peer_anomalies", "analyze_trajectory_intelligence", "analyze_domain_context"]:
            return {
                "p": p,
                "store": store,
                "project_code": p.get("project_code", ""),
                "sector": p.get("sector", "Unknown"),
                "original_cost_cr": float(p.get("original_cost_cr", 0.0)),
                "physical_progress_pct": float(p.get("physical_progress_pct", 0.0)),
                "implementing_agency": p.get("implementing_agency", ""),
                "ref_stats": ref_stats,
            }
        elif tool_name == "memory_retrieval":
            return {"store": store, "project_code": p.get("project_code", ""), "triggering_event_types": event_types}
        elif tool_name == "shap_attribution":
            return {"model": model, "feats": feats, "feature_cols": feature_cols, "background": background, "rule_drivers": drivers}
        return {}

    def _process_observation(self, state: InvestigationState, tool_name: str,
                             result: ToolResult, p: dict, feats: dict):
        """Extracts facts, inferences, decision traces, resolves evidence gaps, and detects contradictions."""
        data = result.data or {}

        if tool_name == "financial_velocity":
            state.resolve_evidence_gap("Verify physical progress vs cumulative expenditure velocity")
            gap = data.get("progress_expenditure_gap_pct", 0.0)
            if gap > 15.0:
                state.add_inference(
                    statement=f"Cumulative expenditure is {gap:.1f} percentage points ahead of certified physical progress.",
                    derived_from=["cumulative_expenditure_cr", "physical_progress_pct"],
                    significance="High financial decoupling / potential uncertified disbursement"
                )
                state.decision_trace.append({
                    "finding": "Progress-Expenditure Decoupling",
                    "evidence_source": "Financial Velocity Audit",
                    "metric_value": f"{gap:.1f}% gap ({p.get('physical_progress_pct', 0):.0f}% progress vs spend)",
                    "threshold_or_baseline": "> 15.0% threshold"
                })
                state.add_evidence_relation("tool:financial_velocity", "SUPPORTS", "hypothesis:front_loaded_billing", weight=0.85)
                state.add_evidence_relation("tool:financial_velocity", "WEAKENS", "hypothesis:reporting_discrepancy", weight=0.50)
            else:
                state.add_evidence_relation("tool:financial_velocity", "WEAKENS", "hypothesis:front_loaded_billing", weight=0.60)

        elif tool_name == "milestone_audit":
            state.resolve_evidence_gap("Verify milestone slippage and completion revisions")
            slip = data.get("schedule_slippage_months", 0.0)
            ratio = data.get("age_to_planned_ratio")
            if slip > 0:
                state.add_inference(
                    statement=f"Completion schedule has slipped by {slip:.0f} months against original approved timeline.",
                    derived_from=["original_completion_date", "revised_completion_date"],
                    significance="Schedule delay / contractor mobilization bottleneck"
                )
                state.decision_trace.append({
                    "finding": "Schedule Target Slippage",
                    "evidence_source": "Milestone Audit",
                    "metric_value": f"{slip:.0f} months slipped",
                    "threshold_or_baseline": f"Original target: {p.get('original_completion_date')}"
                })
                state.add_evidence_relation("tool:milestone_audit", "SUPPORTS", "hypothesis:chronic_schedule_delay", weight=0.85)
            if ratio and ratio > 1.0:
                state.add_inference(
                    statement=f"Project age ({ratio*100:.0f}%) exceeds sanctioned planned lifespan.",
                    derived_from=["project_age_months", "planned_duration_months"],
                    significance="Time budget exhausted"
                )
                state.add_evidence_relation("tool:milestone_audit", "SUPPORTS", "hypothesis:chronic_schedule_delay", weight=0.75)

            # Contradiction Detection: Milestone report says 0 slip, but physical progress is stalled (<20% on an aged project)
            if slip == 0 and ratio and ratio > 0.8 and p.get("physical_progress_pct", 0) < 20:
                c = state.add_contradiction(
                    metric="schedule_progress_alignment",
                    src_a="Milestone Schedule (reported 0 slippage)",
                    val_a="0 months delay",
                    src_b="Physical Progress MPR (stalled at <20% after 80% duration)",
                    val_b=f"{p.get('physical_progress_pct', 0)}% progress",
                    impact="Milestone dates appear unrevised despite severe on-site construction delays"
                )
                self.tracer.trace_contradiction(c.to_dict())
                state.add_evidence_relation("tool:milestone_audit", "CONTRADICTS", "data:milestone_schedule", weight=0.90)
                state.add_evidence_relation("tool:milestone_audit", "SUPPORTS", "hypothesis:reporting_discrepancy", weight=0.80)

        elif tool_name == "peer_intelligence" or tool_name.startswith("peer_"):
            state.resolve_evidence_gap("Benchmark against sector and agency peer baselines")
            note = data.get("note") or result.summary or data.get("summary") or "Peer cohort benchmarked."
            state.add_inference(
                statement=f"Peer benchmarking indicates: {note}",
                derived_from=["peer_cohort", "sector_baseline"],
                significance="Peer cohort comparative context"
            )
            state.decision_trace.append({
                "finding": "Peer Cohort Benchmark",
                "evidence_source": "Peer Intelligence Tool",
                "metric_value": note,
                "threshold_or_baseline": f"{data.get('sector', p.get('sector', 'Unknown'))} {data.get('stage_bracket', 'cohort')}"
            })
            state.add_evidence_relation(f"tool:{tool_name}", "CONTEXTUALIZES", "hypothesis:chronic_schedule_delay", weight=0.60)

        elif tool_name == "memory_retrieval":
            state.resolve_evidence_gap("Query precedent memory for tested intervention outcomes")
            succ = data.get("successful_precedents", [])
            state.retrieved_precedents = data.get("supporting_precedents", [])
            state.retrieved_counterexamples = data.get("counterexamples", [])
            state.retrieved_failures = data.get("failed_precedents", [])
            state.policy_constraints = data.get("policy_constraints", [])
            state.precedent_bundle = data.get("precedent_bundle")

            for cx in state.retrieved_counterexamples:
                state.memory_decision_trace.append({
                    "type": "COUNTEREXAMPLE_NOTED",
                    "id": cx.get("id"),
                    "note": cx.get("why_relevant", "")
                })

            if succ:
                state.decision_trace.append({
                    "finding": "Historical Precedent Success",
                    "evidence_source": "Project Memory Learning Loop",
                    "metric_value": succ[0].get("outcome", ""),
                    "threshold_or_baseline": f"Project {succ[0].get('project_code')}"
                })
                target_h = "hypothesis:front_loaded_billing" if any("billing" in h.name for h in state.hypotheses if h.status == "PRIMARY") else "hypothesis:chronic_schedule_delay"
                state.add_evidence_relation("tool:memory_retrieval", "SUPPORTS", target_h, weight=0.80)

        elif tool_name == "shap_attribution":
            state.resolve_evidence_gap("SHAP model attribution for ML risk escalation")
            lines = data.get("shap_lines", [])
            for line in lines[:2]:
                state.decision_trace.append({
                    "finding": "Key Model Feature Impact (SHAP)",
                    "evidence_source": "SHAP permutation attribution (model-agnostic)",
                    "metric_value": line,
                    "threshold_or_baseline": "Statistically significant risk contributor"
                })
            state.add_evidence_relation("tool:shap_attribution", "EXPLAINS", "model:risk_score", weight=0.75)

    def _update_hypotheses_and_confidence(self, state: InvestigationState, p: dict, feats: dict, ref_stats: Optional[dict]):
        """[CANONICAL HYPOTHESIS SCORING & GROUNDED CONFIDENCE AGGREGATOR]
        
        Evaluates hypotheses strictly using the canonical HypothesisScorer across independent
        evidence groups, contradiction falsifications, and Bayesian posterior distributions.
        Removes conflicting legacy supervisor-level heuristic overrides.
        """
        # 1. Synchronize relational evidence graph to structured evidence items
        for edge in getattr(state, "evidence_graph", []):
            src = edge.get("source", "")
            rel = edge.get("relation", "")
            tgt = edge.get("target", "").replace("hypothesis:", "")
            tool_name = src.replace("tool:", "")
            for ev in state.evidence_items:
                if ev.source_tool == tool_name or ev.source_id == tool_name:
                    if rel in ("SUPPORTS", "CONFIRMS") and tgt not in ev.supports_hypotheses:
                        ev.supports_hypotheses.append(tgt)
                    elif rel in ("WEAKENS", "CONTRADICTS") and tgt not in ev.contradicts_hypotheses:
                        ev.contradicts_hypotheses.append(tgt)

        # 2. Canonical Hypothesis Scoring & State Transitions
        self.hypo_manager.scorer.score_and_transition(
            hypotheses=state.hypotheses,
            evidence_items=state.evidence_items,
            iteration=len(state.investigation_steps),
            confidence_history=state.confidence_history
        )

        self.tracer.trace_hypothesis_update([h.to_dict() for h in state.hypotheses])

        # --------------------------------------------------------------------
        # Multi-Dimensional Grounded Confidence Calculation (Canonical Engine)
        # --------------------------------------------------------------------
        old_conf = state.evidence_confidence
        mem = state.observations.get("memory_retrieval", {})
        conf_result = self.confidence_engine.evaluate(
            evidence_items=state.evidence_items,
            facts=state.facts,
            inferences=state.inferences,
            hypotheses=state.hypotheses,
            contradictions=state.contradictions,
            evidence_groups=state.evidence_groups,
            source_lineage=state.source_lineage,
            precedent_data=mem,
            evidence_gaps=state.evidence_gaps,
            observations=state.observations,
        )

        state.root_cause_confidence = conf_result.root_cause_confidence
        state.recommendation_confidence = conf_result.recommendation_confidence
        state.confidence_score = conf_result.total_confidence
        state.evidence_confidence = conf_result.confidence_tier
        state.confidence_reasons = conf_result.confidence_reasons
        state.confidence_breakdown = conf_result.confidence_breakdown

        # Resource Governance: Graceful Degradation Confidence Coupling
        if hasattr(state, "investigation_budget") and state.investigation_budget:
            from .governance.budget import GracefulDegradationManager
            tier = GracefulDegradationManager.evaluate_tier(state.investigation_budget)
            state.degradation_level = tier.value
            cov_score = getattr(getattr(state, "convergence_state", None), "evidence_coverage", 0.70)
            coup = GracefulDegradationManager.apply_confidence_coupling(
                tier=tier,
                raw_confidence=state.confidence_score,
                evidence_coverage=cov_score,
            )
            state.confidence_score = coup["adjusted_confidence"]
            for cav in coup.get("caveats", []):
                if cav not in state.confidence_reasons:
                    state.confidence_reasons.append(cav)

        if old_conf != conf_result.confidence_tier:
            self.tracer.trace_confidence_update(old_conf, conf_result.confidence_tier, conf_result.total_confidence, conf_result.confidence_reasons)

    def _synthesize_and_validate_recommendations(self, state: InvestigationState, p: dict, feats: dict, store: Store):
        """Generates candidate recommendations and selects winner through constrained multi-criteria ranking."""
        cost = float(p.get("original_cost_cr", 0.0))
        is_mega = cost >= 1000.0 or feats.get("is_mega_project", False)
        mem = state.observations.get("memory_retrieval", {})
        succ = mem.get("successful_precedents", [])
        unsucc = mem.get("unsuccessful_precedents", []) or mem.get("failed_precedents", [])

        # 1. Dynamically generate candidates across 5 sources
        candidates = self.rec_gen.generate_candidates(
            investigation_state=state,
            leading_hypotheses=state.hypotheses,
            investigation_outcome=state.investigation_outcome,
            project=p,
            feats=feats,
            precedents=mem
        )

        # 2. Deduplicate near-identical candidates
        candidates = self.rec_dedup.deduplicate(candidates)

        # 3. Pre-scoring validation gates (evidence exists, hypothesis alignment, authority, precedent failure)
        validated_candidates = self.rec_val.validate_all(
            candidates=candidates,
            state=state,
            unsuccessful_precedents=unsucc,
            is_mega_project=is_mega
        )

        # 4. Multi-Criteria Scoring across 5 dimensions
        policy_class = "financial" if ("billing" in str(state.triggering_events) or "cost_progress" in str(state.triggering_events)) else ("escalation" if is_mega else "standard")
        policy = RankingPolicy.get_policy(policy_class)

        scored_candidates = self.rec_scorer.score_all(
            candidates=validated_candidates,
            state=state,
            policy=policy,
            is_mega_project=is_mega
        )

        # 5. Pareto Filtering to eliminate strictly dominated candidates
        frontier, dominated = pareto_filter(scored_candidates)

        # 6. Constrained Selection & Deterministic Explanation Generation
        decision = self.rec_selector.select(
            frontier_candidates=frontier,
            all_candidates=candidates,
            state=state,
            policy=policy
        )

        for cand in candidates:
            self.tracer.trace_validation(cand.action, cand.validated, cand.validation_reasons)

        state.candidate_recommendations = candidates
        state.selected_recommendation = decision.selected_candidate or (validated_candidates[0] if validated_candidates else (candidates[-1] if candidates else None))
        state.recommendation_alternatives = decision.alternatives
        state.recommendation_decision = decision

        # 7. Phase 12 Governance Lockdown: Prepare formal human approval request (investigate ≠ recommend ≠ approve ≠ execute)
        if state.selected_recommendation:
            from .governance.approval import ApprovalEngine
            app_engine = ApprovalEngine()
            state.governance_approval_request = app_engine.create_request_from_recommendation(
                candidate=state.selected_recommendation,
                project=p,
                state=state
            )

    def _run_causal_evaluation(self, state: InvestigationState, p: dict, feats: dict, ref_stats: Optional[dict]):
        """Evaluates competing causal mechanisms, checks temporal precedence and confounders, and assigns Causal Claim Levels."""
        from .causal import CausalEngine, CausalTraceBuilder

        observed_effect = "Schedule and Progress Deterioration"
        if state.triggering_events:
            first_ev = state.triggering_events[0]
            observed_effect = first_ev.get("message") or first_ev.get("type") or observed_effect

        # RULE: historical precedent ≠ current intervention evidence
        # Precedents from other projects inform recommendation_confidence, NOT current causal proof
        current_interventions = state.observations.get("project_history", {}).get("interventions", [])
        has_current_verified_intervention = any(
            bool(inv.get("outcome")) and "fail" not in str(inv.get("outcome")).lower()
            for inv in current_interventions
        ) if isinstance(current_interventions, list) else False
        is_intervention_verified = has_current_verified_intervention or bool(p.get("current_intervention_verified", False))

        claims = []
        for i, h in enumerate(state.hypotheses):
            h_id = getattr(h, "id", f"Cause-{i+1}")
            statement = getattr(h, "statement", None) or getattr(h, "hypothesis", None) or h_id
            cause_name = f"{h_id}: {statement}" if h_id and not statement.startswith(h_id) else statement
            claim = CausalEngine.evaluate_causal_claim(
                claim_id=f"CAUSAL-CLAIM-{i+1}",
                proposed_cause=cause_name,
                observed_effect=observed_effect,
                observations=state.observations,
                evidence_items=[e.to_dict() if hasattr(e, "to_dict") else dict(e) for e in state.evidence_items],
                cause_timestamp=None,
                effect_timestamp=None,
                peer_data=(
                    state.observations.get("peer_intelligence")
                    or state.observations.get("peer_deviation")
                    or state.observations.get("peer_benchmark")
                    or state.observations.get("detect_peer_anomalies")
                ),
                is_intervention_verified=is_intervention_verified,
                hypothesis_id=h_id
            )
            claims.append(claim)

        top_claim, alt_claims, conclusion_status, rationale = CausalEngine.compare_competing_explanations(claims)

        state.causal_claims = [c.to_dict() for c in claims]
        state.leading_causal_claim = top_claim.to_dict() if top_claim else None
        state.retained_causal_alternatives = [a.to_dict() for a in alt_claims]
        state.causal_conclusion_status = conclusion_status

        # Collect detected confounders across all claims
        all_confounders = []
        for c in claims:
            for conf_name in c.unresolved_confounders:
                if not any(x.get("variable") == conf_name for x in all_confounders):
                    all_confounders.append({
                        "variable": conf_name,
                        "affects_claim": c.proposed_cause,
                        "status": "UNRESOLVED"
                    })
        state.confounders = all_confounders

        # Build auditable causal trace
        trace = CausalTraceBuilder.build_trace(
            investigation_id=str(getattr(state, "investigation_id", f"INV-{state.project_code}")),
            project_code=state.project_code,
            effect=observed_effect,
            claims=claims,
            leading_claim=top_claim,
            alternatives=alt_claims,
            conclusion_status=conclusion_status,
            summary_rationale=rationale
        )
        state.causal_decision_trace = trace

    def _build_final_report(self, state: InvestigationState, res: dict, event_id: Optional[int], store: Store) -> dict:
        """Assembles the final comprehensive, backward-compatible investigation dictionary."""
        code = state.project_code
        primary_hypo = state.hypotheses[0].hypothesis if state.hypotheses else f"Evaluated at {res['tier']} risk."
        selected_rec = state.selected_recommendation or (state.candidate_recommendations[0] if state.candidate_recommendations else None)

        evidence_dict = {
            "history": state.observations.get("project_history", {}),
            "peers": state.observations.get("peer_intelligence", {}),
            "financial": state.observations.get("financial_velocity", {}),
            "milestones": state.observations.get("milestone_audit", {}),
            "shap": state.observations.get("shap_attribution", {}).get("shap_lines", []),
            "learning": state.observations.get("memory_retrieval", {}),
        }

        tools_invoked_formatted = [f"tool_{t}" if not t.startswith("tool_") else t for t in state.tools_used]

        report = {
            "project_code": code,
            "project_name": state.project_name,
            "ts": time.time(),
            "supervisor_goal": state.objective,
            "supervisor_steps": state.investigation_steps,
            "tools_invoked": tools_invoked_formatted,
            "tool_executions": [t.to_dict() for t in state.tool_executions],
            "trigger_events": [e.get("type", str(e)) for e in state.triggering_events],
            "confidence": state.evidence_confidence,
            "confidence_score": round(state.confidence_score, 2),
            "root_cause_confidence": round(state.root_cause_confidence, 2),
            "recommendation_confidence": round(state.recommendation_confidence, 2),
            "confidence_reasons": state.confidence_reasons,
            "confidence_breakdown": {k: round(v, 2) for k, v in state.confidence_breakdown.items()},
            "confidence_reason": f"{state.evidence_confidence.capitalize()} Confidence: " + "; ".join(state.confidence_reasons) + ".",
            "structured_evidence": {
                "facts": [f.to_dict() for f in state.facts],
                "inferences": [i.to_dict() for i in state.inferences],
                "hypotheses": [
                    {**h.to_dict(), "status": "PRIMARY" if (idx == 0 and h.status != "rejected") else h.to_dict()["status"]}
                    for idx, h in enumerate(state.hypotheses)
                ],
            },
            "evidence_items": [e.to_dict() for e in state.evidence_items],
            "evidence_groups": {k: v.to_dict() for k, v in state.evidence_groups.items()},
            "source_lineage": {k: v.to_dict() for k, v in state.source_lineage.items()},
            "confidence_history": [c.to_dict() for c in state.confidence_history],
            "evidence_quality_dashboard": state.get_evidence_quality_dashboard(),
            "unexplained_evidence": [e.to_dict() for e in state.unexplained_evidence],
            "partially_explained_evidence": [e.to_dict() for e in state.partially_explained_evidence],
            "hypothesis_generation_events": state.hypothesis_generation_events,
            "generated_hypothesis_count": state.generated_hypothesis_count,
            "rejected_hypothesis_count": state.rejected_hypothesis_count,
            "investigation_outcome": state.investigation_outcome,
            "contradictions": [c.to_dict() for c in state.contradictions],
            "evidence_gaps": state.evidence_gaps,
            "evidence_needs": [n.to_dict() for n in getattr(state, "evidence_needs", [])],
            "tool_candidates": [c.to_dict() for c in getattr(state, "tool_candidates", [])],
            "tool_selection_history": [s.to_dict() for s in getattr(state, "tool_selection_history", [])],
            "investigation_phase": getattr(state, "investigation_phase", "ORIENTATION"),
            "investigation_budget": state.investigation_budget.to_dict() if getattr(state, "investigation_budget", None) else None,
            "evidence_graph": state.evidence_graph,
            "termination_reason": state.termination_reason,
            "evidence": evidence_dict,
            "decision_trace": state.decision_trace,
            "root_cause_hypothesis": primary_hypo,
            "root_cause": primary_hypo,
            "candidate_recommendations": [c.to_dict() for c in state.candidate_recommendations],
            "selected_recommendation": selected_rec.to_dict() if selected_rec else None,
            "recommendation_alternatives": [c.to_dict() for c in state.recommendation_alternatives],
            "recommendation_decision": state.recommendation_decision.to_dict() if state.recommendation_decision else None,
            "recommendation": selected_rec.action if selected_rec else "Conduct comprehensive baseline review.",
            "recommendation_details": {
                "action": selected_rec.action if selected_rec else "Conduct comprehensive baseline review.",
                "responsible_stakeholder": selected_rec.responsible_stakeholder if selected_rec else "PMU",
                "urgency": selected_rec.urgency if selected_rec else "MEDIUM",
                "justification": selected_rec.justification if selected_rec else "Composite risk elevated.",
                "candidate_type": selected_rec.candidate_type if selected_rec else "BASELINE_REVIEW",
                "tradeoffs": selected_rec.tradeoffs if selected_rec else "",
                "risks": selected_rec.risks if selected_rec else "",
                "uncertainty": selected_rec.uncertainty if selected_rec else "MEDIUM",
                "precedent_outcome": selected_rec.precedent_outcome if selected_rec else None,
                "expected_impact": selected_rec.expected_impact if selected_rec else "",
                "validated": selected_rec.validated if selected_rec else True,
            },
            "recommendation_justification": selected_rec.justification if selected_rec else "Composite risk elevated.",
            "retrieved_precedents": state.retrieved_precedents,
            "retrieved_counterexamples": state.retrieved_counterexamples,
            "retrieved_failures": state.retrieved_failures,
            "policy_constraints": state.policy_constraints,
            "memory_decision_trace": state.memory_decision_trace,
            "precedent_bundle": state.precedent_bundle,
            "causal_claims": state.causal_claims,
            "leading_causal_claim": state.leading_causal_claim,
            "retained_causal_alternatives": state.retained_causal_alternatives,
            "causal_conclusion_status": state.causal_conclusion_status,
            "causal_decision_trace": state.causal_decision_trace,
            "causal_claim_level": state.leading_causal_claim.get("causal_level", "LEVEL_0_OBSERVATION") if state.leading_causal_claim else "LEVEL_0_OBSERVATION",
            "causal_support_score": state.leading_causal_claim.get("causal_support_score", 0.0) if state.leading_causal_claim else 0.0,
            "confounders": state.confounders,
            "convergence_state": state.convergence_state.to_dict() if getattr(state, "convergence_state", None) else None,
            "convergence_dashboard": state.get_convergence_dashboard(),
            "termination_record": state.termination_record.to_dict() if getattr(state, "termination_record", None) else None,
            "governance_trace": state.budget_manager.build_trace(termination_reason=state.termination_reason).to_dict() if getattr(state, "budget_manager", None) else None,
            "governance_dashboard": state.get_governance_dashboard(),
            "degradation_level": getattr(state, "degradation_level", "LEVEL_1_NORMAL"),
            "quality_tier": getattr(state, "quality_tier", "TIER_1_FULL"),
            "status": "pending_approval",
            "action_execution_status": "LOCKED_AWAITING_APPROVAL",
            "governance_approval_request": state.governance_approval_request.to_dict() if getattr(state, "governance_approval_request", None) else None,
            "governance_approval_record": state.governance_approval_record.to_dict() if getattr(state, "governance_approval_record", None) else None,
            "governance_execution_record": state.governance_execution_record.to_dict() if getattr(state, "governance_execution_record", None) else None,
        }

        # Record detected issues into project memory
        if store is not None:
            for e in state.triggering_events:
                store.add_issue(code, e.get("message", str(e)))

        # Register candidate precedent into institutional memory
        try:
            from .memory import MemoryConsolidator
            from .tools import _default_precedent_store
            MemoryConsolidator(_default_precedent_store).create_candidate_from_investigation(
                state=state,
                recommendation=report.get("recommendation_details")
            )
        except Exception:
            pass

        # Persist investigation report
        if store is not None:
            inv_id = store.add_investigation(code, event_id, report)
            report["id"] = inv_id
        else:
            report["id"] = None
        return report
