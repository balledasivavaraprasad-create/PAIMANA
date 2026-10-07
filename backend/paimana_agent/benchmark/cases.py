"""Canonical Ground-Truth Benchmark Cases for Phase 14 — Agent Quality Benchmark.

Defines 6 curated, real-world infrastructure failure scenarios with authoritative
ground-truth labels across hypotheses, causal mechanisms, confounders, tools,
recommendation suitability, peer cohorts, and institutional memory warnings.
"""
from __future__ import annotations
from typing import List, Dict, Any
from .models import BenchmarkCase


def get_benchmark_cases() -> List[BenchmarkCase]:
    """Returns the 6 authoritative ground-truth benchmark cases."""
    return [
        # ====================================================================
        # CASE 1: True Front-Loaded Billing & Milestone Certification Discrepancy
        # ====================================================================
        BenchmarkCase(
            case_id="CASE-01-FRONT-LOADED-BILLING",
            title="Four-Laning National Highway Expansion (NHAI EPC Package 4)",
            description=(
                "Site has 100% unencumbered Right of Way with no land or environmental obstacles. "
                "However, cumulative financial expenditure is 48% against only 14% physical progress "
                "(34% gap). Milestone audit shows certified billing for earthwork and sub-base that has "
                "not been physically verified on site."
            ),
            project_data={
                "project_code": "NH-BENCH-01",
                "project_name": "Four-Laning Highway Package 4",
                "ministry": "Ministry of Road Transport & Highways",
                "sector": "Road Transport and Highways",
                "implementing_agency": "NHAI",
                "state": "Maharashtra",
                "approval_date": "01/2023",
                "start_date": "06/2023",
                "original_completion_date": "06/2026",
                "original_cost_cr": 2200.0,
                "cumulative_expenditure_cr": 1056.0,  # 48% spent
                "physical_progress_pct": 14.0,       # only 14% built -> 34% gap!
                "terrain": "Plain",
                "contract_type": "EPC",
                "land_acquired_pct": 100.0,
            },
            event_type="COST_PROGRESS_MISMATCH",
            report_month="2026-03",
            ground_truth_root_cause="front_loaded_billing",
            ground_truth_causal_level=3,
            has_confounders=False,
            expected_confounders=[],
            punitive_action_warranted=True,  # Disbursal freeze / forensic financial-physical audit
            is_benign_artifact=False,
            relevant_tools=["financial_velocity", "milestone_audit", "project_history"],
            prohibited_actions=[],
            expected_recommendation_type="AUDIT_AND_ESCROW_FREEZE",
            peer_cohort_filters={"sector": "Road Transport and Highways", "cost_band": "Mega (>1000Cr)"},
            max_budget_steps=5
        ),

        # ====================================================================
        # CASE 2: Legitimate Regulatory Land Clearance / Statutory Stay
        # ====================================================================
        BenchmarkCase(
            case_id="CASE-02-REGULATORY-STAY",
            title="Himalayan Rail Tunnel Link (RVNL Package 2)",
            description=(
                "Tunnel excavation has stopped for 7 consecutive months with physical progress frozen "
                "at 18%. Contractor has mobilized tunneling rigs, but Forest & Wildlife Advisory Committee "
                "issued a formal Section 2 statutory stay order. Expenditure remains low (22%), indicating "
                "contractor is not draining funds. Contractor cannot work due to sovereign regulatory stay."
            ),
            project_data={
                "project_code": "RL-BENCH-02",
                "project_name": "Himalayan Rail Tunnel Package 2",
                "ministry": "Ministry of Railways",
                "sector": "Railways",
                "implementing_agency": "RVNL",
                "state": "Uttarakhand",
                "approval_date": "03/2022",
                "start_date": "09/2022",
                "original_completion_date": "09/2027",
                "original_cost_cr": 3400.0,
                "cumulative_expenditure_cr": 748.0,   # 22% spent
                "physical_progress_pct": 18.0,        # stalled at 18%
                "terrain": "Hilly / Mountainous",
                "contract_type": "EPC",
                "land_acquired_pct": 45.0,
                "statutory_clearance_status": "STAYED_FOREST_DEPT",
            },
            event_type="PROGRESS_STALLED",
            report_month="2026-03",
            ground_truth_root_cause="regulatory_land_clearance",
            ground_truth_causal_level=3,
            has_confounders=True,
            expected_confounders=["statutory_stay_order", "forest_wildlife_clearance"],
            punitive_action_warranted=False,  # Punishing contractor would be false attribution and illegal!
            is_benign_artifact=False,
            relevant_tools=["milestone_audit", "project_history", "peer_intelligence"],
            prohibited_actions=["CONTRACT_TERMINATION", "BANK_GUARANTEE_FORFEITURE", "LIQUIDATED_DAMAGES"],
            expected_recommendation_type="INTER_MINISTERIAL_CLEARANCE_TASKFORCE",
            peer_cohort_filters={"sector": "Railways", "cost_band": "Mega (>1000Cr)"},
            max_budget_steps=5
        ),

        # ====================================================================
        # CASE 3: Force Majeure / Catastrophic Environmental Shock
        # ====================================================================
        BenchmarkCase(
            case_id="CASE-03-ENVIRONMENTAL-FORCE-MAJEURE",
            title="Brahmaputra River Multi-Span Cable Stayed Bridge",
            description=(
                "Project was progressing on schedule (46% progress at month 16). In month 17, an unprecedented "
                "cloudburst and flash flood destroyed 2 main foundation cofferdams and submerged staging yards, "
                "forcing structural de-watering and safety reassessment. Physical progress dropped by 3% and "
                "completion slipped 10 months. Contractor was fully deployed before the flood."
            ),
            project_data={
                "project_code": "BR-BENCH-03",
                "project_name": "Brahmaputra River Cable Stayed Bridge",
                "ministry": "Ministry of Road Transport & Highways",
                "sector": "Road Transport and Highways",
                "implementing_agency": "NHIDCL",
                "state": "Assam",
                "approval_date": "06/2023",
                "start_date": "10/2023",
                "original_completion_date": "10/2026",
                "original_cost_cr": 1850.0,
                "cumulative_expenditure_cr": 832.5,   # 45% spent
                "physical_progress_pct": 43.0,        # slipped due to washaway
                "terrain": "Riverine / Floodplain",
                "contract_type": "EPC",
                "environmental_shock": "SEVERE_FLASH_FLOOD_DAMAGE",
            },
            event_type="MILESTONE_DELAYED",
            report_month="2026-03",
            ground_truth_root_cause="environmental_shock",
            ground_truth_causal_level=2,
            has_confounders=True,
            expected_confounders=["monsoon_flash_flood", "force_majeure_washaway"],
            punitive_action_warranted=False,  # Force majeure protects contractor from penalties
            is_benign_artifact=False,
            relevant_tools=["milestone_audit", "project_history"],
            prohibited_actions=["CONTRACT_TERMINATION", "PENALTY_ENFORCEMENT"],
            expected_recommendation_type="EXTENSION_OF_TIME_AND_RESCHEDULING",
            peer_cohort_filters={"sector": "Road Transport and Highways"},
            max_budget_steps=5
        ),

        # ====================================================================
        # CASE 4: Benign Reporting Discrepancy / Data Artifact (Noise Control)
        # ====================================================================
        BenchmarkCase(
            case_id="CASE-04-BENIGN-REPORTING-DISCREPANCY",
            title="Coastal Port Connectivity Four-Lane Link",
            description=(
                "Monthly portal submission shows 28% physical progress against 30% expenditure (minimal 2% gap). "
                "However, a temporary portal synchronization lag occurred because regional office transitioned "
                "to a new PMIS schema. Drone survey and CUF bank accounts show physical milestones are active and healthy. "
                "This is benign reporting noise; the agent must NOT trigger high alerts or false investigations."
            ),
            project_data={
                "project_code": "PT-BENCH-04",
                "project_name": "Coastal Port Connectivity Link",
                "ministry": "Ministry of Ports, Shipping and Waterways",
                "sector": "Ports and Shipping",
                "implementing_agency": "IPA",
                "state": "Gujarat",
                "approval_date": "01/2024",
                "start_date": "04/2024",
                "original_completion_date": "04/2027",
                "original_cost_cr": 850.0,
                "cumulative_expenditure_cr": 255.0,  # 30% spent
                "physical_progress_pct": 28.0,       # 28% built (healthy 2% gap)
                "terrain": "Coastal",
                "contract_type": "EPC",
                "data_sync_lag": "MINOR_PORTAL_TRANSITION",
            },
            event_type="NORMAL_PROGRESS",
            report_month="2026-03",
            ground_truth_root_cause="reporting_discrepancy",
            ground_truth_causal_level=1,
            has_confounders=False,
            expected_confounders=[],
            punitive_action_warranted=False,
            is_benign_artifact=True,
            relevant_tools=["financial_velocity"],
            prohibited_actions=["CRITICAL_ALERT", "CONTRACT_TERMINATION", "SPECIAL_AUDIT"],
            expected_recommendation_type="ROUTINE_MONITORING_OR_DATA_RECONCILIATION",
            peer_cohort_filters={"sector": "Ports and Shipping"},
            max_budget_steps=3
        ),

        # ====================================================================
        # CASE 5: Chronic Contractor Execution Stagnation (Peer Cohort Proves Outlier)
        # ====================================================================
        BenchmarkCase(
            case_id="CASE-05-CHRONIC-CONTRACTOR-STAGNATION",
            title="Greenfield Industrial Corridor Expressway Package 3",
            description=(
                "Site has 100% land acquired, clear approvals, and full advance disbursement. "
                "Yet physical progress is only 21% after 70% of contract duration has elapsed. "
                "National Peer Intelligence reveals 14 cohort projects in identical terrain, budget, and agency "
                "are at 68-82% progress. Contractor has demobilized machinery to other private sites."
            ),
            project_data={
                "project_code": "EXP-BENCH-05",
                "project_name": "Greenfield Industrial Expressway Package 3",
                "ministry": "Ministry of Road Transport & Highways",
                "sector": "Road Transport and Highways",
                "implementing_agency": "NHAI",
                "state": "Rajasthan",
                "approval_date": "01/2022",
                "start_date": "05/2022",
                "original_completion_date": "05/2025",
                "original_cost_cr": 1600.0,
                "cumulative_expenditure_cr": 640.0,   # 40% spent
                "physical_progress_pct": 21.0,        # only 21% built after 34 months!
                "terrain": "Plain / Semi-Arid",
                "contract_type": "EPC",
                "contractor_mobilization_ratio": 0.30,  # 70% machinery missing
            },
            event_type="PROGRESS_STALLED",
            report_month="2026-03",
            ground_truth_root_cause="chronic_schedule_delay",
            ground_truth_causal_level=4,
            has_confounders=False,
            expected_confounders=[],
            punitive_action_warranted=True,  # Contractual cure notice / encash mobilization BG if uncured
            is_benign_artifact=False,
            relevant_tools=["milestone_audit", "peer_intelligence", "financial_velocity"],
            prohibited_actions=[],
            expected_recommendation_type="CONTRACTUAL_CURE_NOTICE_WITH_MILESTONE_CONDITIONS",
            peer_cohort_filters={"sector": "Road Transport and Highways", "cost_band": "Mega (>1000Cr)"},
            max_budget_steps=5
        ),

        # ====================================================================
        # CASE 6: Adverse Precedent Risk / Institutional Memory Warning Test
        # ====================================================================
        BenchmarkCase(
            case_id="CASE-06-ADVERSE-PRECEDENT-RISK",
            title="Inter-State High Voltage Power Transmission Substation Package",
            description=(
                "Contractor dispute arose over price escalation formula. The contractor slowed down "
                "switchyard commissioning. Institutional memory contains a precedent where immediate "
                "unilateral contract termination resulted in High Court litigation, an injunction freezing the site "
                "for 36 months, and an 85% cost escalation. The agent MUST heed the failure memory warning "
                "and reject unilateral termination in favor of structured dispute conciliation or escrow ring-fencing."
            ),
            project_data={
                "project_code": "PW-BENCH-06",
                "project_name": "765kV High Voltage Substation Link",
                "ministry": "Ministry of Power",
                "sector": "Power",
                "implementing_agency": "POWERGRID",
                "state": "Madhya Pradesh",
                "approval_date": "04/2023",
                "start_date": "08/2023",
                "original_completion_date": "08/2026",
                "original_cost_cr": 1250.0,
                "cumulative_expenditure_cr": 600.0,   # 48% spent
                "physical_progress_pct": 36.0,        # 36% built
                "terrain": "Plain",
                "contract_type": "EPC",
                "dispute_type": "PRICE_ESCALATION_CLAUSE",
            },
            event_type="MILESTONE_DELAYED",
            report_month="2026-03",
            ground_truth_root_cause="chronic_schedule_delay",
            ground_truth_causal_level=3,
            has_confounders=False,
            expected_confounders=[],
            punitive_action_warranted=False,  # Unilateral cancellation is counter-productive due to litigation precedent
            is_benign_artifact=False,
            relevant_tools=["milestone_audit", "memory_retrieval", "financial_velocity"],
            prohibited_actions=["UNILATERAL_CONTRACT_TERMINATION", "IMMEDIATE_BANK_GUARANTEE_ENCASHMENT"],
            expected_recommendation_type="CONCILIATION_COMMITTEE_AND_ESCROW_RESTRUCTURING",
            peer_cohort_filters={"sector": "Power", "cost_band": "Mega (>1000Cr)"},
            max_budget_steps=5
        ),
    ]
