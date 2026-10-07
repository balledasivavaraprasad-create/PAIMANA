"""Evidence and Semantic Safety Subsystem for PAIMANA (ESS-01 to ESS-10).

Provides canonical evidence representations, cryptographic provenance lineage,
multi-dimensional reliability profiling, semantic graph relations, 5-level claim
hierarchy enforcement, causal-claim guards, contradiction tracking, pre-report
safety audits, and bounded executive report synthesis.
"""
from .causal_guard import CausalClaimGuard, RULES_CATALOG
from .claims import ClaimManager, ClaimValidator
from .contradiction import ContradictionDetector
from .extraction import EvidenceExtractor
from .provenance import ProvenanceTracker
from .registry import EvidenceRegistry
from .relations import SemanticRelationGraph
from .reliability import ReliabilityEvaluator
from .schemas import (
    Claim,
    ClaimLevel,
    ClaimStatus,
    ContradictionRecord,
    Evidence,
    EvidenceProvenance,
    EvidenceRelationType,
    EvidenceReliability,
    ReliabilityTier,
    SemanticSafeReport,
    SemanticSafetyAuditReport,
    SemanticSafetyRule,
)
from .service import EvidenceAndSemanticSafetyService
from .synthesis import SemanticReportSynthesizer
from .unsupported_claims import UnsupportedClaimAuditor

__all__ = [
    "Evidence",
    "EvidenceProvenance",
    "EvidenceReliability",
    "ReliabilityTier",
    "EvidenceRelationType",
    "ClaimLevel",
    "ClaimStatus",
    "Claim",
    "SemanticRelation",
    "ContradictionRecord",
    "SemanticSafetyRule",
    "SemanticSafetyAuditReport",
    "SemanticSafeReport",
    "EvidenceRegistry",
    "ProvenanceTracker",
    "ReliabilityEvaluator",
    "EvidenceExtractor",
    "SemanticRelationGraph",
    "ClaimValidator",
    "ClaimManager",
    "CausalClaimGuard",
    "RULES_CATALOG",
    "ContradictionDetector",
    "UnsupportedClaimAuditor",
    "SemanticReportSynthesizer",
    "EvidenceAndSemanticSafetyService",
]
