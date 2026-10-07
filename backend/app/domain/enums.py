from enum import Enum


class RiskTier(str, Enum):
    LOW = "Low"
    MODERATE = "Moderate"
    HIGH = "High"
    CRITICAL = "Critical"


class DataFreshness(str, Enum):
    FRESH = "Fresh"
    DELAYED = "Delayed"
    STALE = "Stale"
    UNAVAILABLE = "Unavailable"


class EventType(str, Enum):
    THRESHOLD_CROSSED = "THRESHOLD_CROSSED"
    RISK_ACCELERATING = "RISK_ACCELERATING"
    MILESTONE_DELAYED = "MILESTONE_DELAYED"
    PROGRESS_STALLED = "PROGRESS_STALLED"
    COST_PROGRESS_MISMATCH = "COST_PROGRESS_MISMATCH"
    DATA_STALE = "DATA_STALE"
    PEER_OUTLIER = "PEER_OUTLIER"
    COHORT_ANOMALY = "COHORT_ANOMALY"


class InvestigationStatus(str, Enum):
    TRIGGERED = "TRIGGERED"
    QUEUED = "QUEUED"
    INVESTIGATING = "INVESTIGATING"
    EVIDENCE_COLLECTION = "EVIDENCE_COLLECTION"
    HYPOTHESIS_REVIEW = "HYPOTHESIS_REVIEW"
    READY_FOR_DECISION = "READY_FOR_DECISION"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXECUTED = "EXECUTED"
    OUTCOME_RECORDED = "OUTCOME_RECORDED"
    CONCLUDED_INSUFFICIENT_EVIDENCE = "CONCLUDED_INSUFFICIENT_EVIDENCE"
    FAILED = "FAILED"
    CONCLUDED = "CONCLUDED"


class TerminationReason(str, Enum):
    EVIDENCE_SUFFICIENT = "evidence_sufficient"
    DECISION_READINESS_REACHED = "decision_readiness_reached"
    BUDGET_EXHAUSTED = "budget_exhausted"
    DIMINISHING_RETURNS = "diminishing_returns"
    UNRESOLVED_CONTRADICTION = "unresolved_contradiction"
    SOURCE_UNAVAILABLE = "source_unavailable"
    CONFIDENCE_BELOW_THRESHOLD = "confidence_below_decision_threshold"
    MANUAL_STOP = "manual_stop"


class RecommendationValidationStatus(str, Enum):
    CANDIDATE = "Candidate"
    VALIDATED = "Validated"
    INVALID = "Invalid"


class RecommendationApprovalStatus(str, Enum):
    PENDING_APPROVAL = "Pending approval"
    APPROVED = "Approved"
    REJECTED = "Rejected"


class InterventionExecutionStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    EXECUTED = "executed"
    COMPLETED = "completed"
    CLOSED = "closed"


class OutcomeStatus(str, Enum):
    RECORDED = "recorded"
    IMPROVED = "improved"
    UNCHANGED = "unchanged"
    WORSENED = "worsened"
    INCONCLUSIVE = "inconclusive"


class CohortQuality(str, Enum):
    HIGH_QUALITY = "HIGH_QUALITY"
    MODERATE = "MODERATE"
    WEAK = "WEAK"
    INSUFFICIENT = "INSUFFICIENT"


class PeerClassification(str, Enum):
    SIMILAR_TO_COHORT = "similar_to_peer_cohort"
    PROJECT_SPECIFIC_OUTLIER = "project_specific_outlier"
    COHORT_WIDE_DETERIORATION = "cohort_wide_deterioration"
    INSUFFICIENT_PEER_EVIDENCE = "insufficient_peer_evidence"
    UNCLEAR = "unclear"


class AlertStatus(str, Enum):
    PENDING = "PENDING"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    RESOLVED = "RESOLVED"


class AlertDeliveryStatus(str, Enum):
    QUEUED = "QUEUED"
    SENT = "SENT"
    RETRYING = "RETRYING"
    FAILED = "FAILED"
    DEAD_LETTER = "DEAD_LETTER"


class OutboxStatus(str, Enum):
    PENDING = "pending"
    DISPATCHED = "dispatched"
    FAILED_RETRYABLE = "failed_retryable"
    DEAD_LETTER = "dead_letter"
    DUPLICATE = "duplicate"


class ProductRole(str, Enum):
    VIEWER = "viewer"
    ANALYST = "analyst"
    INVESTIGATOR = "investigator"
    APPROVER = "approver"
    ADMINISTRATOR = "administrator"
