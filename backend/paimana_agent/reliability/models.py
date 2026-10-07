"""Tool Reliability Data Models and Standardized Result Contract.

Defines the formal ToolResult contract, failure status taxonomy,
persistent reliability profiles, and the separation of execution reliability
from evidence reliability.
"""
from __future__ import annotations
import math
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class ToolResultStatus(str, Enum):
    """Standardized tool execution and result quality statuses."""
    SUCCESS = "SUCCESS"                            # High quality, complete evidence
    PARTIAL_SUCCESS = "PARTIAL_SUCCESS"            # Partial data returned; completeness < 1.0
    EMPTY_RESULT = "EMPTY_RESULT"                  # Valid query, but zero matching records found
    STALE_RESULT = "STALE_RESULT"                  # Returned data exceeds allowable age threshold
    TIMEOUT = "TIMEOUT"                            # Execution exceeded time deadline
    AUTH_FAILURE = "AUTH_FAILURE"                  # Permission or credential denial (non-retryable)
    RATE_LIMITED = "RATE_LIMITED"                  # Upstream throttled; backoff required
    SOURCE_UNAVAILABLE = "SOURCE_UNAVAILABLE"      # Upstream API/database offline
    SCHEMA_ERROR = "SCHEMA_ERROR"                  # Payload failed structural parsing/validation
    VALIDATION_ERROR = "VALIDATION_ERROR"          # Domain sanity check failed (e.g. false success)
    DEPENDENCY_FAILURE = "DEPENDENCY_FAILURE"      # Prerequisite service or file missing
    CIRCUIT_OPEN = "CIRCUIT_OPEN"                  # Tool temporarily disabled due to failure rate
    INTERNAL_ERROR = "INTERNAL_ERROR"              # Unexpected runtime exception
    FAILURE = "FAILURE"                            # Generic backward-compatible failure


class NormalizedStatus(str):
    """String subclass that treats 'PARTIAL' and 'PARTIAL_SUCCESS' as equivalent."""
    def __eq__(self, other: Any) -> bool:
        other_str = getattr(other, "value", other)
        if str(self) == "PARTIAL_SUCCESS" and other_str == "PARTIAL":
            return True
        if str(self) == "PARTIAL" and other_str == "PARTIAL_SUCCESS":
            return True
        return super().__eq__(other_str)

    def __hash__(self) -> int:
        return hash(str(self))


@dataclass
class ToolResult:
    """Standardized outcome of a specialist investigation tool execution."""
    tool_name: str
    status: str = "SUCCESS"  # ToolResultStatus value
    data: dict = field(default_factory=dict)
    summary: str = ""
    evidence_items: list[dict] = field(default_factory=list)
    error: Optional[str] = None
    execution_time_ms: float = 0.0

    # Evidence & Reliability Attributes
    completeness_score: float = 1.0      # Proportion of expected fields/records present [0.0, 1.0]
    freshness_score: float = 1.0         # Recency decay score [0.0, 1.0]
    source_metadata: dict = field(default_factory=dict)
    observed_at: Optional[float] = None
    retrieved_at: float = field(default_factory=time.time)
    warnings: list[str] = field(default_factory=list)
    retry_count: int = 0
    empty_reason: Optional[str] = None   # Why data was empty (e.g. NO_RECORDS_EXIST vs NOT_CONFIGURED)
    substitution_metadata: Optional[dict] = None  # Fallback provenance if substituted
    useful_evidence: bool = True         # False if technical success was unusable (false success)

    def __post_init__(self):
        # Backward compatibility for status strings
        if self.status in ("SUCCESS", "PARTIAL", "FAILURE", "UNAVAILABLE"):
            if self.status == "PARTIAL":
                self.status = NormalizedStatus(ToolResultStatus.PARTIAL_SUCCESS.value)
            elif self.status == "UNAVAILABLE":
                self.status = ToolResultStatus.SOURCE_UNAVAILABLE.value
            elif self.status == "SUCCESS":
                self.status = ToolResultStatus.SUCCESS.value
            elif self.status == "FAILURE":
                self.status = ToolResultStatus.FAILURE.value
        elif self.status == ToolResultStatus.PARTIAL_SUCCESS.value:
            self.status = NormalizedStatus(ToolResultStatus.PARTIAL_SUCCESS.value)

    @property
    def is_success(self) -> bool:
        return self.status in (ToolResultStatus.SUCCESS.value, ToolResultStatus.PARTIAL_SUCCESS.value)

    @property
    def is_usable_evidence(self) -> bool:
        return self.is_success and self.useful_evidence and self.status not in (
            ToolResultStatus.SCHEMA_ERROR.value,
            ToolResultStatus.VALIDATION_ERROR.value,
            ToolResultStatus.STALE_RESULT.value,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "tool": self.tool_name,
            "tool_name": self.tool_name,
            "status": self.status,
            "data": self.data,
            "summary": self.summary,
            "evidence_items": self.evidence_items,
            "error": self.error,
            "execution_time_ms": round(self.execution_time_ms, 2),
            "completeness_score": round(self.completeness_score, 3),
            "freshness_score": round(self.freshness_score, 3),
            "source_metadata": self.source_metadata,
            "observed_at": self.observed_at,
            "retrieved_at": self.retrieved_at,
            "warnings": list(self.warnings),
            "retry_count": self.retry_count,
            "empty_reason": self.empty_reason,
            "substitution_metadata": self.substitution_metadata,
            "useful_evidence": self.useful_evidence,
        }


@dataclass
class ToolReliabilityProfile:
    """Persistent operational and evidence reliability profile for an individual tool."""
    tool_name: str

    # Execution Reliability Metrics
    total_calls: int = 0
    successful_calls: int = 0
    timeout_calls: int = 0
    schema_error_calls: int = 0
    partial_result_calls: int = 0
    failed_calls: int = 0

    average_latency_ms: float = 200.0
    p95_latency_ms: float = 350.0

    # Evidence Quality Metrics
    data_completeness: float = 0.95
    data_freshness: float = 0.95
    source_authority: float = 0.85

    # Advanced Reliability & Recovery
    historical_recovery_rate: float = 0.80
    false_success_rate: float = 0.02
    useful_evidence_rate: float = 0.95

    last_success_at: Optional[float] = None
    last_failure_at: Optional[float] = None
    reliability_version: str = "1.0"
    reason_codes: list[str] = field(default_factory=list)

    @property
    def success_rate(self) -> float:
        if self.total_calls == 0:
            return 0.95
        return round(self.successful_calls / self.total_calls, 3)

    @property
    def timeout_rate(self) -> float:
        if self.total_calls == 0:
            return 0.02
        return round(self.timeout_calls / self.total_calls, 3)

    @property
    def execution_reliability(self) -> float:
        """Execution reliability [0.0, 1.0] reflecting uptime and technical success."""
        if self.total_calls == 0:
            return 0.95
        technical_ok = (self.successful_calls + 0.5 * self.partial_result_calls) / self.total_calls
        return round(min(1.0, max(0.05, technical_ok)), 3)

    @property
    def evidence_reliability(self) -> float:
        """Evidence reliability [0.0, 1.0] reflecting completeness, freshness, and authority."""
        score = (
            0.40 * self.source_authority +
            0.30 * self.data_completeness +
            0.30 * self.data_freshness
        )
        # Penalize if tool frequently produces false successes or unusable payloads
        penalty = min(0.30, self.false_success_rate * 2.0)
        return round(min(1.0, max(0.05, score - penalty)), 3)

    @property
    def composite_reliability(self) -> float:
        """Overall reliability weighting execution and evidentiary accuracy."""
        return round(0.50 * self.execution_reliability + 0.50 * self.evidence_reliability, 3)

    def record_call(self, result: ToolResult):
        """Updates profile metrics based on completed tool result."""
        self.total_calls += 1
        st = result.status

        if st == ToolResultStatus.SUCCESS.value:
            self.successful_calls += 1
            self.last_success_at = time.time()
        elif st == ToolResultStatus.PARTIAL_SUCCESS.value:
            self.partial_result_calls += 1
            self.last_success_at = time.time()
        elif st == ToolResultStatus.TIMEOUT.value:
            self.timeout_calls += 1
            self.last_failure_at = time.time()
        elif st == ToolResultStatus.SCHEMA_ERROR.value:
            self.schema_error_calls += 1
            self.last_failure_at = time.time()
        else:
            self.failed_calls += 1
            self.last_failure_at = time.time()

        if not result.useful_evidence and result.is_success:
            # False success detected
            prev_fs = self.false_success_rate * (self.total_calls - 1)
            self.false_success_rate = (prev_fs + 1.0) / self.total_calls

        # Update completeness and freshness rolling EMA
        alpha = 0.20
        self.data_completeness = round((1 - alpha) * self.data_completeness + alpha * result.completeness_score, 3)
        self.data_freshness = round((1 - alpha) * self.data_freshness + alpha * result.freshness_score, 3)

        # Update useful evidence rate
        is_useful = 1.0 if result.is_usable_evidence else 0.0
        self.useful_evidence_rate = round((1 - alpha) * self.useful_evidence_rate + alpha * is_useful, 3)

    def to_dict(self) -> dict[str, Any]:
        return {
            "tool_name": self.tool_name,
            "total_calls": self.total_calls,
            "success_rate": self.success_rate,
            "timeout_rate": self.timeout_rate,
            "execution_reliability": self.execution_reliability,
            "evidence_reliability": self.evidence_reliability,
            "composite_reliability": self.composite_reliability,
            "data_completeness": self.data_completeness,
            "data_freshness": self.data_freshness,
            "source_authority": self.source_authority,
            "useful_evidence_rate": self.useful_evidence_rate,
            "false_success_rate": round(self.false_success_rate, 3),
            "historical_recovery_rate": self.historical_recovery_rate,
            "average_latency_ms": round(self.average_latency_ms, 1),
            "p95_latency_ms": round(self.p95_latency_ms, 1),
            "last_success_at": self.last_success_at,
            "last_failure_at": self.last_failure_at,
            "reason_codes": list(self.reason_codes),
        }
