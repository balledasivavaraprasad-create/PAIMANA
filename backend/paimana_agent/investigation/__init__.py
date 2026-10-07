"""Dynamic Tool Selection & Uncertainty-Driven Evidence Acquisition Subsystem.

Provides:
- EvidenceNeed: First-class information gaps seeking empirical resolution.
- ToolCandidate & ToolSelectionRecord: Auditable candidate structures.
- EvidenceGapAnalyzer: Translates state uncertainties into prioritized needs.
- HypothesisDiscriminator: Computes dynamic information gain and hypothesis separation.
- ToolUtilityEvaluator: Multi-criteria utility engine.
- InvestigationBudget, InvestigationPhase, ConvergenceDetector: Execution bounds.
- DynamicInformationSeekingSelector: Integrated planner.
"""
from .evidence_need import EvidenceNeed
from .candidate import ToolCandidate, ToolSelectionRecord
from .gap_analyzer import EvidenceGapAnalyzer
from .discriminator import HypothesisDiscriminator
from .utility import ToolUtilityEvaluator
from .budget import InvestigationBudget, InvestigationPhase, ConvergenceDetector
from .selector import DynamicInformationSeekingSelector

__all__ = [
    "EvidenceNeed",
    "ToolCandidate",
    "ToolSelectionRecord",
    "EvidenceGapAnalyzer",
    "HypothesisDiscriminator",
    "ToolUtilityEvaluator",
    "InvestigationBudget",
    "InvestigationPhase",
    "ConvergenceDetector",
    "DynamicInformationSeekingSelector",
]
