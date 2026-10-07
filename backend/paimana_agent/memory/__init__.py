"""Institutional Knowledge & Precedent Learning Engine Subsystem.

Combines closed-loop institutional precedent memory, pattern fingerprint matching,
contextual transferability evaluation, temporal decay, failure warnings, and
counterexample reasoning with backward-compatible legacy project memory.
"""
from __future__ import annotations

# Legacy Project Intelligence API
from .legacy import (
    record_issue,
    record_intervention,
    record_outcome,
    project_memory,
    similar_past_pattern,
    _parse_outcome,
    learn_from_interventions,
)

# Core Models
from .models import (
    PrecedentStatus,
    AttributionClass,
    PatternFingerprint,
    PrecedentContext,
    PrecedentProvenance,
    Precedent,
    PrecedentBundle,
    InvestigationMemory,
)

# Pattern & Context Engines
from .pattern_fingerprint import (
    PatternFingerprintBuilder,
    PatternMatcher,
)
from .transferability import TransferabilityEvaluator
from .memory_decay import MemoryDecayManager
from .memory_reliability import MemoryReliabilityManager

# Outcome & Failure Reasoning
from .outcome_evaluator import OutcomeEvaluator
from .failure_memory import FailureMemoryManager
from .policy_memory import PolicyConstraint, PolicyMemoryStore

# Storage, Consolidation, and Retrieval
from .precedent_memory import PrecedentMemoryStore
from .memory_consolidator import MemoryConsolidator
from .memory_retriever import MemoryRetriever

__all__ = [
    # Legacy
    "record_issue",
    "record_intervention",
    "record_outcome",
    "project_memory",
    "similar_past_pattern",
    "_parse_outcome",
    "learn_from_interventions",
    # Models
    "PrecedentStatus",
    "AttributionClass",
    "PatternFingerprint",
    "PrecedentContext",
    "PrecedentProvenance",
    "Precedent",
    "PrecedentBundle",
    "InvestigationMemory",
    # Engines
    "PatternFingerprintBuilder",
    "PatternMatcher",
    "TransferabilityEvaluator",
    "MemoryDecayManager",
    "MemoryReliabilityManager",
    "OutcomeEvaluator",
    "FailureMemoryManager",
    "PolicyConstraint",
    "PolicyMemoryStore",
    "PrecedentMemoryStore",
    "MemoryConsolidator",
    "MemoryRetriever",
]
