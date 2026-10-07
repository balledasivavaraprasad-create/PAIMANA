"""Evidence Subpackage for PAIMANA Agentic Layer."""
from .model import Evidence, EvidenceGroup, SourceLineage, ConfidenceUpdate, SOURCE_AUTHORITY
from .normalizer import EvidenceNormalizer
from .coverage import ExplanatoryCoverageEvaluator
from .contradiction import ContradictionDetector

from .confidence import EvidenceConfidenceEngine, GroundedConfidenceResult

__all__ = [
    "Evidence",
    "EvidenceGroup",
    "SourceLineage",
    "ConfidenceUpdate",
    "SOURCE_AUTHORITY",
    "EvidenceNormalizer",
    "ExplanatoryCoverageEvaluator",
    "ContradictionDetector",
    "EvidenceConfidenceEngine",
    "GroundedConfidenceResult",
]
