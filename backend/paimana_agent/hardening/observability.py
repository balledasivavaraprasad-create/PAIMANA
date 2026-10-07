"""Observability Subsystem: Structured JSON Logging, OpenTelemetry Tracing, and Prometheus Metrics.

Provides end-to-end production visibility, distributed request tracing with W3C traceparents,
and OpenMetrics format generation for Prometheus / Grafana monitoring.
"""
from __future__ import annotations
import json
import logging
import os
import sys
import threading
import time
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional

logger = logging.getLogger("paimana_agent.hardening.observability")


class StructuredJsonFormatter(logging.Formatter):
    """Formats log records as structured single-line JSON objects."""

    def format(self, record: logging.LogRecord) -> str:
        log_obj = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(record.created)),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "line": record.lineno,
        }
        # Add trace context if attached
        if hasattr(record, "trace_id"):
            log_obj["trace_id"] = getattr(record, "trace_id")
        if hasattr(record, "span_id"):
            log_obj["span_id"] = getattr(record, "span_id")
        if hasattr(record, "project_code"):
            log_obj["project_code"] = getattr(record, "project_code")

        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_obj, default=str)


@dataclass
class TraceSpan:
    trace_id: str
    span_id: str
    parent_span_id: Optional[str]
    name: str
    start_time: float
    end_time: Optional[float] = None
    attributes: Dict[str, Any] = field(default_factory=dict)
    status: str = "OK"

    def finish(self, status: str = "OK"):
        self.end_time = time.time()
        self.status = status

    @property
    def duration_ms(self) -> float:
        end = self.end_time or time.time()
        return (end - self.start_time) * 1000.0

    @property
    def w3c_traceparent(self) -> str:
        return f"00-{self.trace_id.replace('-', '')[:32].zfill(32)}-{self.span_id.replace('-', '')[:16].zfill(16)}-01"


class DistributedTracer:
    """Thread-safe distributed tracer producing W3C-compatible trace spans."""
    _instance = None
    _lock = threading.Lock()

    def __init__(self):
        self.spans: List[TraceSpan] = []
        self._span_lock = threading.Lock()

    @classmethod
    def get_tracer(cls) -> DistributedTracer:
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    def start_span(self, name: str, trace_id: Optional[str] = None, parent_span_id: Optional[str] = None) -> TraceSpan:
        now = time.time()
        t_id = trace_id or f"trace_{int(now*1000)}_{os.urandom(4).hex()}"
        s_id = f"span_{os.urandom(4).hex()}"
        span = TraceSpan(trace_id=t_id, span_id=s_id, parent_span_id=parent_span_id, name=name, start_time=now)
        with self._span_lock:
            self.spans.append(span)
            if len(self.spans) > 500:
                self.spans = self.spans[-250:]
        return span


class PrometheusMetrics:
    """Thread-safe in-memory metric collector emitting standard Prometheus OpenMetrics."""
    _instance = None
    _lock = threading.Lock()

    def __init__(self):
        self._counters: Dict[str, float] = {}
        self._gauges: Dict[str, float] = {}
        self._histograms: Dict[str, List[float]] = {}
        self._metric_lock = threading.Lock()

        # Initialize core default metrics
        self.set_gauge("paimana_up", 1.0)
        self.set_gauge("paimana_active_alerts", 0.0)
        self.set_gauge("paimana_model_calibration_error_mace", 0.0)

    @classmethod
    def get_collector(cls) -> PrometheusMetrics:
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    def inc_counter(self, name: str, value: float = 1.0):
        with self._metric_lock:
            self._counters[name] = self._counters.get(name, 0.0) + value

    def set_gauge(self, name: str, value: float):
        with self._metric_lock:
            self._gauges[name] = float(value)

    def observe_histogram(self, name: str, value: float):
        with self._metric_lock:
            if name not in self._histograms:
                self._histograms[name] = []
            self._histograms[name].append(float(value))
            if len(self._histograms[name]) > 200:
                self._histograms[name] = self._histograms[name][-100:]

    def export_metrics(self) -> str:
        """Renders metrics in Prometheus / OpenMetrics plain-text exposition format."""
        lines = []
        with self._metric_lock:
            # Counters
            for name, val in sorted(self._counters.items()):
                lines.append(f"# TYPE {name} counter")
                lines.append(f"{name} {val}")

            # Gauges
            for name, val in sorted(self._gauges.items()):
                lines.append(f"# TYPE {name} gauge")
                lines.append(f"{name} {val}")

            # Histograms (exporting count, sum, and avg)
            for name, vals in sorted(self._histograms.items()):
                lines.append(f"# TYPE {name} summary")
                s = sum(vals)
                c = len(vals)
                lines.append(f"{name}_count {c}")
                lines.append(f"{name}_sum {s:.4f}")
                if c > 0:
                    lines.append(f"{name}_avg {s/c:.4f}")

        return "\n".join(lines) + "\n"
