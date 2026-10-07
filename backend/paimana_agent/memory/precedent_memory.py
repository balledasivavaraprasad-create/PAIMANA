"""Precedent Memory Store.

Persistent and in-memory registry of validated institutional precedents,
failure precedents, and counterexamples.
"""
from __future__ import annotations
import json
import os
import time
from typing import Optional
from .models import (
    Precedent, PrecedentContext, PatternFingerprint, PrecedentProvenance,
    PrecedentStatus, AttributionClass
)
from .pattern_fingerprint import PatternFingerprintBuilder


class PrecedentMemoryStore:
    """Manages the lifecycle, storage, and indexing of Precedent records."""

    def __init__(self, persistence_path: Optional[str] = None):
        self.persistence_path = persistence_path
        self._precedents: dict[str, Precedent] = {}
        self._seed_canonical_precedents()
        if self.persistence_path and os.path.exists(self.persistence_path):
            self.load()

    def add_precedent(self, precedent: Precedent) -> None:
        """Stores or updates a precedent."""
        self._precedents[precedent.id] = precedent
        if self.persistence_path:
            self.save()

    def get_precedent(self, precedent_id: str) -> Optional[Precedent]:
        return self._precedents.get(precedent_id)

    def list_all(self, status: Optional[str] = None) -> list[Precedent]:
        if status:
            return [p for p in self._precedents.values() if p.status == status]
        return list(self._precedents.values())

    def clear(self) -> None:
        """Clears all stored precedents."""
        self._precedents.clear()

    def reset(self) -> None:
        """Resets the store to canonical seeds."""
        self._precedents.clear()
        self._seed_canonical_precedents()

    def find_counterexamples(self, target_pattern: Optional[PatternFingerprint] = None,
                             hypothesis: Optional[str] = None) -> list[Precedent]:
        """Finds counterexamples matching the hypothesis or pattern to refute confirmation bias."""
        results = []
        for p in self._precedents.values():
            if not p.is_counterexample:
                continue
            if hypothesis:
                hypo_norm = hypothesis.strip().lower()
                matches = any(hypo_norm == ch.strip().lower() or hypo_norm in ch.strip().lower() or ch.strip().lower() in hypo_norm
                              for ch in p.counterexample_for_hypotheses)
                if matches:
                    results.append(p)
                    continue
            if target_pattern and p.pattern_fingerprint.event_type == target_pattern.event_type:
                results.append(p)
        return results

    def find_failed_precedents(self) -> list[Precedent]:
        """Returns all validated failure precedents."""
        return [
            p for p in self._precedents.values()
            if p.attribution_class in {"FAILED", "LIKELY_INEFFECTIVE"} or p.failure_count > p.success_count
        ]

    def _seed_canonical_precedents(self) -> None:
        """Seeds canonical precedents from high-value infrastructure case studies."""
        # 1. Successful ROW Descoping Precedent
        p1 = Precedent(
            id="PREC-NHAI-ROW-01",
            title="ROW Descoping and Milestone Re-baselining",
            event_pattern={"event_type": "progress_stalled", "gap": 22.0},
            pattern_fingerprint=PatternFingerprint(
                event_type="progress_stalled",
                financial_velocity="decoupled",
                milestone_slippage="persistent",
                progress_variance="high",
                risk_direction="increasing",
                risk_velocity="fast",
                approval_delay="high",
                contractor_delay="low"
            ),
            context=PrecedentContext(
                sector="Road Transport and Highways",
                project_type="Expressway / 4-Laning",
                project_size_cr=1250.0,
                cost_band="Mega (>1000Cr)",
                stage_bracket="Mid (25-75%)",
                implementing_agency="NHAI",
                contract_type="EPC"
            ),
            evidence_pattern=["High land acquisition delay", "Cumulative expenditure outpacing physical works", "Encroachment on 18% stretch"],
            hypothesis_pattern=["LAND_ACQUISITION_BLOCKED", "SCOPE_CREEP"],
            root_cause="Unencumbered ROW unavailable on 18% of alignment, preventing continuous paver run.",
            root_cause_confidence=0.88,
            intervention={
                "action": "Descope 18% disputed alignment into standalone future package; declare Commercial Operation Date for completed 82% section.",
                "intervention_class": "DESCOPING_AND_REBASELINING"
            },
            expected_outcome={"risk_reduction": 15, "progress_resumption_months": 2},
            observed_outcome={"status": "positive", "notes": "Contractor mobilized on unencumbered section; physical progress rose 14% in 90 days.", "risk_delta": -12.0},
            outcome_quality=0.90,
            intervention_effectiveness=0.88,
            attribution_class="LIKELY_EFFECTIVE",
            memory_reliability=0.92,
            transferability_score=0.85,
            source_project_id="NH-44-PKG-3",
            provenance=PrecedentProvenance(
                source_investigation_ids=["INV-2023-NH44-01"],
                source_project_codes=["NH-44-PKG-3"],
                independence_group_ids=["NHAI_RO_LUCKNOW"]
            ),
            status="VALIDATED",
            application_count=3,
            success_count=3,
            failure_count=0,
            usage_guidance="Apply when land dispute affects <20% of corridor and rest is ready for tolling/COD."
        )

        # 2. Failure Precedent: Premature Penalty Without Land Clearance
        p2 = Precedent(
            id="PREC-NHAI-PENALTY-FAIL",
            title="Premature Liquidated Damages Without ROW Clearance",
            event_pattern={"event_type": "progress_stalled", "gap": 18.0},
            pattern_fingerprint=PatternFingerprint(
                event_type="progress_stalled",
                financial_velocity="decoupled",
                milestone_slippage="persistent",
                progress_variance="high",
                risk_direction="increasing",
                risk_velocity="moderate",
                approval_delay="high",
                contractor_delay="moderate"
            ),
            context=PrecedentContext(
                sector="Road Transport and Highways",
                project_type="Highway Widening",
                project_size_cr=650.0,
                cost_band="Standard (150-1000Cr)",
                stage_bracket="Mid (25-75%)",
                implementing_agency="NHAI",
                contract_type="EPC"
            ),
            evidence_pattern=["Contractor idling plant", "Pending forest clearance in Stage-II", "Show-cause issued"],
            hypothesis_pattern=["CONTRACTOR_MOBILIZATION_FAILURE"],
            root_cause="Authority issued show-cause and withheld bills while ROW was physically encumbered.",
            root_cause_confidence=0.82,
            intervention={
                "action": "Enforce liquidated damages and freeze escrow milestone disbursements.",
                "intervention_class": "PENALTY_ENFORCEMENT"
            },
            expected_outcome={"compliance": "Contractor remobilizes within 30 days"},
            observed_outcome={"status": "negative", "notes": "Contractor stopped work entirely and filed Section 9 arbitration petition. Site shut for 11 months.", "risk_delta": +18.0},
            outcome_quality=0.85,
            intervention_effectiveness=0.10,
            attribution_class="FAILED",
            memory_reliability=0.89,
            transferability_score=0.80,
            source_project_id="NH-66-PKG-1",
            provenance=PrecedentProvenance(
                source_investigation_ids=["INV-2022-NH66-04"],
                source_project_codes=["NH-66-PKG-1"],
                independence_group_ids=["NHAI_RO_KERALA"]
            ),
            status="VALIDATED",
            application_count=2,
            success_count=0,
            failure_count=2,
            why_relevant="Demonstrates that punitive actions without resolving owner-side ROW encumbrances triggers legal paralysis.",
            usage_guidance="DO NOT issue liquidated damages or bill freezes if landowner or regulatory clearances are incomplete."
        )

        # 3. Counterexample: Spend Stall was Regulatory, Not Cashflow
        p3 = Precedent(
            id="PREC-COUNTER-CASHFLOW-01",
            title="Spend Stagnation Caused by Wildlife NGT Injunction, Not Cashflow",
            event_pattern={"event_type": "cost_progress_mismatch", "gap": -8.0},
            pattern_fingerprint=PatternFingerprint(
                event_type="cost_progress_mismatch",
                financial_velocity="behind",
                milestone_slippage="moderate",
                progress_variance="moderate",
                risk_direction="increasing",
                risk_velocity="moderate",
                approval_delay="high",
                contractor_delay="low"
            ),
            context=PrecedentContext(
                sector="Railways",
                project_type="Dedicated Freight Corridor",
                project_size_cr=2100.0,
                cost_band="Mega (>1000Cr)",
                stage_bracket="Early (<25%)",
                implementing_agency="DFCCIL",
                contract_type="EPC"
            ),
            evidence_pattern=["Disbursements halted", "Equipment parked", "Subcontractor complaints"],
            hypothesis_pattern=["CONTRACTOR_CASHFLOW_DISTRESS"],
            root_cause="NGT interim stay on eco-sensitive zone quarrying stopped earthwork despite solvent balance sheet.",
            root_cause_confidence=0.85,
            intervention={
                "action": "Expedited legal appeal with specialized counsel to vacate NGT interim injunction.",
                "intervention_class": "LEGAL_INTERVENTION"
            },
            expected_outcome={"stay_vacated": True},
            observed_outcome={"status": "positive", "notes": "Interim stay vacated in 45 days, work resumed.", "risk_delta": -6.0},
            outcome_quality=0.80,
            intervention_effectiveness=0.80,
            attribution_class="LIKELY_EFFECTIVE",
            memory_reliability=0.85,
            transferability_score=0.75,
            source_project_id="DFC-W-PKG-02",
            is_counterexample=True,
            counterexample_for_hypotheses=["CONTRACTOR_CASHFLOW_DISTRESS", "VENDOR_INSOLVENCY"],
            why_relevant="Expenditure halt appeared identical to contractor cashflow insolvency, but true cause was external regulatory injunction.",
            important_differences="Audited balance sheet showed strong liquidity; contractor was legally restrained from sourcing aggregate.",
            status="VALIDATED",
            application_count=1,
            success_count=1,
            failure_count=0
        )

        self._precedents[p1.id] = p1
        self._precedents[p2.id] = p2
        self._precedents[p3.id] = p3

    def save(self) -> None:
        if not self.persistence_path:
            return
        os.makedirs(os.path.dirname(os.path.abspath(self.persistence_path)), exist_ok=True)
        data = {k: v.to_dict() for k, v in self._precedents.items()}
        with open(self.persistence_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def load(self) -> None:
        if not self.persistence_path or not os.path.exists(self.persistence_path):
            return
        try:
            with open(self.persistence_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Merge loaded precedents into in-memory store
            for k, d in data.items():
                if isinstance(d, dict):
                    self._precedents[k] = Precedent.from_dict(d)
        except Exception:
            pass
