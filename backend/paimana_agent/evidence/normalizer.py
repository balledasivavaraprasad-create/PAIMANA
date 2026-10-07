"""Evidence Normalizer for transforming raw tool outputs into first-class Evidence records.

Enforces source provenance, timestamp capture, authority scoring, lineage tracking,
and snapshot-based independence grouping.
"""
from __future__ import annotations
import time
from typing import Any, Optional
from .model import Evidence, SOURCE_AUTHORITY


class EvidenceNormalizer:
    """Normalizes raw observations and domain facts into structured Evidence instances."""

    def __init__(self):
        self._counter = 0

    def _next_id(self) -> str:
        self._counter += 1
        return f"E{self._counter}"

    def normalize_baseline_facts(self, p: dict) -> list[Evidence]:
        """Normalizes official CUF project facts into initial Evidence records with snapshot lineage."""
        items: list[Evidence] = []
        code = p.get("project_code", "unknown")
        month = p.get("report_month", "2026-01")
        snapshot_id = f"PAIMANA_SNAPSHOT_{code}_{month}"
        now = time.time()

        cost = p.get("original_cost_cr")
        exp = p.get("cumulative_expenditure_cr")
        if cost is not None and exp is not None:
            spend_pct = (exp / cost * 100.0) if cost > 0 else 0.0
            items.append(Evidence(
                id=self._next_id(),
                source_id="cuf_financial_ledger",
                source_tool="cuf_financial_ledger",
                source_type="verified_financial_record",
                source_system="PAIMANA",
                source_record_id=snapshot_id,
                source_field="cumulative_expenditure_cr",
                observed_at=now,
                recorded_at=now,
                retrieved_at=now,
                authority_score=SOURCE_AUTHORITY["verified_financial_record"],
                parent_evidence_ids=[],
                transformation_chain=["CUF raw financial ledger"],
                independence_group_id=snapshot_id,
                evidence_type="direct_observation",
                claim=f"Original cost is Rs {cost:,.1f} Cr; cumulative expenditure is Rs {exp:,.1f} Cr ({spend_pct:.1f}% disbursed).",
                raw_value={"original_cost_cr": cost, "cumulative_expenditure_cr": exp},
                derived_value=spend_pct,
                reliability=1.0,
                is_material=True
            ))

        prog = p.get("physical_progress_pct")
        if prog is not None:
            items.append(Evidence(
                id=self._next_id(),
                source_id="cuf_monthly_progress_report",
                source_tool="cuf_monthly_progress_report",
                source_type="official_project_record",
                source_system="PAIMANA",
                source_record_id=snapshot_id,
                source_field="physical_progress_pct",
                observed_at=now,
                recorded_at=now,
                retrieved_at=now,
                authority_score=SOURCE_AUTHORITY["official_project_record"],
                parent_evidence_ids=[],
                transformation_chain=["CUF monthly progress report"],
                independence_group_id=snapshot_id,
                evidence_type="direct_observation",
                claim=f"Certified physical site execution is {prog:.1f}%.",
                raw_value={"physical_progress_pct": prog},
                derived_value=float(prog),
                reliability=0.95,
                is_material=True
            ))

        orig_d = p.get("original_completion_date")
        rev_d = p.get("revised_completion_date")
        if orig_d:
            claim = f"Approved completion date was {orig_d}."
            if rev_d and rev_d != orig_d:
                claim += f" Current revised target is {rev_d}."
            items.append(Evidence(
                id=self._next_id(),
                source_id="cuf_milestone_schedule",
                source_tool="cuf_milestone_schedule",
                source_type="official_milestone_record",
                source_system="PAIMANA",
                source_record_id=snapshot_id,
                source_field="completion_date",
                observed_at=now,
                recorded_at=now,
                retrieved_at=now,
                authority_score=SOURCE_AUTHORITY["official_milestone_record"],
                parent_evidence_ids=[],
                transformation_chain=["CUF approved milestone schedule"],
                independence_group_id=snapshot_id,
                evidence_type="direct_observation",
                claim=claim,
                raw_value={"original_completion_date": orig_d, "revised_completion_date": rev_d},
                derived_value=rev_d or orig_d,
                reliability=1.0,
                is_material=True
            ))

        return items

    def normalize_tool_result(self, tool_name: str, result_data: Any, p: dict, feats: Optional[dict] = None) -> list[Evidence]:
        """Converts output of a specialist tool execution into structured Evidence records with lineage."""
        items: list[Evidence] = []
        data = result_data if isinstance(result_data, dict) else {}
        code = p.get("project_code", "unknown")
        month = p.get("report_month", "2026-01")
        snapshot_id = f"PAIMANA_SNAPSHOT_{code}_{month}"
        now = time.time()

        if tool_name == "financial_velocity":
            gap = data.get("progress_expenditure_gap_pct", 0.0)
            is_mat = abs(gap) > 5.0
            e = Evidence(
                id=self._next_id(),
                source_id=tool_name,
                source_tool=tool_name,
                source_type="tool_result",
                source_system="PAIMANA",
                source_record_id=snapshot_id,
                source_field="progress_expenditure_gap_pct",
                observed_at=now,
                recorded_at=now,
                retrieved_at=now,
                authority_score=SOURCE_AUTHORITY["tool_result"],
                parent_evidence_ids=["E1", "E2"],
                transformation_chain=["CUF project snapshot", "financial_velocity differential calculation"],
                independence_group_id=snapshot_id,  # Shared snapshot group (derived)
                evidence_type="derived_metric",
                claim=f"Cumulative financial spend leads certified physical progress by {gap:.1f} percentage points.",
                raw_value=data,
                derived_value=gap,
                reliability=0.95,
                relevance=1.0 if is_mat else 0.5,
                is_material=is_mat
            )
            if gap > 5.0:
                e.supports_hypotheses.append("front_loaded_billing")
                if gap > 15.0:
                    e.contradicts_hypotheses.append("reporting_discrepancy")
            elif gap < -5.0:
                e.contradicts_hypotheses.append("front_loaded_billing")
            items.append(e)

        elif tool_name == "milestone_audit":
            slip = data.get("schedule_slippage_months", 0.0)
            ratio = data.get("age_to_planned_ratio")
            is_mat = slip > 0 or (ratio is not None and ratio > 1.0)
            claim = f"Milestone schedule reflects {slip:.0f} months of slippage."
            if ratio and ratio > 1.0:
                claim += f" Project age ({ratio*100:.0f}%) exceeds sanctioned planned duration."
            e = Evidence(
                id=self._next_id(),
                source_id=tool_name,
                source_tool=tool_name,
                source_type="tool_result",
                source_system="PAIMANA",
                source_record_id=snapshot_id,
                source_field="schedule_slippage_months",
                observed_at=now,
                recorded_at=now,
                retrieved_at=now,
                authority_score=SOURCE_AUTHORITY["tool_result"],
                parent_evidence_ids=["E3"],
                transformation_chain=["CUF milestone dates", "milestone_audit slippage calculation"],
                independence_group_id=snapshot_id,  # Shared snapshot group (derived)
                evidence_type="derived_metric",
                claim=claim,
                raw_value=data,
                derived_value=slip,
                reliability=0.90,
                relevance=1.0 if is_mat else 0.5,
                is_material=is_mat
            )
            if slip > 0 or (ratio and ratio > 1.0):
                e.supports_hypotheses.append("chronic_schedule_delay")
                if slip > 6.0:
                    e.contradicts_hypotheses.append("reporting_discrepancy")
            elif slip == 0 and ratio and ratio <= 0.8:
                e.contradicts_hypotheses.append("chronic_schedule_delay")
            items.append(e)

        elif tool_name == "peer_intelligence" or tool_name.startswith("peer_") or tool_name in ["cohort_intelligence", "statistical_benchmark", "detect_peer_anomalies", "analyze_trajectory_intelligence", "analyze_domain_context"]:
            note = data.get("note") or data.get("summary") or "Peer intelligence cohort benchmarked."
            sector = p.get("sector", "all")
            peer_group = f"PEER_COHORT_{sector}"
            e = Evidence(
                id=self._next_id(),
                source_id=tool_name,
                source_tool=tool_name,
                source_type="approved_external_api",
                source_system="PAIMANA_PEER_DB",
                source_record_id=peer_group,
                source_field="sector_national_baseline",
                observed_at=now,
                recorded_at=now,
                retrieved_at=now,
                authority_score=SOURCE_AUTHORITY["approved_external_api"],
                parent_evidence_ids=[],
                transformation_chain=["National sector peer cohort aggregation"],
                independence_group_id=peer_group,  # Independent source group!
                evidence_type="direct_observation",
                claim=f"Peer Cohort: {note}",
                raw_value=data,
                derived_value=data.get("sector_national_baseline"),
                reliability=0.85,
                relevance=0.80,
                is_material=False
            )
            items.append(e)

            # Granular Peer Deviation Inferences
            dev_map = data.get("deviations", {})
            if isinstance(dev_map, dict):
                dev_items = dev_map.get("deviations", dev_map)
                if isinstance(dev_items, dict):
                    # Progress deviation
                    prog_dev = dev_items.get("physical_progress_pct")
                    if isinstance(prog_dev, dict):
                        is_sig = prog_dev.get("is_significant", False)
                        diff = float(prog_dev.get("difference_from_median", 0.0) or 0.0)
                        prank = float(prog_dev.get("percentile_rank", 50.0) or 50.0)
                        interp = prog_dev.get("interpretation", "")
                        dev_ev = Evidence(
                            id=self._next_id(),
                            source_id=f"{tool_name}_progress_deviation",
                            source_tool=tool_name,
                            source_type="approved_external_api",
                            source_system="PAIMANA_PEER_DB",
                            source_record_id=f"{peer_group}_PROG_DEV",
                            source_field="physical_progress_pct_deviation",
                            observed_at=now,
                            recorded_at=now,
                            retrieved_at=now,
                            authority_score=SOURCE_AUTHORITY["approved_external_api"],
                            parent_evidence_ids=[e.id],
                            transformation_chain=["Peer cohort median deviation calculation"],
                            independence_group_id=peer_group,
                            evidence_type="derived_metric",
                            claim=f"Peer Progress Deviation: {interp or f'Ranked {prank:.0f}th percentile across comparable peers.'}",
                            raw_value=prog_dev,
                            derived_value=diff,
                            reliability=0.88,
                            relevance=0.90 if is_sig else 0.60,
                            is_material=is_sig
                        )
                        if diff < -10.0 or prank <= 25.0:
                            dev_ev.supports_hypotheses.extend(["chronic_schedule_delay", "front_loaded_billing"])
                        elif diff > 10.0 or prank >= 75.0:
                            dev_ev.contradicts_hypotheses.append("chronic_schedule_delay")
                        items.append(dev_ev)

                    # Slippage deviation
                    slip_dev = dev_items.get("schedule_slippage_months")
                    if isinstance(slip_dev, dict):
                        is_sig = slip_dev.get("is_significant", False)
                        diff = float(slip_dev.get("difference_from_median", 0.0) or 0.0)
                        interp = slip_dev.get("interpretation", "")
                        slip_ev = Evidence(
                            id=self._next_id(),
                            source_id=f"{tool_name}_slippage_deviation",
                            source_tool=tool_name,
                            source_type="approved_external_api",
                            source_system="PAIMANA_PEER_DB",
                            source_record_id=f"{peer_group}_SLIP_DEV",
                            source_field="schedule_slippage_months_deviation",
                            observed_at=now,
                            recorded_at=now,
                            retrieved_at=now,
                            authority_score=SOURCE_AUTHORITY["approved_external_api"],
                            parent_evidence_ids=[e.id],
                            transformation_chain=["Peer cohort slippage comparison"],
                            independence_group_id=peer_group,
                            evidence_type="derived_metric",
                            claim=f"Peer Slippage Deviation: {interp or f'Slippage differs by {diff:+.1f} mo from cohort median.'}",
                            raw_value=slip_dev,
                            derived_value=diff,
                            reliability=0.88,
                            relevance=0.90 if is_sig else 0.60,
                            is_material=is_sig
                        )
                        if diff > 6.0:
                            slip_ev.supports_hypotheses.append("chronic_schedule_delay")
                        elif abs(diff) <= 3.0:
                            slip_ev.supports_hypotheses.extend(["unrealistic_original_dpr_timeline", "regulatory_land_clearance"])
                        items.append(slip_ev)

        elif tool_name == "project_history":
            hist = data.get("risk_history", [])
            issues = data.get("issues", [])
            hist_group = f"HISTORY_{code}"
            claim = f"Project history contains {len(hist)} evaluation records and {len(issues)} logged issues."
            if issues:
                claim += f" Recent issue: '{issues[-1]}'."
            e = Evidence(
                id=self._next_id(),
                source_id=tool_name,
                source_tool=tool_name,
                source_type="historical_precedent",
                source_system="PAIMANA_HISTORICAL_STORE",
                source_record_id=hist_group,
                source_field="issues",
                observed_at=now - 86400.0 * 30.0,  # 30 days historical context
                recorded_at=now - 86400.0 * 30.0,
                retrieved_at=now,
                authority_score=SOURCE_AUTHORITY["historical_precedent"],
                parent_evidence_ids=[],
                transformation_chain=["Historical evaluation logs retrieval"],
                independence_group_id=hist_group,  # Independent historical source group!
                evidence_type="direct_observation",
                claim=claim,
                raw_value=data,
                derived_value=len(issues),
                reliability=0.90,
                relevance=0.85,
                is_material=len(issues) > 0
            )
            items.append(e)

        elif tool_name == "memory_retrieval":
            succ = data.get("successful_precedents", [])
            unsucc = data.get("unsuccessful_precedents", [])
            claim = f"Memory retrieval matched {len(succ)} successful and {len(unsucc)} unsuccessful precedents."
            if succ:
                claim += f" Prior successful outcome: '{succ[0].get('outcome', '')}'."
            e = Evidence(
                id=self._next_id(),
                source_id=tool_name,
                source_tool=tool_name,
                source_type="historical_precedent",
                source_system="PAIMANA_MEMORY_STORE",
                source_record_id="INTERVENTION_OUTCOME_PREPARATION",
                observed_at=now - 86400.0 * 60.0,  # Precedents from prior periods
                recorded_at=now - 86400.0 * 60.0,
                retrieved_at=now,
                authority_score=SOURCE_AUTHORITY["historical_precedent"],
                parent_evidence_ids=[],
                transformation_chain=["Precedent similarity matching"],
                independence_group_id="HISTORICAL_PRECEDENT_MEMORY",  # Independent precedent group!
                evidence_type="precedent",
                claim=claim,
                raw_value=data,
                derived_value={"succ": len(succ), "unsucc": len(unsucc)},
                reliability=0.85,
                relevance=0.90,
                is_material=len(succ) > 0 or len(unsucc) > 0
            )
            items.append(e)

        elif tool_name == "shap_attribution":
            lines = data.get("shap_lines", [])
            claim = "SHAP attribution: " + "; ".join(lines[:2]) if lines else "SHAP attribution completed."
            e = Evidence(
                id=self._next_id(),
                source_id=tool_name,
                source_tool=tool_name,
                source_type="model_inference",
                source_system="PAIMANA_ML_PIPELINE",
                source_record_id=snapshot_id,
                source_field="shap_feature_importance",
                observed_at=now,
                recorded_at=now,
                retrieved_at=now,
                authority_score=SOURCE_AUTHORITY["model_inference"],
                parent_evidence_ids=["E1", "E2", "E3"],
                transformation_chain=["CUF project snapshot", "HistGradientBoosting inference", "SHAP permutation sampling"],
                independence_group_id=snapshot_id,  # Derived from snapshot!
                evidence_type="model_attribution",
                claim=claim,
                raw_value=data,
                derived_value=lines,
                reliability=0.75,
                relevance=0.80,
                is_material=False
            )
            items.append(e)

        else:
            # Generic fallback for any arbitrary tool
            e = Evidence(
                id=self._next_id(),
                source_id=tool_name,
                source_tool=tool_name,
                source_type="tool_result",
                source_system="PAIMANA",
                source_record_id=snapshot_id,
                observed_at=now,
                recorded_at=now,
                retrieved_at=now,
                authority_score=SOURCE_AUTHORITY["default"],
                parent_evidence_ids=[],
                transformation_chain=[f"Tool {tool_name} invocation"],
                independence_group_id=tool_name,
                evidence_type="direct_observation",
                claim=str(data.get("summary") or f"Executed tool {tool_name}."),
                raw_value=data,
                reliability=0.80,
                is_material=True
            )
            items.append(e)

        return items
