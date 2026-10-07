"""Observability & Telemetry Tracer for PAIMANA Agentic Layer.

Provides non-blocking instrumented tracing for:
  - Investigation lifecycle
  - Supervisor reasoning & dynamic tool selection
  - Tool execution & latency
  - Hypothesis generation & changes
  - Contradiction detection
  - Dynamic confidence updates
  - Recommendation validation
  - Human approvals & outbox dispatches

Compatible with Langfuse if installed and configured, otherwise falls back gracefully
to internal non-blocking logging without blocking or failing execution.
"""
from __future__ import annotations
import logging
import time
from typing import Any, Optional

logger = logging.getLogger("paimana_agent.tracer")


class AgentTracer:
    """Non-blocking telemetry & execution tracer for agentic investigations."""

    def __init__(self, langfuse_client: Any = None):
        self.langfuse = langfuse_client
        self._enabled = True
        self._current_trace = None

    @classmethod
    def auto_configure(cls, config: Optional[dict] = None) -> AgentTracer:
        """Attempts to initialize Langfuse if configured in config.yaml."""
        if not config or not config.get("langfuse", {}).get("enabled", False):
            return cls(langfuse_client=None)
        try:
            from langfuse import Langfuse
            lf = Langfuse(
                public_key=config["langfuse"].get("public_key"),
                secret_key=config["langfuse"].get("secret_key"),
                host=config["langfuse"].get("host", "https://cloud.langfuse.com")
            )
            return cls(langfuse_client=lf)
        except Exception as e:
            logger.warning(f"Langfuse initialization skipped: {e}")
            return cls(langfuse_client=None)

    def trace_investigation_start(self, project_code: str, objective: str, triggers: list[str]) -> dict:
        event = {
            "type": "investigation_start",
            "project_code": project_code,
            "objective": objective,
            "triggers": triggers,
            "ts": time.time(),
        }
        logger.debug(f"[Trace Start] {project_code} - {objective}")
        if self.langfuse:
            try:
                self._current_trace = self.langfuse.trace(
                    name=f"investigation_{project_code}",
                    id=f"inv_{project_code}_{int(time.time() * 1000)}",
                    metadata={"objective": objective, "triggers": triggers, "project_code": project_code}
                )
            except Exception as ex:
                logger.debug(f"Langfuse trace_start failed: {ex}")
        return event

    def trace_supervisor_decision(self, step: int, thought: str, chosen_tool: Optional[str],
                                 evidence_gap: Optional[str] = None) -> dict:
        event = {
            "type": "supervisor_decision",
            "step": step,
            "thought": thought,
            "chosen_tool": chosen_tool,
            "evidence_gap": evidence_gap,
            "ts": time.time(),
        }
        logger.debug(f"[Supervisor Step {step}] {thought} -> Tool: {chosen_tool}")
        if self._current_trace:
            try:
                self._current_trace.generation(
                    name=f"supervisor_step_{step}",
                    input={"evidence_gap": evidence_gap, "step": step},
                    output={"thought": thought, "chosen_tool": chosen_tool},
                    metadata={"step": step, "tool": chosen_tool}
                )
            except Exception as ex:
                logger.debug(f"Langfuse generation failed: {ex}")
        return event

    def trace_tool_execution(self, tool_name: str, status: str, latency_ms: float,
                             observation_summary: str, error: Optional[str] = None) -> dict:
        event = {
            "type": "tool_execution",
            "tool": tool_name,
            "status": status,
            "latency_ms": latency_ms,
            "observation_summary": observation_summary,
            "error": error,
            "ts": time.time(),
        }
        logger.debug(f"[Tool Execution] {tool_name} [{status}] ({latency_ms:.1f}ms): {observation_summary}")
        if self._current_trace:
            try:
                self._current_trace.span(
                    name=f"tool_{tool_name}",
                    input={"tool": tool_name},
                    output={"summary": observation_summary, "error": error},
                    status_message=status,
                    metadata={"latency_ms": latency_ms}
                )
            except Exception as ex:
                logger.debug(f"Langfuse span failed: {ex}")
        return event

    def trace_hypothesis_update(self, active_hypotheses: list[dict]) -> dict:
        event = {
            "type": "hypothesis_update",
            "count": len(active_hypotheses),
            "hypotheses": [h.get("hypothesis") for h in active_hypotheses],
            "ts": time.time(),
        }
        logger.debug(f"[Hypothesis Update] {len(active_hypotheses)} active hypotheses")
        if self._current_trace:
            try:
                self._current_trace.event(
                    name="hypothesis_update",
                    metadata={"count": len(active_hypotheses), "hypotheses": [h.get("name") for h in active_hypotheses]}
                )
            except Exception as ex:
                logger.debug(f"Langfuse event failed: {ex}")
        return event

    def trace_contradiction(self, contradiction: dict) -> dict:
        event = {
            "type": "contradiction_detected",
            "metric": contradiction.get("metric_or_claim"),
            "source_a": contradiction.get("source_a"),
            "source_b": contradiction.get("source_b"),
            "resolution": contradiction.get("resolution_strategy"),
            "ts": time.time(),
        }
        logger.warning(f"[Contradiction Detected] {contradiction.get('metric_or_claim')}: {contradiction.get('source_a')} vs {contradiction.get('source_b')}")
        if self._current_trace:
            try:
                self._current_trace.event(
                    name="contradiction_detected",
                    metadata=contradiction
                )
            except Exception as ex:
                logger.debug(f"Langfuse event failed: {ex}")
        return event

    def trace_confidence_update(self, old_conf: str, new_conf: str, score: float, reasons: list[str]) -> dict:
        event = {
            "type": "confidence_update",
            "old_confidence": old_conf,
            "new_confidence": new_conf,
            "confidence_score": score,
            "reasons": reasons,
            "ts": time.time(),
        }
        logger.debug(f"[Confidence Update] {old_conf} -> {new_conf} (Score: {score:.2f})")
        if self._current_trace:
            try:
                self._current_trace.score(
                    name="evidence_confidence",
                    value=score,
                    comment=f"{old_conf} -> {new_conf} | " + ", ".join(reasons)
                )
            except Exception as ex:
                logger.debug(f"Langfuse score failed: {ex}")
        return event

    def trace_validation(self, recommendation: str, passed: bool, reasons: list[str]) -> dict:
        event = {
            "type": "recommendation_validation",
            "recommendation": recommendation,
            "passed": passed,
            "reasons": reasons,
            "ts": time.time(),
        }
        logger.debug(f"[Validation Check] Passed: {passed} - {reasons}")
        if self._current_trace:
            try:
                self._current_trace.event(
                    name="recommendation_validation",
                    metadata={"passed": passed, "reasons": reasons, "recommendation": recommendation[:100]}
                )
            except Exception as ex:
                logger.debug(f"Langfuse event failed: {ex}")
        return event

