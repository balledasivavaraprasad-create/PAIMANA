"""Unified Domain Intelligence Service (DSI-01 to DSI-14).

Orchestrates multi-attribute project profiling, land acquisition analysis,
statutory clearance monitoring, utility shifting evaluation, commercial procurement,
contract variations, physical terrain/weather windows, linear workfront continuity,
dependency graph modeling, peer normalizations, and investigation planning.
"""
from __future__ import annotations

import hashlib
import json
import logging
import time
from typing import Any, Dict, List, Optional

from .contract import ContractAnalyzer
from .contractor_workfront import ContractorWorkfrontAnalyzer
from .dependency_graph import DependencyGraphBuilder
from .environmental import EnvironmentalClearanceAnalyzer
from .explanation import DomainExplanationEngine
from .investigation_strategy import InvestigationStrategyPlanner
from .land_acquisition import LandAcquisitionAnalyzer
from .normalization import DomainNormalizationEngine
from .physical_context import PhysicalContextAnalyzer
from .procurement import ProcurementAnalyzer
from .project_profile import ProjectProfileBuilder
from .utility_shifting import UtilityShiftingAnalyzer
from .schemas import (
    ConstraintSeverity,
    DomainContextReport,
    EvidenceStatus,
)

logger = logging.getLogger("paimana.peer.domain.service")


class DomainIntelligenceService:
    """Master analytical service for domain-specific infrastructure intelligence."""

    def __init__(self, cache_enabled: bool = True):
        self.profile_builder = ProjectProfileBuilder()
        self.land_analyzer = LandAcquisitionAnalyzer()
        self.clearance_analyzer = EnvironmentalClearanceAnalyzer()
        self.utility_analyzer = UtilityShiftingAnalyzer()
        self.procurement_analyzer = ProcurementAnalyzer()
        self.contract_analyzer = ContractAnalyzer()
        self.physical_analyzer = PhysicalContextAnalyzer()
        self.workfront_analyzer = ContractorWorkfrontAnalyzer()
        self.graph_builder = DependencyGraphBuilder()
        self.normalization_engine = DomainNormalizationEngine()
        self.strategy_planner = InvestigationStrategyPlanner()
        self.explanation_engine = DomainExplanationEngine()
        self.cache_enabled = cache_enabled
        self._cache: Dict[str, DomainContextReport] = {}

    def analyze_domain_context(
        self,
        project_data: Dict[str, Any],
        question: Optional[str] = None,
        hypothesis: Optional[str] = None,
        target_metrics: Optional[Dict[str, float]] = None,
    ) -> DomainContextReport:
        """Executes full domain-specific intelligence analysis for a project."""
        cache_key = self._compute_cache_key(project_data, question, hypothesis)
        if self.cache_enabled and cache_key in self._cache:
            return self._cache[cache_key]

        t0 = time.time()

        # 1. Build Domain Profile (DSI-01, DSI-02)
        profile = self.profile_builder.build_profile(project_data)

        # 2. Land Acquisition Analysis (DSI-05)
        raw_p = project_data.get("physical_progress_pct") or project_data.get("physical_progress")
        phys_pct = float(raw_p) if raw_p is not None else 0.0
        land_analysis = self.land_analyzer.analyze(
            project_data=project_data,
            is_linear=profile.is_linear,
            physical_progress_pct=phys_pct,
        )

        # 3. Environmental & Statutory Clearances (DSI-06)
        clearance_analysis = self.clearance_analyzer.analyze(project_data)

        # 4. Utility Shifting & Obstructions (DSI-07)
        utility_analysis = self.utility_analyzer.analyze(project_data)

        # 5. Procurement Intelligence (DSI-03)
        procurement_analysis = self.procurement_analyzer.analyze(project_data)

        # 6. Contract Variations & EOT (DSI-04)
        contract_analysis = self.contract_analyzer.analyze(project_data)

        # 7. Physical Terrain & Seasonal Weather (DSI-08, DSI-09)
        physical_analysis = self.physical_analyzer.analyze(project_data, terrain=profile.terrain)

        # 8. Contractor Profile & Workfront Continuity (DSI-10, DSI-11)
        workfront_analysis = self.workfront_analyzer.analyze(
            project_data=project_data,
            is_linear=profile.is_linear,
            length_km=profile.length_km,
            handover_pct=land_analysis.handover_pct if land_analysis.required_ha > 0 else 100.0,
        )

        # 9. Dependency Graph Modeling (DSI-13)
        packages = project_data.get("packages")
        milestones = project_data.get("milestones")
        graph_report = self.graph_builder.build_graph(
            project_code=profile.project_code,
            land_analysis=land_analysis,
            clearance_analysis=clearance_analysis,
            utility_analysis=utility_analysis,
            packages=packages,
            milestones=milestones,
        )

        # 10. Peer Normalization Adjustments (DSI-12)
        metrics_dict = target_metrics or {}
        normalizations = self.normalization_engine.compute_normalizations(profile, metrics_dict)

        # 11. Investigation Strategy Recommendations (DSI-14)
        investigation_strategies = self.strategy_planner.plan_strategy(
            profile=profile,
            question=question,
            hypothesis=hypothesis,
            land_analysis=land_analysis,
            clearance_analysis=clearance_analysis,
            utility_analysis=utility_analysis,
            contract_analysis=contract_analysis,
        )

        # 12. Consolidate Key Constraints and Provenance Gaps
        key_constraints: List[str] = []
        data_gaps: List[str] = []

        for analysis_obj, domain_label in [
            (land_analysis, "Land Acquisition"),
            (clearance_analysis, "Statutory Clearances"),
            (utility_analysis, "Utility Shifting"),
            (procurement_analysis, "Procurement"),
            (contract_analysis, "Contract Administration"),
            (physical_analysis, "Physical Environment"),
            (workfront_analysis, "Workfront Continuity"),
        ]:
            if analysis_obj.evidence_status == EvidenceStatus.UNVERIFIED_GAP:
                data_gaps.append(f"Missing {domain_label} operational documentation.")
            else:
                for f in getattr(analysis_obj, "findings", []):
                    # Flag findings that indicate friction/risk
                    if any(w in f.lower() for w in ["deficit", "pending", "risk", "delay", "gap", "dispute", "fragmented", "unpaid", "invoked", "difficulty", "obstruction"]):
                        key_constraints.append(f"[{domain_label}] {f}")

        # 13. Evidence Attribution & Narrative (DSI-14)
        evidence_items = self.explanation_engine.generate_evidence_items(
            profile=profile,
            land=land_analysis,
            clearances=clearance_analysis,
            utilities=utility_analysis,
            procurement=procurement_analysis,
            contract=contract_analysis,
            physical=physical_analysis,
        )

        summary_narrative = self.explanation_engine.build_narrative(
            profile=profile,
            land=land_analysis,
            clearances=clearance_analysis,
            utilities=utility_analysis,
            procurement=procurement_analysis,
            contract=contract_analysis,
            physical=physical_analysis,
            graph=graph_report,
            key_constraints=key_constraints,
            data_gaps=data_gaps,
        )

        t_elapsed = (time.time() - t0) * 1000.0

        report = DomainContextReport(
            project_code=profile.project_code,
            project_name=profile.project_name,
            profile=profile,
            land_acquisition=land_analysis,
            environmental_clearances=clearance_analysis,
            utility_shifting=utility_analysis,
            procurement=procurement_analysis,
            contract=contract_analysis,
            physical_context=physical_analysis,
            contractor_workfront=workfront_analysis,
            dependency_graph=graph_report,
            normalizations=normalizations,
            investigation_strategies=investigation_strategies,
            evidence_items=evidence_items,
            summary_narrative=summary_narrative,
            key_constraints=key_constraints,
            data_gaps=data_gaps,
            execution_time_ms=t_elapsed,
        )

        if self.cache_enabled and cache_key:
            self._cache[cache_key] = report

        return report

    def _compute_cache_key(
        self,
        project_data: Dict[str, Any],
        question: Optional[str],
        hypothesis: Optional[str],
    ) -> str:
        keys = [
            "project_code", "project_name", "sector", "state", "length_km",
            "physical_progress_pct", "original_cost_cr", "report_month"
        ]
        sub = {k: project_data.get(k) for k in keys}
        sub["question"] = question or ""
        sub["hypothesis"] = hypothesis or ""
        return hashlib.sha256(json.dumps(sub, sort_keys=True, default=str).encode("utf-8")).hexdigest()
