"""General Infrastructure Causal Ontology and Mechanism Templates.

Codifies domain-specific mechanisms for capital infrastructure projects,
distinguishing theoretical plausibility from project-specific empirical evidence.
"""
from __future__ import annotations
from typing import Optional
from .models import CausalMechanism


class CausalOntology:
    """Repository of canonical causal mechanisms for infrastructure monitoring."""

    MECHANISMS = {
        "M_CONTRACTOR_EXECUTION": CausalMechanism(
            id="M_CONTRACTOR_EXECUTION",
            name="Contractor Execution & Mobilization Bottleneck",
            cause="Contractor Resource Shortage",
            intermediate_variables=[
                "machinery_equipment_deployment",
                "skilled_labor_density",
                "site_productivity_rate",
                "workfront_execution_rate",
                "physical_progress"
            ],
            effect="Milestone & Schedule Delay",
            predicted_observations=[
                "Equipment deployment below mobilization plan",
                "Low labor muster on active workfronts",
                "Contractor idling reports",
                "Delay in sub-contractor procurement"
            ],
            falsifying_observations=[
                "Resource deployment at or above contract baseline",
                "Productivity normal or high on all unencumbered workfronts",
                "Contractor idling directly caused by lack of site access",
                "Timely completion of all packages managed by the same contractor"
            ],
            actionable_node="Subcontractor Mobilization & Resource Infusion",
            actionable_stakeholder="Contractor Project Manager & Independent Engineer"
        ),
        "M_APPROVAL_DEPENDENCY": CausalMechanism(
            id="M_APPROVAL_DEPENDENCY",
            name="Regulatory and Inter-Agency Approval Delay",
            cause="Regulatory / Clearance Bottleneck",
            intermediate_variables=[
                "statutory_turnaround_time",
                "encumbrance_free_workfront",
                "access_to_alignment",
                "activity_commencement",
                "milestone_completion"
            ],
            effect="Milestone Slippage & Stalled Progress",
            predicted_observations=[
                "Forest Stage-II or wildlife clearance pending beyond SLA",
                "Railway crossing / utility shifting approvals unissued",
                "Local body stop-work notices or environmental compliance stay",
                "Subcontractor mobilized but barred from working in eco-sensitive zones"
            ],
            falsifying_observations=[
                "All statutory clearances issued prior to scheduled milestone start",
                "Delayed milestones have zero regulatory dependencies",
                "Contractor failing to progress on fully cleared stretches"
            ],
            actionable_node="Expedited Inter-Departmental Clearance Taskforce",
            actionable_stakeholder="Ministry Coordinating Officer / District Collector"
        ),
        "M_FUNDING_CONSTRAINT": CausalMechanism(
            id="M_FUNDING_CONSTRAINT",
            name="Liquidity and Fund Release Disruption",
            cause="Budgetary Allocation / Liquidity Bottleneck",
            intermediate_variables=[
                "budget_release_schedule",
                "escrow_account_balance",
                "running_bill_payment_turnaround",
                "vendor_cashflow_liquidity",
                "material_procurement_pace"
            ],
            effect="Expenditure Decoupling or Complete Site Stoppage",
            predicted_observations=[
                "Running account bills pending unpaid beyond 45 days",
                "Subcontractor complaints regarding unpaid milestone payments",
                "Supplier freeze on cement/steel deliveries due to overdue invoices",
                "Escrow account depleted below minimum mandatory buffer"
            ],
            falsifying_observations=[
                "Sufficient budget allocation available in project escrow",
                "Contractor running bills cleared and paid within 15 days",
                "Contractor audited financials demonstrate strong independent working capital"
            ],
            actionable_node="Prompt Milestone Bill Liquidation & Escrow Top-up",
            actionable_stakeholder="Ministry Financial Advisor & Project Director"
        ),
        "M_LAND_ROW_DEFICIT": CausalMechanism(
            id="M_LAND_ROW_DEFICIT",
            name="Land Acquisition and Contiguous ROW Deficit",
            cause="Land Possession & Encroachment Delay",
            intermediate_variables=[
                "section_3D_gazette_possession",
                "contiguous_unencumbered_stretch_km",
                "heavy_equipment_continuity",
                "linear_paving_productivity"
            ],
            effect="Discontinuous Workfronts & Paving Stoppage",
            predicted_observations=[
                "Encroachment litigations pending in local revenue courts",
                "Compensation disbursement delayed to titleholders",
                "Patchwork workfronts (<5 km contiguous stretches) preventing paver movement",
                "Demolition of existing structures resisted by landowners"
            ],
            falsifying_observations=[
                "100% encumbrance-free contiguous ROW handed over at Appointed Date",
                "Slippage occurred exclusively on 100% acquired corridor segments",
                "Zero pending compensation claims in district revenue registry"
            ],
            actionable_node="Stage-wise Corridor Descoping & Focused Revenue Liaison",
            actionable_stakeholder="Competent Authority for Land Acquisition (CALA) & NHAI RO"
        ),
        "M_DESIGN_VARIATION": CausalMechanism(
            id="M_DESIGN_VARIATION",
            name="Geological Strata Surprise & Design Revision",
            cause="Geotechnical Variance / Major Scope Variation",
            intermediate_variables=[
                "subsurface_geotechnical_variance",
                "good_for_construction_drawing_freeze",
                "scope_variation_approval_cycle",
                "structural_redesign_rework"
            ],
            effect="Suspended Foundation Work & Extended Schedule",
            predicted_observations=[
                "Encountered unexpected underground strata / water ingress",
                "Revised structural drawings pending proof-consultant review",
                "Formal variation orders submitted exceeding 10% contract value",
                "Specialized geotechnical consultant mobilized for slope stabilization"
            ],
            falsifying_observations=[
                "All Good-for-Construction drawings frozen before work commenced",
                "Subsurface bore logs perfectly matched tender geotechnical reports",
                "Zero variation claims submitted by executing contractor"
            ],
            actionable_node="Fast-Track Technical Advisory Committee Review",
            actionable_stakeholder="Proof Consultant & Chief Engineer"
        ),
        "M_FRONT_LOADED_BILLING": CausalMechanism(
            id="M_FRONT_LOADED_BILLING",
            name="Front-Loaded Billing and Uncertified Advance Decoupling",
            cause="Front-Loaded Billing or Uncertified Advance Decoupling",
            intermediate_variables=[
                "disbursement_velocity",
                "uncertified_advance_billing",
                "milestone_certification_gap",
                "contractor_cashflow_frontloading",
                "physical_delivery_lag"
            ],
            effect="Financial Progress Outpacing Physical Progress",
            predicted_observations=[
                "Financial expenditure rate significantly exceeds physical progress",
                "Advance payments or mobilization advances disbursed without corresponding site milestone signoff",
                "Uncertified milestone claims approved provisionally",
                "Physical completion lagging certified financial disbursements by >15%"
            ],
            falsifying_observations=[
                "Certified physical completion matches or exceeds disbursement milestones",
                "All payments backed 100% by independent engineer certified measurement sheets",
                "Zero mobilization advances outstanding unrecovered"
            ],
            actionable_node="Independent Measurement Book (MB) Audit & Advance Recovery",
            actionable_stakeholder="Project Financial Controller & Independent Engineer"
        ),
        "M_REPORTING_DISCREPANCY": CausalMechanism(
            id="M_REPORTING_DISCREPANCY",
            name="Administrative Reporting Discrepancy and Data Lag",
            cause="Reporting Discrepancy or Administrative Data Lag",
            intermediate_variables=[
                "portal_data_entry_lag",
                "site_measurement_book_reconciliation",
                "administrative_reporting_delay",
                "progress_metric_misalignment"
            ],
            effect="Paper-vs-Site Status Inconsistency",
            predicted_observations=[
                "Monthly Progress Reports (MPR) inconsistent with project portal entries",
                "Site measurement books updated weeks after physical execution",
                "Field inspection logs show higher or lower progress than central dashboards",
                "Data entry backlog confirmed at field division office"
            ],
            falsifying_observations=[
                "Daily automated RFID / drone / sensor sync with central database",
                "Portal records match physical site audit records within 24 hours",
                "Independent Engineer certifies portal reporting matches physical ground reality"
            ],
            actionable_node="Field Data Reconciliation & Portal Synchronization Protocol",
            actionable_stakeholder="Project Management Consultant (PMC) & Monitoring Cell"
        )
    }

    @classmethod
    def get_mechanism(cls, mechanism_id: str) -> Optional[CausalMechanism]:
        """Returns a copy of the canonical mechanism template."""
        mech = cls.MECHANISMS.get(mechanism_id)
        if not mech:
            return None
        return CausalMechanism(
            id=mech.id,
            name=mech.name,
            cause=mech.cause,
            intermediate_variables=list(mech.intermediate_variables),
            effect=mech.effect,
            predicted_observations=list(mech.predicted_observations),
            falsifying_observations=list(mech.falsifying_observations),
            actionable_node=mech.actionable_node,
            actionable_stakeholder=mech.actionable_stakeholder,
            links_verified={},
            is_validated=False
        )

    @classmethod
    def match_mechanism_for_cause(cls, proposed_cause: str) -> Optional[CausalMechanism]:
        """Finds closest canonical mechanism matching a proposed cause."""
        cause_lower = proposed_cause.lower()
        if any(w in cause_lower for w in ["front_load", "front-load", "front loaded", "billing", "decoupling"]):
            return cls.get_mechanism("M_FRONT_LOADED_BILLING")
        elif any(w in cause_lower for w in ["reporting", "discrepancy", "mpr", "data lag", "misalignment"]):
            return cls.get_mechanism("M_REPORTING_DISCREPANCY")
        elif any(w in cause_lower for w in ["contractor", "mobilization", "execution", "manpower", "equipment"]):
            return cls.get_mechanism("M_CONTRACTOR_EXECUTION")
        elif any(w in cause_lower for w in ["approval", "clearance", "forest", "wildlife", "regulatory"]):
            return cls.get_mechanism("M_APPROVAL_DEPENDENCY")
        elif any(w in cause_lower for w in ["fund", "budget", "liquidity", "payment", "escrow", "cashflow"]):
            return cls.get_mechanism("M_FUNDING_CONSTRAINT")
        elif any(w in cause_lower for w in ["land", "row", "encumbrance", "possession", "acquisition"]):
            return cls.get_mechanism("M_LAND_ROW_DEFICIT")
        elif any(w in cause_lower for w in ["design", "geological", "strata", "drawing", "variation"]):
            return cls.get_mechanism("M_DESIGN_VARIATION")
        return None
