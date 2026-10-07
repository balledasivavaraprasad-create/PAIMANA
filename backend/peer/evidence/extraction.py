"""Subsystem Evidence Extraction & Normalization Adapter (ESS-01).

Converts heterogeneous outputs from financial tools, milestone audits, peer benchmarking,
domain analysis, and ML explainers into canonical standardized Evidence objects.
"""
from __future__ import annotations

import time
from typing import Any, Dict, List, Optional, Tuple, Union

from .provenance import ProvenanceTracker
from .reliability import ReliabilityEvaluator
from .schemas import Evidence, ReliabilityTier


class EvidenceExtractor:
    """Adapts raw analytical tool results into standardized Evidence objects."""

    def __init__(
        self,
        provenance_tracker: Optional[ProvenanceTracker] = None,
        reliability_evaluator: Optional[ReliabilityEvaluator] = None,
    ):
        self.provenance_tracker = provenance_tracker or ProvenanceTracker()
        self.reliability_evaluator = reliability_evaluator or ReliabilityEvaluator()

    @staticmethod
    def _resolve_project(project: Union[str, Dict[str, Any]]) -> Tuple[str, Dict[str, Any]]:
        if isinstance(project, str):
            return project, {"project_code": project, "code": project}
        p_id = str(project.get("project_code") or project.get("code") or project.get("project_id") or "UNKNOWN")
        return p_id, project

    def extract_from_financial_velocity(
        self,
        project_data: Union[str, Dict[str, Any]],
        tool_result: Dict[str, Any],
    ) -> List[Evidence]:
        p_id, p_dict = self._resolve_project(project_data)
        data = tool_result.get("data") or tool_result
        ev_items: List[Evidence] = []

        # 1. Cost-Progress Mismatch Evidence
        gap = float(data.get("cost_progress_gap_pct") or data.get("progress_expenditure_gap_pct") or 0.0)
        has_mismatch = bool(data.get("cost_progress_mismatch") or gap > 10.0)
        if has_mismatch or gap > 0:
            prov = self.provenance_tracker.build_provenance(
                source="CUF Financial Ledger & MPR",
                source_id="financial_velocity",
                project_id=p_id,
                tool_name="financial_velocity",
                raw_inputs=data,
                calculation_method="progress_expenditure_gap_percentage",
            )
            rel = self.reliability_evaluator.evaluate(
                source_name="financial_velocity",
                provenance=prov,
                methodology="deterministic_gap_calculation",
            )
            eid = f"EV_FIN_GAP_{p_id}_{int(time.time() * 1000) % 10000}"
            obs = f"Expenditure leads physical execution by {gap:.1f} percentage points."
            ev_items.append(
                Evidence(
                    evidence_id=eid,
                    project_id=p_id,
                    evidence_type="COST_PROGRESS_MISMATCH",
                    source_type="FINANCIAL_TOOL",
                    source_id="financial_velocity",
                    observation=obs,
                    value=gap,
                    unit="percentage_points",
                    as_of_date=str(p_dict.get("report_month") or ""),
                    methodology="expenditure_vs_physical_progress_differential",
                    provenance=prov,
                    reliability=rel,
                    limitations=["Physical progress reported at aggregate project level", "No package-level invoice breakdown"],
                    semantic_status=rel.overall_tier,
                )
            )

        # 2. Cumulative Spend Evidence
        spend_pct = data.get("cost_consumed_pct") or data.get("expenditure_pct")
        if spend_pct is not None:
            spend_val = float(spend_pct)
            prov_spend = self.provenance_tracker.build_provenance(
                source="CUF Financial Ledger",
                source_id="financial_velocity",
                project_id=p_id,
                tool_name="financial_velocity",
                raw_inputs={"cost_consumed_pct": spend_val},
                calculation_method="sanctioned_cost_expenditure_percentage",
            )
            rel_spend = self.reliability_evaluator.evaluate(
                source_name="financial_velocity",
                provenance=prov_spend,
                methodology="ledger_expenditure_ratio",
            )
            eid_spend = f"EV_FIN_SPEND_{p_id}_{int(time.time() * 1000) % 10000}"
            ev_items.append(
                Evidence(
                    evidence_id=eid_spend,
                    project_id=p_id,
                    evidence_type="FINANCIAL_EXPENDITURE",
                    source_type="FINANCIAL_TOOL",
                    source_id="financial_velocity",
                    observation=f"Cumulative financial expenditure reached {spend_val:.1f}% of sanctioned cost.",
                    value=spend_val,
                    unit="percentage",
                    as_of_date=str(p_dict.get("report_month") or ""),
                    methodology="cumulative_expenditure_over_sanctioned_cost",
                    provenance=prov_spend,
                    reliability=rel_spend,
                    semantic_status=rel_spend.overall_tier,
                )
            )

        # 3. Physical Progress Evidence
        prog = data.get("physical_progress_pct")
        if prog is not None:
            prog_val = float(prog)
            prov_prog = self.provenance_tracker.build_provenance(
                source="Monthly Progress Report",
                source_id="financial_velocity",
                project_id=p_id,
                tool_name="financial_velocity",
                raw_inputs={"physical_progress_pct": prog_val},
                calculation_method="weighted_physical_completion_percentage",
            )
            rel_prog = self.reliability_evaluator.evaluate(
                source_name="Monthly Progress Report",
                provenance=prov_prog,
                methodology="engineering_weightage_survey",
            )
            eid_prog = f"EV_PROG_{p_id}_{int(time.time() * 1000) % 10000}"
            ev_items.append(
                Evidence(
                    evidence_id=eid_prog,
                    project_id=p_id,
                    evidence_type="PHYSICAL_PROGRESS",
                    source_type="PROGRESS_REPORT",
                    source_id="financial_velocity",
                    observation=f"Overall physical progress certified at {prog_val:.1f}%.",
                    value=prog_val,
                    unit="percentage",
                    as_of_date=str(p_dict.get("report_month") or ""),
                    methodology="site_measurement_weightage",
                    provenance=prov_prog,
                    reliability=rel_prog,
                    semantic_status=rel_prog.overall_tier,
                )
            )

        return ev_items

    def extract_from_milestone_audit(
        self,
        project_data: Union[str, Dict[str, Any]],
        tool_result: Dict[str, Any],
    ) -> List[Evidence]:
        p_id, p_dict = self._resolve_project(project_data)
        data = tool_result.get("data") or tool_result
        slip = float(data.get("schedule_slippage_months") or p_dict.get("schedule_slippage_months") or 0.0)

        prov = self.provenance_tracker.build_provenance(
            source="CUF Milestone Target Schedule",
            source_id="milestone_audit",
            project_id=p_id,
            tool_name="milestone_audit",
            raw_inputs={"schedule_slippage_months": slip},
            calculation_method="milestone_slippage_months",
        )
        rel = self.reliability_evaluator.evaluate(
            source_name="milestone_audit",
            provenance=prov,
            methodology="calendar_differential",
        )

        eid = f"EV_MLS_{p_id}_{int(time.time() * 1000) % 10000}"
        obs = tool_result.get("summary") or f"Milestone schedule target slippage is {slip:.0f} months."

        ev = Evidence(
            evidence_id=eid,
            project_id=p_id,
            evidence_type="SCHEDULE_SLIPPAGE",
            source_type="MILESTONE_TOOL",
            source_id="milestone_audit",
            observation=obs,
            value=slip,
            unit="months",
            as_of_date=str(p_dict.get("report_month") or ""),
            methodology="sanctioned_vs_revised_completion_date_delta",
            provenance=prov,
            reliability=rel,
            limitations=["Contractual revision may include granted extensions of time (EOT)"],
            semantic_status=rel.overall_tier,
        )
        return [ev]

    def extract_from_peer_intelligence(
        self,
        project_data: Union[str, Dict[str, Any]],
        tool_result: Dict[str, Any],
    ) -> List[Evidence]:
        p_id, p_dict = self._resolve_project(project_data)
        data = tool_result.get("data") or tool_result
        outliers = data.get("outliers") or {}
        is_outlier = bool(outliers.get("overall_is_outlier") or data.get("is_overall_peer_outlier", False))

        prov = self.provenance_tracker.build_provenance(
            source="PAIMANA Peer Intelligence Engine",
            source_id="peer_intelligence",
            project_id=p_id,
            tool_name="peer_intelligence",
            raw_inputs=data,
            calculation_method="multivariate_peer_benchmark_and_outlier_detection",
        )
        rel = self.reliability_evaluator.evaluate(
            source_name="peer_intelligence",
            provenance=prov,
            methodology="peer_distribution_percentile_benchmarking",
            source_category="PEER_INTELLIGENCE",
        )

        eid = f"EV_PEER_{p_id}_{int(time.time() * 1000) % 10000}"
        obs = tool_result.get("summary") or (
            f"Peer cohort benchmark: target is {'an outlier' if is_outlier else 'consistent with cohort distributions'}."
        )

        ev = Evidence(
            evidence_id=eid,
            project_id=p_id,
            evidence_type="PEER_COMPARATIVE_ANOMALY",
            source_type="PEER_SUBSYSTEM",
            source_id="peer_intelligence",
            observation=obs,
            value=is_outlier,
            unit="boolean_flag",
            as_of_date=str(p_dict.get("report_month") or ""),
            methodology="modified_zscore_and_iqr_peer_banding",
            provenance=prov,
            reliability=rel,
            limitations=["Comparative distribution only; contextualizes but does NOT prove root-cause"],
            semantic_status=ReliabilityTier.CONTEXTUAL,
        )
        return [ev]

    def extract_from_domain_context(
        self,
        project_data: Union[str, Dict[str, Any]],
        tool_result: Dict[str, Any],
    ) -> List[Evidence]:
        p_id, p_dict = self._resolve_project(project_data)
        data = tool_result.get("data") or tool_result
        ev_items: List[Evidence] = []

        land = data.get("land_acquisition") or {}
        if land and land.get("handover_pct") is not None:
            prov = self.provenance_tracker.build_provenance(
                source="Revenue Department & State Land Acquisition Records",
                source_id="analyze_domain_context",
                project_id=p_id,
                tool_name="analyze_domain_context",
                raw_inputs=land,
                calculation_method="land_possession_percentage",
            )
            rel = self.reliability_evaluator.evaluate(
                source_name="analyze_domain_context",
                provenance=prov,
                methodology="land_handover_measurement",
            )
            h_pct = float(land["handover_pct"])
            eid = f"EV_DOM_LAND_{p_id}_{int(time.time() * 1000) % 10000}"
            ev_items.append(
                Evidence(
                    evidence_id=eid,
                    project_id=p_id,
                    evidence_type="LAND_HANDOVER_STATUS",
                    source_type="DOMAIN_SUBSYSTEM",
                    source_id="analyze_domain_context",
                    observation=f"Right-of-way land handover is {h_pct:.1f}% (pending {land.get('pending_ha', 0):.1f} ha).",
                    value=h_pct,
                    unit="percentage",
                    as_of_date=str(p_dict.get("report_month") or ""),
                    methodology="statutory_3a_to_3h_land_possession_ratio",
                    provenance=prov,
                    reliability=rel,
                    limitations=["Physical possession boundary; does NOT prove sole causal driver of delay"],
                    semantic_status=rel.overall_tier,
                )
            )

        clearances = data.get("environmental_clearances") or {}
        if clearances and clearances.get("pending_count") is not None:
            p_count = int(clearances["pending_count"])
            prov = self.provenance_tracker.build_provenance(
                source="Statutory Clearance Registry",
                source_id="analyze_domain_context",
                project_id=p_id,
                tool_name="analyze_domain_context",
                raw_inputs=clearances,
                calculation_method="clearance_lifecycle_enumeration",
            )
            rel = self.reliability_evaluator.evaluate(
                source_name="analyze_domain_context",
                provenance=prov,
                methodology="statutory_portal_enumeration",
            )
            eid = f"EV_DOM_CLR_{p_id}_{int(time.time() * 1000) % 10000}"
            ev_items.append(
                Evidence(
                    evidence_id=eid,
                    project_id=p_id,
                    evidence_type="STATUTORY_CLEARANCE_STATUS",
                    source_type="DOMAIN_SUBSYSTEM",
                    source_id="analyze_domain_context",
                    observation=f"{p_count} statutory clearance(s) pending ({clearances.get('pending_critical_count', 0)} critical-path).",
                    value=p_count,
                    unit="clearances_count",
                    as_of_date=str(p_dict.get("report_month") or ""),
                    methodology="regulatory_clearance_tracking",
                    provenance=prov,
                    reliability=rel,
                    limitations=["Statutory processing timeline; does NOT constitute verified sole root-cause"],
                    semantic_status=rel.overall_tier,
                )
            )

        return ev_items
