"""Hard Eligibility Filter Engine for Peer Discovery.

Enforces mandatory non-negotiable compatibility rules before soft similarity scoring.
Guarantees that disqualified candidates are rejected with explicit, auditable reasons.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

from .context import PeerInvestigationContext
from .strategy_registry import PeerStrategyDefinition


class RejectionReason(str, Enum):
    """Explicit domain reasons for candidate disqualification."""
    SAME_PROJECT = "SAME_PROJECT"
    DUPLICATE_PROJECT = "DUPLICATE_PROJECT"
    SECTOR_MISMATCH = "SECTOR_MISMATCH"
    INCOMPATIBLE_PROJECT_TYPE = "INCOMPATIBLE_PROJECT_TYPE"
    TEMPORAL_INELIGIBILITY = "TEMPORAL_INELIGIBILITY"
    INVALID_SNAPSHOT = "INVALID_SNAPSHOT"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    INCOMPATIBLE_STATUS = "INCOMPATIBLE_STATUS"


@dataclass
class EligibilityEvaluation:
    """Outcome of hard eligibility evaluation for a single candidate."""
    candidate_code: str
    candidate_name: str
    is_eligible: bool
    rejection_reasons: List[RejectionReason] = field(default_factory=list)
    diagnostics: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "candidate_code": self.candidate_code,
            "candidate_name": self.candidate_name,
            "is_eligible": self.is_eligible,
            "rejection_reasons": [r.value for r in self.rejection_reasons],
            "diagnostics": self.diagnostics,
        }


class HardEligibilityFilter:
    """Evaluates candidates against strict non-negotiable compatibility rules."""

    def evaluate_candidate(
        self,
        target_project: Dict[str, Any],
        candidate: Dict[str, Any],
        strategy: PeerStrategyDefinition,
        context: Optional[PeerInvestigationContext] = None,
    ) -> EligibilityEvaluation:
        """Evaluates one candidate against mandatory eligibility criteria."""
        cand_code = str(candidate.get("project_code") or candidate.get("canonical_project_id", "")).strip()
        cand_name = str(candidate.get("project_name", "")).strip()
        target_code = str(target_project.get("project_code") or target_project.get("canonical_project_id", "")).strip()
        target_name = str(target_project.get("project_name", "")).strip()

        rejection_reasons: List[RejectionReason] = []
        diagnostics: Dict[str, str] = {}

        # 1. Check SAME_PROJECT
        if target_code and cand_code and target_code.lower() == cand_code.lower():
            rejection_reasons.append(RejectionReason.SAME_PROJECT)
            diagnostics["SAME_PROJECT"] = f"Candidate code '{cand_code}' matches target project code."

        if target_name and cand_name and target_name.lower() == cand_name.lower():
            if RejectionReason.SAME_PROJECT not in rejection_reasons:
                rejection_reasons.append(RejectionReason.SAME_PROJECT)
                diagnostics["SAME_PROJECT"] = f"Candidate name '{cand_name}' matches target project name."

        # 2. Check DUPLICATE_PROJECT (Aliases or Canonical ID matching)
        target_aliases = [str(a).lower() for a in target_project.get("aliases", []) if a]
        cand_aliases = [str(a).lower() for a in candidate.get("aliases", []) if a]
        if cand_code and cand_code.lower() in target_aliases:
            rejection_reasons.append(RejectionReason.DUPLICATE_PROJECT)
            diagnostics["DUPLICATE_PROJECT"] = f"Candidate code '{cand_code}' is an alias of target project."

        common_aliases = set(target_aliases).intersection(set(cand_aliases))
        if common_aliases:
            if RejectionReason.DUPLICATE_PROJECT not in rejection_reasons:
                rejection_reasons.append(RejectionReason.DUPLICATE_PROJECT)
                diagnostics["DUPLICATE_PROJECT"] = f"Shared aliases detected: {list(common_aliases)}"

        # 3. Check SECTOR_MISMATCH
        target_sector = str(target_project.get("sector", "")).strip()
        cand_sector = str(candidate.get("sector", "")).strip()
        if target_sector and cand_sector and target_sector.lower() != cand_sector.lower():
            rejection_reasons.append(RejectionReason.SECTOR_MISMATCH)
            diagnostics["SECTOR_MISMATCH"] = f"Sector mismatch: Target '{target_sector}' vs Candidate '{cand_sector}'."

        # 4. Check TEMPORAL_INELIGIBILITY (lookahead prevention)
        as_of_date = context.as_of_date if context else None
        if as_of_date:
            cand_date = str(candidate.get("observation_date") or candidate.get("snapshot_date", "")).strip()
            if cand_date and cand_date > as_of_date:
                rejection_reasons.append(RejectionReason.TEMPORAL_INELIGIBILITY)
                diagnostics["TEMPORAL_INELIGIBILITY"] = (
                    f"Candidate observation date '{cand_date}' is after investigation as_of_date '{as_of_date}'."
                )

        # 5. Check INVALID_SNAPSHOT (negative costs, out-of-range progress)
        cand_cost = _to_opt_float(candidate.get("original_cost_cr") or candidate.get("original_cost") or candidate.get("cost"))
        cand_progress = _to_opt_float(candidate.get("physical_progress_pct") or candidate.get("physical_progress") or candidate.get("progress"))
        if cand_cost is not None and cand_cost < 0:
            rejection_reasons.append(RejectionReason.INVALID_SNAPSHOT)
            diagnostics["INVALID_SNAPSHOT"] = f"Negative project cost reported: {cand_cost}."
        if cand_progress is not None and (cand_progress < 0.0 or cand_progress > 150.0):
            rejection_reasons.append(RejectionReason.INVALID_SNAPSHOT)
            diagnostics["INVALID_SNAPSHOT"] = f"Physical progress out of physical bounds: {cand_progress}%."

        # 6. Check INSUFFICIENT_DATA (ensure at least some essential attributes exist)
        has_cost = cand_cost is not None and cand_cost > 0
        has_progress = cand_progress is not None
        has_agency = bool(str(candidate.get("implementing_agency") or candidate.get("agency", "")).strip())
        if not (has_cost or has_progress or has_agency):
            rejection_reasons.append(RejectionReason.INSUFFICIENT_DATA)
            diagnostics["INSUFFICIENT_DATA"] = "Candidate lacks cost, physical progress, and implementing agency data."

        is_eligible = len(rejection_reasons) == 0

        return EligibilityEvaluation(
            candidate_code=cand_code,
            candidate_name=cand_name,
            is_eligible=is_eligible,
            rejection_reasons=rejection_reasons,
            diagnostics=diagnostics,
        )

    def filter_candidates(
        self,
        target_project: Dict[str, Any],
        candidates: List[Dict[str, Any]],
        strategy: PeerStrategyDefinition,
        context: Optional[PeerInvestigationContext] = None,
    ) -> Tuple[List[Dict[str, Any]], List[EligibilityEvaluation]]:
        """Filters candidate list into eligible projects and full transparent evaluations."""
        eligible_candidates: List[Dict[str, Any]] = []
        evaluations: List[EligibilityEvaluation] = []

        for cand in candidates:
            eval_res = self.evaluate_candidate(
                target_project=target_project,
                candidate=cand,
                strategy=strategy,
                context=context,
            )
            evaluations.append(eval_res)
            if eval_res.is_eligible:
                eligible_candidates.append(cand)

        return eligible_candidates, evaluations


def _to_opt_float(val: Any) -> Optional[float]:
    if val is None:
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None
