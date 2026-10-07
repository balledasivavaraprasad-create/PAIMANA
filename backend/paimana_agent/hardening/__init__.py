"""Phase 15 — Production Hardening Package.

Exports model version pinning, persistence tuning, restart safety, concurrency managers,
observability collectors, investigation replay, and security sanitization.
"""
from .model_registry import (
    ModelMetadata,
    ModelRegistryManager,
    ModelSecurityError,
    ModelVersionMismatchError,
)
from .persistence import PersistenceHardener
from .restart_safety import RestartRecoveryManager, RecoverySummary
from .concurrency import ThreadSafeStore, ConcurrencyTester
from .observability import (
    StructuredJsonFormatter,
    TraceSpan,
    DistributedTracer,
    PrometheusMetrics,
)
from .replay import InvestigationReplayEngine, ReplayVerificationResult
from .security import (
    SecuritySanitizer,
    SecurityRedactor,
    GovernanceSignatureManager,
)

__all__ = [
    "ModelMetadata",
    "ModelRegistryManager",
    "ModelSecurityError",
    "ModelVersionMismatchError",
    "PersistenceHardener",
    "RestartRecoveryManager",
    "RecoverySummary",
    "ThreadSafeStore",
    "ConcurrencyTester",
    "StructuredJsonFormatter",
    "TraceSpan",
    "DistributedTracer",
    "PrometheusMetrics",
    "InvestigationReplayEngine",
    "ReplayVerificationResult",
    "SecuritySanitizer",
    "SecurityRedactor",
    "GovernanceSignatureManager",
]
