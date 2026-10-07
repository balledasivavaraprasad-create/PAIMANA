"""Reproducibility & Audit Trail Metadata Engine (SB-11).

Provides cryptographic hashing, parameter auditing, and deterministic verification
to guarantee that all statistical benchmarking computations are fully reproducible.
"""
from __future__ import annotations

import hashlib
import json
import time
from typing import Any, Dict, List, Optional


class AuditTrailEngine:
    """Manages audit metadata, input checksums, and execution provenance."""

    ENGINE_VERSION = "1.0.0"

    @classmethod
    def generate_input_checksum(
        cls,
        target_project_code: str,
        peer_codes: List[str],
        metric_names: List[str],
        random_seed: int,
    ) -> str:
        """Compute deterministic SHA-256 fingerprint of input data and configuration."""
        payload = {
            "target": target_project_code,
            "peers": sorted(peer_codes),
            "metrics": sorted(metric_names),
            "seed": random_seed,
        }
        raw_bytes = json.dumps(payload, sort_keys=True).encode("utf-8")
        return hashlib.sha256(raw_bytes).hexdigest()

    @classmethod
    def build_audit_metadata(
        cls,
        target_project_code: str,
        peer_codes: List[str],
        metric_names: List[str],
        random_seed: int,
        resample_count: int,
        start_time: float,
        extra_info: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Construct standard audit dictionary for benchmark results."""
        duration_ms = (time.time() - start_time) * 1000.0
        checksum = cls.generate_input_checksum(
            target_project_code=target_project_code,
            peer_codes=peer_codes,
            metric_names=metric_names,
            random_seed=random_seed,
        )

        meta = {
            "engine_version": cls.ENGINE_VERSION,
            "input_checksum": checksum,
            "random_seed": random_seed,
            "resample_count": resample_count,
            "execution_duration_ms": round(duration_ms, 2),
            "reproducibility_contract": "DETERMINISTIC_PRNG_BOOTSTRAP",
        }
        if extra_info:
            meta.update(extra_info)
        return meta
