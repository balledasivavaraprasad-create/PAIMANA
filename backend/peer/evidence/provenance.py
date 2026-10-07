"""Provenance Lineage Tracking & Input Hash Generator (ESS-02).

Ensures complete, auditable lineage for every evidence object, tracking raw data source,
tool versions, snapshot IDs, deterministic input hashes, and transformation history.
"""
from __future__ import annotations

import hashlib
import json
import time
from typing import Any, Dict, List, Optional

from .schemas import EvidenceProvenance


class ProvenanceTracker:
    """Tracks and validates evidence provenance and end-to-end source lineage."""

    @staticmethod
    def build_provenance(
        source: str,
        source_id: str,
        project_id: str,
        tool_name: str,
        raw_inputs: Optional[Dict[str, Any]] = None,
        snapshot_id: Optional[str] = None,
        observation_date: Optional[str] = None,
        calculation_method: str = "",
        tool_version: str = "1.0.0",
        algorithm_version: str = "1.0.0",
        transformations: Optional[List[str]] = None,
    ) -> EvidenceProvenance:
        # Compute deterministic sha256 input hash
        input_payload = raw_inputs or {}
        hash_str = json.dumps(input_payload, sort_keys=True, default=str)
        input_hash = hashlib.sha256(hash_str.encode("utf-8")).hexdigest()

        return EvidenceProvenance(
            source=source,
            source_id=source_id,
            project_id=project_id,
            snapshot_id=snapshot_id,
            observation_date=observation_date,
            ingestion_date=time.strftime("%Y-%m-%d %H:%M:%S"),
            tool_name=tool_name,
            tool_version=tool_version,
            algorithm_version=algorithm_version,
            input_hash=input_hash,
            calculation_method=calculation_method,
            transformation_history=list(transformations or []),
        )

    @classmethod
    def create_provenance(
        cls,
        project_id: str,
        tool_name: str,
        source: str,
        raw_inputs: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> EvidenceProvenance:
        return cls.build_provenance(
            source=source,
            source_id=kwargs.get("source_id", tool_name),
            project_id=project_id,
            tool_name=tool_name,
            raw_inputs=raw_inputs,
            **kwargs,
        )

    @staticmethod
    def validate_provenance_completeness(provenance: EvidenceProvenance) -> tuple[bool, List[str]]:
        """Verifies that all required audit fields are populated."""
        issues: List[str] = []
        if not provenance.source:
            issues.append("Missing source identity.")
        if not provenance.source_id:
            issues.append("Missing source tool or component ID.")
        if not provenance.project_id:
            issues.append("Missing canonical project ID.")
        if not provenance.input_hash:
            issues.append("Missing deterministic input hash.")
        if not provenance.observation_date and not provenance.snapshot_id:
            issues.append("Missing both observation date and snapshot ID (temporal anchor missing).")

        return (len(issues) == 0, issues)
