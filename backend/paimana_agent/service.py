"""Production HTTP / WSGI Service for PAIMANA Agent.

Provides production endpoints:
  - GET  /healthz : Liveness probe
  - GET  /readyz  : Readiness probe with database and model verification
  - GET  /metrics : Prometheus exposition format metrics
  - POST /evaluate: Evaluates project record with input sanitization & tracing
  - POST /replay/<id>: Deterministic audit replay of historical investigation
"""
from __future__ import annotations
import json
import logging
import os
import time
from typing import Optional

from flask import Flask, request, jsonify, Response

from .agent import MonitoringAgent, load_config
from .store import Store
from .hardening.persistence import PersistenceHardener
from .hardening.restart_safety import RestartRecoveryManager
from .hardening.security import SecuritySanitizer
from .hardening.observability import DistributedTracer, PrometheusMetrics
from .hardening.replay import InvestigationReplayEngine

logger = logging.getLogger("paimana_agent.service")


def create_app(config_path: str = "config.yaml", agent: Optional[MonitoringAgent] = None) -> Flask:
    app = Flask(__name__)

    # Initialize core components
    if agent is None:
        cfg = load_config(config_path)
        active_agent = MonitoringAgent.from_config(config_path)
    else:
        active_agent = agent

    # Persistence WAL configuration and startup recovery
    try:
        PersistenceHardener.configure_wal(active_agent.store)
        recovery_summary = RestartRecoveryManager.reconcile_on_startup(active_agent.store)
        logger.info(f"Startup recovery complete: {recovery_summary.to_dict()}")
    except Exception as ex:
        logger.warning(f"Could not apply SQLite WAL or startup recovery: {ex}")

    tracer = DistributedTracer.get_tracer()
    metrics = PrometheusMetrics.get_collector()

    @app.route("/healthz", methods=["GET"])
    def healthz():
        """Liveness probe: verifies process is alive and responsive."""
        return jsonify({
            "status": "healthy",
            "service": "paimana-monitoring-agent",
            "timestamp": time.time()
        }), 200

    @app.route("/readyz", methods=["GET"])
    def readyz():
        """Readiness probe: verifies database integrity and model readiness."""
        db_ok = PersistenceHardener.verify_integrity(active_agent.store)
        models_ready = bool(active_agent.models and "risk_score" in active_agent.models)
        is_ready = db_ok and models_ready

        status_code = 200 if is_ready else 503
        return jsonify({
            "ready": is_ready,
            "database_integrity_ok": db_ok,
            "models_ready": models_ready,
            "timestamp": time.time()
        }), status_code

    @app.route("/metrics", methods=["GET"])
    def get_metrics():
        """Prometheus metrics exposition endpoint."""
        data = metrics.export_metrics()
        return Response(data, mimetype="text/plain; version=0.0.4; charset=utf-8")

    @app.route("/evaluate", methods=["POST"])
    def evaluate():
        """Evaluates infrastructure project record with security sanitization."""
        span = tracer.start_span("http_evaluate_project")
        t0 = time.time()
        try:
            payload = request.get_json(force=True)
            if not isinstance(payload, dict):
                return jsonify({"error": "Request body must be a JSON object"}), 400

            # Security sanitization
            sanitized = {}
            for k, v in payload.items():
                if isinstance(v, str):
                    sanitized[k] = SecuritySanitizer.sanitize_text(v)
                else:
                    sanitized[k] = v

            # Validate project_code security
            if "project_code" in sanitized:
                sanitized["project_code"] = SecuritySanitizer.validate_project_code(sanitized["project_code"])

            event = request.args.get("event", "edit")
            report_month = request.args.get("report_month", None)

            # Evaluate project via MonitoringAgent
            result = active_agent.evaluate_project(sanitized, event=event, report_month=report_month)

            duration = time.time() - t0
            metrics.inc_counter("paimana_evaluations_total")
            metrics.observe_histogram("paimana_evaluation_duration_seconds", duration)
            if result.get("alert"):
                metrics.inc_counter("paimana_alerts_fired_total")

            span.finish(status="OK")
            response = jsonify(result)
            response.headers["traceparent"] = span.w3c_traceparent
            return response, 200
        except Exception as ex:
            span.finish(status="ERROR")
            metrics.inc_counter("paimana_evaluation_errors_total")
            logger.error(f"Error during evaluation: {ex}", exc_info=True)
            return jsonify({"error": str(ex)}), 500

    @app.route("/replay/<int:investigation_id>", methods=["POST"])
    def replay(investigation_id: int):
        """Audits and deterministically replays a historical investigation."""
        try:
            res = InvestigationReplayEngine.replay_investigation(active_agent.store, investigation_id)
            return jsonify(res.to_dict()), 200
        except ValueError as ex:
            return jsonify({"error": str(ex)}), 404
        except Exception as ex:
            logger.error(f"Error replaying investigation {investigation_id}: {ex}", exc_info=True)
            return jsonify({"error": str(ex)}), 500

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=8000)
