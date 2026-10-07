from typing import Any, Generic, Optional, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")


class Unavailable(BaseModel):
    """Explicit absence. Never encode unknown as 0."""

    availability: bool = False
    reason: str
    value: None = None


class Availability(BaseModel, Generic[T]):
    availability: bool = True
    reason: Optional[str] = None
    value: Optional[T] = None

    @classmethod
    def of(cls, value: T) -> "Availability[T]":
        return cls(availability=True, reason=None, value=value)

    @classmethod
    def missing(cls, reason: str) -> "Availability[T]":
        return cls(availability=False, reason=reason, value=None)


def optional_metric(value: Any, reason: str = "unavailable") -> Optional[float]:
    """Return a numeric metric only when it is a real observation.

    Zero is a valid observed value. None means unknown.
    """
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None


def metric_payload(value: Any, reason_if_missing: str) -> dict:
    if value is None:
        return {"availability": False, "reason": reason_if_missing, "value": None}
    return {"availability": True, "reason": None, "value": value}
