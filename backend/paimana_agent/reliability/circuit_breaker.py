"""Tool Circuit Breaker.

Prevents repeated execution of failing tools across investigations, protecting
upstream services and freeing agent cycles for working alternatives.
"""
from __future__ import annotations
import time
from enum import Enum
from typing import Any, Optional


class CircuitBreakerState(str, Enum):
    """Operational states of a tool circuit breaker."""
    CLOSED = "CLOSED"        # Normal operation: requests pass through
    OPEN = "OPEN"            # Tripped: requests blocked immediately
    HALF_OPEN = "HALF_OPEN"  # Cooldown expired: probe request allowed


class CircuitBreaker:
    """Finite state machine protecting tools from cascading or repeated failure."""

    def __init__(
        self,
        tool_name: str,
        failure_threshold: int = 3,
        cooldown_seconds: float = 30.0,
        half_open_probes: int = 1,
    ):
        self.tool_name = tool_name
        self.failure_threshold = failure_threshold
        self.cooldown_seconds = cooldown_seconds
        self.half_open_probes = half_open_probes

        self.consecutive_failures = 0
        self.consecutive_successes = 0
        self.state = CircuitBreakerState.CLOSED
        self.last_state_change = time.time()
        self.last_failure_time: Optional[float] = None

    def can_execute(self) -> bool:
        """Determines whether a tool invocation is permitted."""
        now = time.time()
        if self.state == CircuitBreakerState.CLOSED:
            return True

        if self.state == CircuitBreakerState.OPEN:
            # Check if cooldown has elapsed
            if (now - self.last_state_change) >= self.cooldown_seconds:
                self.state = CircuitBreakerState.HALF_OPEN
                self.last_state_change = now
                return True
            return False

        if self.state == CircuitBreakerState.HALF_OPEN:
            return True

        return False

    def record_success(self):
        """Records a successful tool execution."""
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.consecutive_successes += 1
            if self.consecutive_successes >= self.half_open_probes:
                self.state = CircuitBreakerState.CLOSED
                self.consecutive_failures = 0
                self.consecutive_successes = 0
                self.last_state_change = time.time()
        else:
            self.consecutive_failures = 0

    def record_failure(self):
        """Records a failed tool execution."""
        self.last_failure_time = time.time()
        self.consecutive_failures += 1

        if self.state == CircuitBreakerState.HALF_OPEN:
            # Probe failed -> reopen immediately
            self.state = CircuitBreakerState.OPEN
            self.last_state_change = time.time()
            self.consecutive_successes = 0
        elif self.consecutive_failures >= self.failure_threshold:
            self.state = CircuitBreakerState.OPEN
            self.last_state_change = time.time()

    def to_dict(self) -> dict[str, Any]:
        return {
            "tool_name": self.tool_name,
            "state": self.state.value,
            "consecutive_failures": self.consecutive_failures,
            "consecutive_successes": self.consecutive_successes,
            "failure_threshold": self.failure_threshold,
            "cooldown_seconds": self.cooldown_seconds,
            "can_execute": self.can_execute(),
            "last_state_change": self.last_state_change,
        }
