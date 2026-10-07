"""Tiny stdlib HTTP wrapper so any backend can call the agent (no extra dependencies).

  POST /projects                   add project     -> runs agent, returns predictions (+alert)
  PUT  /projects/<code>            edit project    -> runs agent
  GET  /alerts?open=1              list alerts
  POST /alerts/<id>/ack            acknowledge
  GET  /projects/<code>/memory     project intelligence memory (risk history/issues/interventions)
  GET  /events?project=<code>      event log (events.py taxonomy)
  GET  /investigations?project=<code>            investigation reports
  POST /investigations/<id>/approve              human sign-off; body: {"by": "name"} optional
  POST /investigations/<id>/outcome              body: {"action": "...", "outcome": "..."}
  PUT  /projects/<code>/threshold  body: {"threshold": 62}   set the per-project alert boundary
  POST /scan                       run one scheduled-scan pass now; body: [project, ...]
Run:  python -m paimana_agent.server config.yaml 8080
"""
import json, sys, re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs
from .agent import MonitoringAgent
from .features import ValidationError
from . import memory as M


def make_handler(agent: MonitoringAgent):
    class H(BaseHTTPRequestHandler):
        def _send(self, code, obj):
            b = json.dumps(obj, default=str).encode()
            self.send_response(code); self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)

        def _body(self):
            n = int(self.headers.get("Content-Length", 0))
            return json.loads(self.rfile.read(n) or b"{}")

        def _save(self, event, code=None):
            try:
                body = self._body()
                if code:
                    body["project_code"] = code
                self._send(200, agent.on_project_saved(body, event=event))
            except (ValidationError, json.JSONDecodeError) as e:
                self._send(422, {"error": str(e)})
            except Exception as e:
                self._send(500, {"error": f"{type(e).__name__}: {e}"})

        def do_POST(self):
            path = urlparse(self.path).path
            if path == "/projects":
                return self._save("add")
            if path == "/scan":
                try:
                    projects = self._body()
                    return self._send(200, agent.run_scheduled_scan(projects))
                except Exception as e:
                    return self._send(500, {"error": f"{type(e).__name__}: {e}"})
            m = re.fullmatch(r"/alerts/(\d+)/ack", path)
            if m:
                agent.store.acknowledge(int(m.group(1))); return self._send(200, {"ok": True})
            m = re.fullmatch(r"/investigations/(\d+)/approve", path)
            if m:
                body = self._body()
                inv_id = int(m.group(1))
                approved_by = body.get("by", "admin")
                is_new = agent.store.approve_investigation(inv_id, approved_by)
                if not is_new:
                    inv = agent.store.get_investigation(inv_id)
                    return self._send(200, {"ok": True, "newly_approved": False, "message": "Investigation was already approved", "investigation_id": inv_id})

                inv = agent.store.get_investigation(inv_id)
                report = json.loads(inv["report"]) if inv else {}
                iv_id = M.record_intervention(agent.store, report.get("project_code", ""),
                                              report.get("recommendation", ""))

                # Durable outbox enqueue (idempotent & retryable)
                n8n_payload = {
                    "event": "INVESTIGATION_APPROVED",
                    "investigation_id": inv_id,
                    "intervention_id": iv_id,
                    "approved_by": approved_by,
                    "project_code": report.get("project_code"),
                    "recommendation": report.get("recommendation"),
                    "confidence": report.get("confidence", "MEDIUM"),
                    "decision_trace": report.get("decision_trace", []),
                    "structured_evidence": report.get("structured_evidence", {})
                }
                outbox_id = agent.store.enqueue_outbox(inv_id, "N8N_DISPATCH", n8n_payload)

                # Downstream n8n automation dispatch
                n8n_cfg = agent.cfg.get("n8n", {})
                n8n_dispatched = False
                if n8n_cfg.get("enabled") and n8n_cfg.get("webhook_url"):
                    import urllib.request
                    try:
                        req = urllib.request.Request(
                            n8n_cfg["webhook_url"],
                            data=json.dumps(n8n_payload, default=str).encode(),
                            headers={"Content-Type": "application/json"}
                        )
                        with urllib.request.urlopen(req, timeout=n8n_cfg.get("timeout", 10)) as resp:
                            n8n_dispatched = (200 <= resp.status < 300)
                        if n8n_dispatched:
                            agent.store.update_outbox(outbox_id, "delivered")
                        else:
                            agent.store.update_outbox(outbox_id, "failed_retryable", f"HTTP {resp.status}")
                    except Exception as ex:
                        agent.store.update_outbox(outbox_id, "failed_retryable", str(ex))

                return self._send(200, {
                    "ok": True, "newly_approved": True, "intervention_id": iv_id,
                    "outbox_id": outbox_id, "n8n_dispatched": n8n_dispatched
                })
            m = re.fullmatch(r"/investigations/(\d+)/outcome", path)
            if m:
                body = self._body()
                M.record_outcome(agent.store, int(body["intervention_id"]), body.get("outcome", ""))
                return self._send(200, {"ok": True})
            self._send(404, {"error": "not found"})

        def do_PUT(self):
            path = urlparse(self.path).path
            m = re.fullmatch(r"/projects/([^/]+)", path)
            if m:
                return self._save("edit", m.group(1))
            m = re.fullmatch(r"/projects/([^/]+)/threshold", path)
            if m:
                body = self._body()
                agent.store.set_threshold(m.group(1), float(body["threshold"]))
                return self._send(200, {"ok": True})
            self._send(404, {"error": "not found"})

        def do_GET(self):
            u = urlparse(self.path)
            q = parse_qs(u.query)
            if u.path == "/alerts":
                return self._send(200, agent.store.list_alerts(only_open=q.get("open") == ["1"]))
            if u.path == "/events":
                return self._send(200, agent.store.list_events(code=(q.get("project") or [None])[0]))
            if u.path == "/investigations":
                return self._send(200, agent.store.list_investigations(code=(q.get("project") or [None])[0]))
            if u.path == "/outbox":
                return self._send(200, agent.store.list_outbox(status=(q.get("status") or [None])[0]))
            m = re.fullmatch(r"/projects/([^/]+)/memory", u.path)
            if m:
                return self._send(200, M.project_memory(agent.store, m.group(1)))
            self._send(404, {"error": "not found"})

        def log_message(self, *a):
            pass
    return H


if __name__ == "__main__":
    cfg = sys.argv[1] if len(sys.argv) > 1 else "config.yaml"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 8080
    ag = MonitoringAgent.from_config(cfg)
    print(f"agent listening on :{port}")
    ThreadingHTTPServer(("0.0.0.0", port), make_handler(ag)).serve_forever()
