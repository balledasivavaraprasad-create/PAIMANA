"""Candidate Generation Engine for Question-Conditioned Peer Discovery.

Retrieves a broad, pre-filtered pool of potentially comparable project records
from the repository, decoupling candidate retrieval from similarity scoring.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

from ..repository import ProjectRepository
from .context import PeerInvestigationContext
from .strategy_registry import PeerStrategyDefinition


@dataclass
class CandidateGenerationResult:
    """Outcome of candidate generation with retrieval metadata."""
    candidates: List[Dict[str, Any]]
    total_candidates: int
    total_scanned: int
    filters_applied: Dict[str, Any]
    retrieval_duration_ms: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_candidates": self.total_candidates,
            "total_scanned": self.total_scanned,
            "filters_applied": self.filters_applied,
            "retrieval_duration_ms": round(self.retrieval_duration_ms, 2),
        }


class CandidateGenerator:
    """Scalable candidate generation service supporting database and in-memory prefiltering."""

    def __init__(self, repository: ProjectRepository):
        self.repository = repository

    def generate_candidates(
        self,
        target_project: Dict[str, Any],
        strategy: PeerStrategyDefinition,
        context: Optional[PeerInvestigationContext] = None,
        max_candidates: int = 100,
        enable_cost_prefilter: bool = True,
    ) -> CandidateGenerationResult:
        """Retrieves and pre-filters candidates from the repository."""
        start_time = time.perf_counter()

        target_code = str(target_project.get("project_code") or target_project.get("canonical_project_id", "")).strip()
        target_sector = str(target_project.get("sector", "")).strip()
        target_cost = _to_float(target_project.get("original_cost_cr") or target_project.get("original_cost") or target_project.get("cost"))

        filters_applied: Dict[str, Any] = {
            "exclude_target_code": target_code,
            "sector": target_sector or None,
            "max_candidates": max_candidates,
        }

        # 1. Primary repository candidate retrieval (with sector filter if applicable)
        raw_candidates = self.repository.get_candidates(
            sector=target_sector if target_sector else None,
            exclude_code=target_code if target_code else None,
        )
        total_scanned = len(raw_candidates)

        # 2. In-memory pre-filtering and deduplication
        seen_codes: Set[str] = set()
        seen_names: Set[str] = set()
        if target_code:
            seen_codes.add(target_code.lower())
        target_name = str(target_project.get("project_name", "")).strip().lower()
        if target_name:
            seen_names.add(target_name)

        filtered: List[Dict[str, Any]] = []

        # Cost tolerance ratio from strategy
        cost_ratio = strategy.cost_tolerance_ratio if enable_cost_prefilter else None
        min_cost: Optional[float] = None
        max_cost: Optional[float] = None
        if cost_ratio is not None and target_cost is not None and target_cost > 0:
            min_cost = target_cost * max(0.1, 1.0 - cost_ratio)
            max_cost = target_cost * (1.0 + cost_ratio * 2.0)
            filters_applied["cost_bounds"] = {"min": round(min_cost, 2), "max": round(max_cost, 2)}

        for cand in raw_candidates:
            code = str(cand.get("project_code") or cand.get("canonical_project_id", "")).strip()
            name = str(cand.get("project_name", "")).strip()

            # Deduplication
            if not code or code.lower() in seen_codes:
                continue
            if name and name.lower() in seen_names:
                continue

            # Optional cost bounds pre-filter (only if candidate cost is populated)
            cand_cost = _to_float(cand.get("original_cost_cr") or cand.get("original_cost") or cand.get("cost"))
            if min_cost is not None and max_cost is not None and cand_cost is not None and cand_cost > 0:
                if cand_cost < min_cost or cand_cost > max_cost:
                    continue

            seen_codes.add(code.lower())
            if name:
                seen_names.add(name.lower())
            filtered.append(cand)

            if len(filtered) >= max_candidates:
                break

        duration_ms = (time.perf_counter() - start_time) * 1000.0

        return CandidateGenerationResult(
            candidates=filtered,
            total_candidates=len(filtered),
            total_scanned=total_scanned,
            filters_applied=filters_applied,
            retrieval_duration_ms=duration_ms,
        )


def _to_float(val: Any) -> Optional[float]:
    if val is None:
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None
