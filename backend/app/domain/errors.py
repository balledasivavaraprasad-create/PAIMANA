from enum import Enum
from typing import Any, Optional


class ErrorCode(str, Enum):
    PROJECT_NOT_FOUND = "PROJECT_NOT_FOUND"
    INVESTIGATION_NOT_FOUND = "INVESTIGATION_NOT_FOUND"
    ALERT_NOT_FOUND = "ALERT_NOT_FOUND"
    INTERVENTION_NOT_FOUND = "INTERVENTION_NOT_FOUND"
    VALIDATION_FAILED = "VALIDATION_FAILED"
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    CONFLICT = "CONFLICT"
    MODEL_UNAVAILABLE = "MODEL_UNAVAILABLE"
    AGENT_UNAVAILABLE = "AGENT_UNAVAILABLE"
    DATA_QUALITY_BLOCKED = "DATA_QUALITY_BLOCKED"
    DUPLICATE_EVENT = "DUPLICATE_EVENT"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class DomainError(Exception):
    def __init__(
        self,
        code: ErrorCode,
        message: str,
        http_status: int = 400,
        details: Optional[dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.code = code
        self.message = message
        self.http_status = http_status
        self.details = details or {}
