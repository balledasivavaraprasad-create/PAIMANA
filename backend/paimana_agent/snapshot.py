"""Canonical Project Snapshot and Freshness Model.

Defines the authoritative snapshot representation for infrastructure projects,
including cryptographic hashing, explicit snapshot sources, and discrete data
freshness states.
"""
from __future__ import annotations
import hashlib
import json
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, Optional

from .features import report_index


class SnapshotSource(str, Enum):
    """Authoritative snapshot source provenance."""
    PAIMANA_SYNC = "PAIMANA_SYNC"
    USER_EDIT = "USER_EDIT"
    IMPORT = "IMPORT"
    SYSTEM_UPDATE = "SYSTEM_UPDATE"
    SCHEDULED_SCAN = "SCHEDULED_SCAN"

    @classmethod
    def from_str(cls, val: Optional[str]) -> SnapshotSource:
        if not val:
            return cls.SYSTEM_UPDATE
        normalized = val.strip().upper()
        if normalized in ("ADD", "EDIT", "USER_EDIT"):
            return cls.USER_EDIT
        if normalized in ("SYNC", "PAIMANA_SYNC", "FILE_SYNC", "API_SYNC"):
            return cls.PAIMANA_SYNC
        if normalized in ("SCHEDULED", "SCHEDULED_SCAN", "SCAN"):
            return cls.SCHEDULED_SCAN
        if normalized in ("IMPORT", "BATCH_IMPORT"):
            return cls.IMPORT
        return cls.SYSTEM_UPDATE


class FreshnessState(str, Enum):
    """Discrete data freshness state of project observations."""
    FRESH = "FRESH"          # Observed within 0-1 months of reporting cycle
    AGING = "AGING"          # Observed within 2 months of reporting cycle
    STALE = "STALE"          # Observed >= 3 months behind reporting cycle
    UNAVAILABLE = "UNAVAILABLE"  # Missing reporting date or unobserved metrics


def compute_freshness(report_month: Optional[str], observed_at: Optional[float] = None) -> tuple[FreshnessState, int]:
    """Calculates discrete freshness state and monthly lag relative to calendar cycle."""
    if not report_month:
        return FreshnessState.UNAVAILABLE, 999
    try:
        r_idx = report_index(report_month)
        cur_idx = report_index(None)
        lag = max(0, cur_idx - r_idx)
        if lag <= 1:
            return FreshnessState.FRESH, lag
        elif lag == 2:
            return FreshnessState.AGING, lag
        else:
            return FreshnessState.STALE, lag
    except Exception:
        return FreshnessState.UNAVAILABLE, 999


@dataclass
class CanonicalSnapshot:
    """Authoritative canonical snapshot representation for continuous monitoring."""
    project_id: str
    snapshot_id: str
    reporting_period: str
    observed_at: Optional[float]
    recorded_at: float
    retrieved_at: float
    source: SnapshotSource
    source_record_id: Optional[str]
    snapshot_hash: str
    schema_version: str = "1.0"
    freshness_state: FreshnessState = FreshnessState.FRESH
    freshness_lag_months: int = 0
    payload: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_id": self.project_id,
            "project_code": self.project_id,
            "snapshot_id": self.snapshot_id,
            "reporting_period": self.reporting_period,
            "report_month": self.reporting_period,
            "observed_at": self.observed_at,
            "recorded_at": self.recorded_at,
            "retrieved_at": self.retrieved_at,
            "source": self.source.value if isinstance(self.source, SnapshotSource) else str(self.source),
            "source_record_id": self.source_record_id,
            "snapshot_hash": self.snapshot_hash,
            "schema_version": self.schema_version,
            "freshness_state": self.freshness_state.value if isinstance(self.freshness_state, FreshnessState) else str(self.freshness_state),
            "freshness_lag_months": self.freshness_lag_months,
            "payload": self.payload,
        }

    @classmethod
    def create(
        cls,
        project: Dict[str, Any],
        source: Optional[str] = None,
        source_record_id: Optional[str] = None,
        report_month: Optional[str] = None,
        retrieved_at: Optional[float] = None
    ) -> CanonicalSnapshot:
        """Constructs a CanonicalSnapshot from a project dictionary with deterministic hashing."""
        now = time.time()
        p_code = project.get("project_code") or project.get("project_id", "")
        rep_period = report_month or project.get("report_month") or project.get("reporting_period", "")
        
        # Calculate freshness
        freshness, lag = compute_freshness(rep_period)

        # Deterministic snapshot hash
        from .store import compute_snapshot_hash
        snap_hash = compute_snapshot_hash(project)
        snap_source = SnapshotSource.from_str(source)

        snap_id = f"SNAP-{p_code}-{snap_hash[:8]}"

        return cls(
            project_id=p_code,
            snapshot_id=snap_id,
            reporting_period=rep_period,
            observed_at=project.get("observed_at", now),
            recorded_at=now,
            retrieved_at=retrieved_at or now,
            source=snap_source,
            source_record_id=source_record_id or project.get("source_record_id"),
            snapshot_hash=snap_hash,
            schema_version="1.0",
            freshness_state=freshness,
            freshness_lag_months=lag,
            payload=project
        )
