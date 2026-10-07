"""SQLite persistence: project versions, predictions, alerts, dedup state."""
from __future__ import annotations
import json, sqlite3, threading, time
from typing import Optional

import hashlib

SCHEMA = """
CREATE TABLE IF NOT EXISTS snapshots(
  project_code TEXT, report_index INTEGER, payload TEXT, updated_at REAL,
  PRIMARY KEY(project_code, report_index));
CREATE TABLE IF NOT EXISTS predictions(
  id INTEGER PRIMARY KEY AUTOINCREMENT, project_code TEXT, event TEXT, ts REAL,
  cost_overrun_pct REAL, slippage_months REAL, risk_score REAL, combined_score REAL,
  tier TEXT, detail TEXT);
CREATE TABLE IF NOT EXISTS alerts(
  id INTEGER PRIMARY KEY AUTOINCREMENT, project_code TEXT, ts REAL, severity TEXT,
  tier TEXT, risk_score REAL, reason TEXT, message TEXT, channels TEXT, delivered INTEGER,
  acknowledged INTEGER DEFAULT 0);

-- v2 additions: project-specific thresholds, event engine, investigations, project memory.
CREATE TABLE IF NOT EXISTS project_thresholds(
  project_code TEXT PRIMARY KEY, threshold REAL, updated_at REAL);
CREATE TABLE IF NOT EXISTS events(
  id INTEGER PRIMARY KEY AUTOINCREMENT, project_code TEXT, ts REAL, type TEXT, severity TEXT,
  message TEXT, payload TEXT, investigated INTEGER DEFAULT 0);
CREATE TABLE IF NOT EXISTS investigations(
  id INTEGER PRIMARY KEY AUTOINCREMENT, project_code TEXT, event_id INTEGER, ts REAL, report TEXT,
  approved INTEGER DEFAULT 0, approved_by TEXT, approved_at REAL);
CREATE TABLE IF NOT EXISTS issues(
  id INTEGER PRIMARY KEY AUTOINCREMENT, project_code TEXT, ts REAL, issue TEXT);
CREATE TABLE IF NOT EXISTS interventions(
  id INTEGER PRIMARY KEY AUTOINCREMENT, project_code TEXT, ts REAL, action TEXT,
  outcome TEXT, outcome_ts REAL);
CREATE TABLE IF NOT EXISTS automation_outbox(
  id INTEGER PRIMARY KEY AUTOINCREMENT, investigation_id INTEGER, task_type TEXT,
  payload TEXT, status TEXT DEFAULT 'pending', attempts INTEGER DEFAULT 0,
  last_error TEXT, created_at REAL, updated_at REAL, next_retry_at REAL DEFAULT 0);
CREATE TABLE IF NOT EXISTS project_checks(
  id INTEGER PRIMARY KEY AUTOINCREMENT, project_code TEXT, checked_at REAL,
  was_material_change INTEGER, reason TEXT);
"""


def compute_snapshot_hash(record: Optional[dict]) -> str:
    """Computes deterministic sha256 hash of core project attributes to detect material changes."""
    if not record:
        return ""
    core_keys = [
        "project_code", "project_name", "sector", "ministry", "implementing_agency",
        "state", "approval_date", "start_date", "original_completion_date",
        "revised_completion_date", "original_cost_cr", "revised_cost_cr",
        "cumulative_expenditure_cr", "physical_progress_pct", "report_month"
    ]
    sub = {}
    for k in core_keys:
        v = record.get(k)
        if v is not None:
            sub[k] = v
    canonical = json.dumps(sub, sort_keys=True, default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class Store:
    def __init__(self, path: str = "monitoring.db"):
        self._c = sqlite3.connect(path, check_same_thread=False)
        self._c.row_factory = sqlite3.Row
        self._lock = threading.Lock()
        with self._lock:
            self._c.executescript(SCHEMA)
            try:
                self._c.execute("ALTER TABLE automation_outbox ADD COLUMN next_retry_at REAL DEFAULT 0")
            except Exception:
                pass
            # Canonical snapshot columns migration
            for col, defn in [
                ("snapshot_id", "TEXT"),
                ("source", "TEXT DEFAULT 'SYSTEM_UPDATE'"),
                ("source_record_id", "TEXT"),
                ("snapshot_hash", "TEXT"),
                ("schema_version", "TEXT DEFAULT '1.0'"),
                ("observed_at", "REAL"),
                ("recorded_at", "REAL"),
                ("retrieved_at", "REAL"),
                ("reporting_period", "TEXT"),
                ("freshness_state", "TEXT DEFAULT 'FRESH'"),
            ]:
                try:
                    self._c.execute(f"ALTER TABLE snapshots ADD COLUMN {col} {defn}")
                except Exception:
                    pass

    def save_snapshot(self, code: str, report_index: int, record: dict, snapshot=None):
        now = time.time()
        s_id = getattr(snapshot, "snapshot_id", None) or f"SNAP-{code}-{int(now*1000)%1000000}"
        src = getattr(snapshot, "source", "SYSTEM_UPDATE")
        src_str = src.value if hasattr(src, "value") else str(src)
        src_rec_id = getattr(snapshot, "source_record_id", None)
        s_hash = getattr(snapshot, "snapshot_hash", None) or compute_snapshot_hash(record)
        s_ver = getattr(snapshot, "schema_version", "1.0")
        obs_at = getattr(snapshot, "observed_at", now)
        rec_at = getattr(snapshot, "recorded_at", now)
        ret_at = getattr(snapshot, "retrieved_at", now)
        rep_per = getattr(snapshot, "reporting_period", None) or record.get("report_month", "")
        fresh_st = getattr(snapshot, "freshness_state", "FRESH")
        fresh_str = fresh_st.value if hasattr(fresh_st, "value") else str(fresh_st)

        with self._lock, self._c:
            self._c.execute(
                """INSERT OR REPLACE INTO snapshots(
                    project_code, report_index, payload, updated_at,
                    snapshot_id, source, source_record_id, snapshot_hash,
                    schema_version, observed_at, recorded_at, retrieved_at,
                    reporting_period, freshness_state
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (code, report_index, json.dumps(record), now,
                 s_id, src_str, src_rec_id, s_hash, s_ver,
                 obs_at, rec_at, ret_at, rep_per, fresh_str)
            )

    def previous_snapshot(self, code: str, before_index: int) -> Optional[dict]:
        with self._lock:
            r = self._c.execute("SELECT * FROM snapshots WHERE project_code=? AND report_index<? "
                                "ORDER BY report_index DESC LIMIT 1", (code, before_index)).fetchone()
        if not r:
            return None
        d = json.loads(r["payload"])
        d["report_index"] = r["report_index"]
        keys = r.keys()
        for k in ("snapshot_id", "source", "source_record_id", "snapshot_hash",
                  "schema_version", "observed_at", "recorded_at", "retrieved_at",
                  "reporting_period", "freshness_state"):
            if k in keys and r[k] is not None:
                d[k] = r[k]
        return d

    def exists(self, code: str) -> bool:
        with self._lock:
            return self._c.execute("SELECT 1 FROM snapshots WHERE project_code=? LIMIT 1", (code,)).fetchone() is not None

    def last_prediction(self, code: str) -> Optional[dict]:
        with self._lock:
            r = self._c.execute("SELECT * FROM predictions WHERE project_code=? ORDER BY id DESC LIMIT 1", (code,)).fetchone()
        return dict(r) if r else None

    def add_prediction(self, code, event, res: dict):
        with self._lock, self._c:
            self._c.execute(
                "INSERT INTO predictions(project_code,event,ts,cost_overrun_pct,slippage_months,risk_score,combined_score,tier,detail) "
                "VALUES (?,?,?,?,?,?,?,?,?)",
                (code, event, time.time(), res["cost_overrun_pct"], res["slippage_months"], res["risk_score"],
                 res["combined_score"], res["tier"], json.dumps(res.get("detail", {}), default=str)))

    def last_alert(self, code: str) -> Optional[dict]:
        with self._lock:
            r = self._c.execute("SELECT * FROM alerts WHERE project_code=? ORDER BY id DESC LIMIT 1", (code,)).fetchone()
        return dict(r) if r else None

    def add_alert(self, code, severity, tier, score, reason, message, channels, delivered) -> int:
        with self._lock, self._c:
            cur = self._c.execute(
                "INSERT INTO alerts(project_code,ts,severity,tier,risk_score,reason,message,channels,delivered) VALUES (?,?,?,?,?,?,?,?,?)",
                (code, time.time(), severity, tier, score, reason, message, json.dumps(channels), int(delivered)))
            return cur.lastrowid

    def list_alerts(self, limit=50, only_open=False):
        q = "SELECT * FROM alerts " + ("WHERE acknowledged=0 " if only_open else "") + "ORDER BY id DESC LIMIT ?"
        with self._lock:
            return [dict(r) for r in self._c.execute(q, (limit,)).fetchall()]

    def acknowledge(self, alert_id: int):
        with self._lock, self._c:
            self._c.execute("UPDATE alerts SET acknowledged=1 WHERE id=?", (alert_id,))

    # ---------- v2: project-specific alert thresholds ----------
    def get_threshold(self, code: str, default: float) -> float:
        with self._lock:
            r = self._c.execute("SELECT threshold FROM project_thresholds WHERE project_code=?", (code,)).fetchone()
        return float(r["threshold"]) if r else float(default)

    def set_threshold(self, code: str, threshold: float):
        with self._lock, self._c:
            self._c.execute("INSERT OR REPLACE INTO project_thresholds VALUES (?,?,?)",
                            (code, threshold, time.time()))

    # ---------- v2: event log ----------
    def add_event(self, code, type_, severity, message, payload: dict) -> int:
        with self._lock, self._c:
            cur = self._c.execute(
                "INSERT INTO events(project_code,ts,type,severity,message,payload) VALUES (?,?,?,?,?,?)",
                (code, time.time(), type_, severity, message, json.dumps(payload, default=str)))
            return cur.lastrowid

    def list_events(self, code: Optional[str] = None, limit=50, uninvestigated_only=False):
        q = "SELECT * FROM events WHERE 1=1 "
        args: list = []
        if code:
            q += "AND project_code=? "; args.append(code)
        if uninvestigated_only:
            q += "AND investigated=0 "
        q += "ORDER BY id DESC LIMIT ?"; args.append(limit)
        with self._lock:
            return [dict(r) for r in self._c.execute(q, args).fetchall()]

    def mark_investigated(self, event_id: int):
        with self._lock, self._c:
            self._c.execute("UPDATE events SET investigated=1 WHERE id=?", (event_id,))

    def prediction_history(self, code: str, limit=24):
        """Risk-score time series for a project, oldest first -> project memory's 'risk history'."""
        with self._lock:
            rows = self._c.execute(
                "SELECT ts, risk_score, tier, cost_overrun_pct, slippage_months FROM predictions "
                "WHERE project_code=? ORDER BY id DESC LIMIT ?", (code, limit)).fetchall()
        return [dict(r) for r in rows][::-1]

    def all_project_codes(self) -> list[str]:
        with self._lock:
            return [r["project_code"] for r in self._c.execute(
                "SELECT DISTINCT project_code FROM snapshots").fetchall()]

    def latest_snapshot(self, code: str) -> Optional[dict]:
        with self._lock:
            r = self._c.execute("SELECT * FROM snapshots WHERE project_code=? "
                                "ORDER BY report_index DESC LIMIT 1", (code,)).fetchone()
        if not r:
            return None
        d = json.loads(r["payload"])
        d["report_index"] = r["report_index"]
        keys = r.keys()
        for k in ("snapshot_id", "source", "source_record_id", "snapshot_hash",
                  "schema_version", "observed_at", "recorded_at", "retrieved_at",
                  "reporting_period", "freshness_state"):
            if k in keys and r[k] is not None:
                d[k] = r[k]
        return d

    def record_project_check(self, code: str, was_material_change: bool, reason: str = ""):
        with self._lock, self._c:
            self._c.execute(
                "INSERT INTO project_checks(project_code, checked_at, was_material_change, reason) VALUES (?,?,?,?)",
                (code, time.time(), int(was_material_change), reason)
            )

    def last_project_check(self, code: str) -> Optional[dict]:
        with self._lock:
            r = self._c.execute("SELECT * FROM project_checks WHERE project_code=? ORDER BY id DESC LIMIT 1", (code,)).fetchone()
        return dict(r) if r else None

    def get_project(self, code: str) -> Optional[dict]:
        """Convenience alias for latest_snapshot."""
        return self.latest_snapshot(code)

    def peers(self, sector: str, exclude_code: str, limit=200) -> list[dict]:
        """Latest known snapshot for every OTHER project the agent has ever seen in this sector.
        This is the agent's own accumulated memory, not an external catalogue -> it starts thin
        and gets more useful the longer the monitoring engine has been running."""
        with self._lock:
            rows = self._c.execute(
                "SELECT s.project_code, s.payload FROM snapshots s "
                "INNER JOIN (SELECT project_code, MAX(report_index) mx FROM snapshots "
                "  WHERE project_code!=? GROUP BY project_code) l "
                "ON s.project_code=l.project_code AND s.report_index=l.mx LIMIT ?",
                (exclude_code, limit)).fetchall()
        out = []
        for r in rows:
            d = json.loads(r["payload"])
            if d.get("sector") == sector:
                out.append(d)
        return out

    # ---------- v2: investigations (agentic layer output, pending human approval) ----------
    def add_investigation(self, code: str, event_id: Optional[int], report: dict) -> int:
        with self._lock, self._c:
            cur = self._c.execute(
                "INSERT INTO investigations(project_code,event_id,ts,report) VALUES (?,?,?,?)",
                (code, event_id, time.time(), json.dumps(report, default=str)))
            return cur.lastrowid

    def approve_investigation(self, inv_id: int, approved_by: str = "") -> bool:
        """Idempotently approve an investigation. Returns True if newly approved, False if already approved."""
        with self._lock, self._c:
            row = self._c.execute("SELECT approved FROM investigations WHERE id=?", (inv_id,)).fetchone()
            if not row:
                return False
            if row["approved"]:
                return False  # Already approved (idempotent no-op)
            self._c.execute("UPDATE investigations SET approved=1, approved_by=?, approved_at=? WHERE id=?",
                            (approved_by, time.time(), inv_id))
            return True

    def get_investigation(self, inv_id: int) -> Optional[dict]:
        with self._lock:
            r = self._c.execute("SELECT * FROM investigations WHERE id=?", (inv_id,)).fetchone()
        return dict(r) if r else None

    def list_investigations(self, code: Optional[str] = None, limit=20):
        q = "SELECT * FROM investigations "
        args: list = []
        if code:
            q += "WHERE project_code=? "; args.append(code)
        q += "ORDER BY id DESC LIMIT ?"; args.append(limit)
        with self._lock:
            return [dict(r) for r in self._c.execute(q, args).fetchall()]

    # ---------- v3: automation outbox (durable, retryable webhook queue) ----------
    def enqueue_outbox(self, inv_id: int, task_type: str, payload: dict) -> int:
        """Idempotently enqueue an automation task in the outbox."""
        with self._lock, self._c:
            existing = self._c.execute(
                "SELECT id FROM automation_outbox WHERE investigation_id=? AND task_type=?",
                (inv_id, task_type)).fetchone()
            if existing:
                return existing["id"]
            cur = self._c.execute(
                "INSERT INTO automation_outbox(investigation_id, task_type, payload, status, attempts, created_at, updated_at) "
                "VALUES (?,?,?,?,?,?,?)",
                (inv_id, task_type, json.dumps(payload, default=str), "pending", 0, time.time(), time.time()))
            return cur.lastrowid

    def update_outbox(self, outbox_id: int, status: str, error: Optional[str] = None):
        with self._lock, self._c:
            self._c.execute(
                "UPDATE automation_outbox SET status=?, attempts=attempts+1, last_error=?, updated_at=? WHERE id=?",
                (status, error or "", time.time(), outbox_id))

    def claim_pending_outbox_tasks(self, max_tasks: int = 10, max_attempts: int = 4) -> list[dict]:
        """Atomically leases pending or due retry tasks by transitioning them to 'processing' in a single transaction."""
        now = time.time()
        with self._lock, self._c:
            rows = self._c.execute(
                "SELECT * FROM automation_outbox WHERE status IN ('pending', 'retrying') "
                "AND attempts < ? AND (next_retry_at <= ? OR next_retry_at IS NULL) "
                "ORDER BY id ASC LIMIT ?", (max_attempts, now, max_tasks)).fetchall()
            tasks = [dict(r) for r in rows]
            if tasks:
                ids = [t["id"] for t in tasks]
                placeholders = ",".join("?" * len(ids))
                self._c.execute(
                    f"UPDATE automation_outbox SET status='processing', updated_at=? WHERE id IN ({placeholders})",
                    [now] + ids
                )
            return tasks

    def mark_outbox_delivered(self, outbox_id: int):
        with self._lock, self._c:
            self._c.execute(
                "UPDATE automation_outbox SET status='delivered', updated_at=? WHERE id=?",
                (time.time(), outbox_id))

    def mark_outbox_retry(self, outbox_id: int, error: str, backoff_seconds: float):
        now = time.time()
        with self._lock, self._c:
            self._c.execute(
                "UPDATE automation_outbox SET status='retrying', attempts=attempts+1, "
                "last_error=?, updated_at=?, next_retry_at=? WHERE id=?",
                (error, now, now + backoff_seconds, outbox_id))

    def mark_outbox_dead_letter(self, outbox_id: int, error: str):
        with self._lock, self._c:
            self._c.execute(
                "UPDATE automation_outbox SET status='dead_letter', attempts=attempts+1, "
                "last_error=?, updated_at=? WHERE id=?",
                (error, time.time(), outbox_id))

    def list_outbox(self, status: Optional[str] = None, limit=50) -> list[dict]:
        with self._lock:
            if status:
                rows = self._c.execute(
                    "SELECT * FROM automation_outbox WHERE status=? ORDER BY id DESC LIMIT ?", (status, limit)).fetchall()
            else:
                rows = self._c.execute("SELECT * FROM automation_outbox ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        return [dict(r) for r in rows]

    # ---------- v2/v3: project memory (issues detected, interventions taken, outcomes) ----------
    def add_issue(self, code: str, issue: str):
        with self._lock, self._c:
            self._c.execute("INSERT INTO issues(project_code,ts,issue) VALUES (?,?,?)", (code, time.time(), issue))

    def list_issues(self, code: str, limit=20):
        with self._lock:
            return [dict(r) for r in self._c.execute(
                "SELECT * FROM issues WHERE project_code=? ORDER BY id DESC LIMIT ?", (code, limit)).fetchall()]

    def add_intervention(self, code: str, action: str) -> int:
        with self._lock, self._c:
            cur = self._c.execute("INSERT INTO interventions(project_code,ts,action) VALUES (?,?,?)",
                                  (code, time.time(), action))
            return cur.lastrowid

    def record_outcome(self, intervention_id: int, outcome: str):
        with self._lock, self._c:
            self._c.execute("UPDATE interventions SET outcome=?, outcome_ts=? WHERE id=?",
                            (outcome, time.time(), intervention_id))

    def list_interventions(self, code: str, limit=20):
        with self._lock:
            return [dict(r) for r in self._c.execute(
                "SELECT * FROM interventions WHERE project_code=? ORDER BY id DESC LIMIT ?", (code, limit)).fetchall()]

    def find_precedents(self, code: Optional[str] = None, limit=20) -> list[dict]:
        """Find past interventions that have a recorded real-world outcome (the learning loop)."""
        with self._lock:
            if code:
                rows = self._c.execute(
                    "SELECT * FROM interventions WHERE project_code=? AND outcome IS NOT NULL AND outcome != '' "
                    "ORDER BY id DESC LIMIT ?", (code, limit)).fetchall()
            else:
                rows = self._c.execute(
                    "SELECT * FROM interventions WHERE outcome IS NOT NULL AND outcome != '' "
                    "ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        return [dict(r) for r in rows]


class OutboxWorker:
    """Autonomous durable background worker that drains outbox queue with exponential backoff and dead-letter handling."""

    def __init__(self, store: Store, webhook_url: str = "", interval_sec: float = 2.0, max_attempts: int = 4):
        self.store = store
        self.webhook_url = webhook_url
        self.interval_sec = interval_sec
        self.max_attempts = max_attempts
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def drain_once(self) -> int:
        """Processes one batch of pending/due retry tasks."""
        tasks = self.store.claim_pending_outbox_tasks(max_tasks=10, max_attempts=self.max_attempts)
        processed = 0
        for t in tasks:
            tid = t["id"]
            attempts = t.get("attempts", 0) + 1
            try:
                if self.webhook_url:
                    import urllib.request
                    req = urllib.request.Request(
                        self.webhook_url,
                        data=json.dumps(t).encode("utf-8"),
                        headers={"Content-Type": "application/json"}
                    )
                    with urllib.request.urlopen(req, timeout=5) as resp:
                        if 200 <= resp.status < 300:
                            self.store.mark_outbox_delivered(tid)
                            processed += 1
                        else:
                            raise RuntimeError(f"HTTP status {resp.status}")
                else:
                    # In test/mock environment without external webhook, deliver directly
                    self.store.mark_outbox_delivered(tid)
                    processed += 1
            except Exception as ex:
                if attempts >= self.max_attempts:
                    self.store.mark_outbox_dead_letter(tid, str(ex))
                else:
                    backoff = min(60.0, (2 ** attempts) * 1.5)
                    self.store.mark_outbox_retry(tid, str(ex), backoff_seconds=backoff)
                processed += 1
        return processed

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def stop(self, timeout: float = 3.0):
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=timeout)

    def _run_loop(self):
        while not self._stop_event.is_set():
            try:
                self.drain_once()
            except Exception:
                pass
            self._stop_event.wait(self.interval_sec)

