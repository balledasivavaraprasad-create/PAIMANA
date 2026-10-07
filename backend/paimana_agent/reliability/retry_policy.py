"""Bounded Retry Policy with Backoff & Jitter.

Prevents unbounded retry loops while providing resilient recovery for
transient timeouts, rate limits, and network hiccups.
"""
from __future__ import annotations
import math
import random
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class RetryPolicy:
    """Configurable retry rules bounded by attempt ceilings and backoff limits."""
    max_attempts: int = 2
    base_delay: float = 0.5
    max_delay: float = 5.0
    retryable_error_classes: list[str] = field(default_factory=lambda: [
        "TOOL_TIMEOUT",
        "TOOL_RATE_LIMITED",
        "TOOL_SOURCE_UNAVAILABLE",
    ])

    def should_retry(self, taxonomy_code: str, attempt: int) -> bool:
        """Determines whether a failed tool should be retried."""
        if attempt >= self.max_attempts:
            return False
        return taxonomy_code in self.retryable_error_classes

    def calculate_delay(self, attempt: int) -> float:
        """Calculates exponential backoff with random jitter."""
        exp = math.pow(2, max(0, attempt - 1))
        delay = min(self.max_delay, self.base_delay * exp)
        jitter = random.uniform(0.8, 1.2)
        return round(delay * jitter, 3)

    def to_dict(self) -> dict[str, Any]:
        return {
            "max_attempts": self.max_attempts,
            "base_delay": self.base_delay,
            "max_delay": self.max_delay,
            "retryable_error_classes": list(self.retryable_error_classes),
        }
