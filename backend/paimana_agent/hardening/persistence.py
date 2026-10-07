"""Production Persistence Hardening for SQLite.

Configures Write-Ahead Logging (WAL), busy timeouts, synchronous mode,
periodic WAL checkpointing, and database integrity verification.
"""
from __future__ import annotations
import logging
import sqlite3
from typing import Optional, Union

from ..store import Store

logger = logging.getLogger("paimana_agent.hardening.persistence")


class PersistenceHardener:
    """Manages SQLite production tuning, WAL pragmas, and checkpointing."""

    @staticmethod
    def configure_wal(target: Union[sqlite3.Connection, Store], busy_timeout_ms: int = 10000) -> dict:
        """Applies production pragmas to SQLite connection: WAL mode, synchronous NORMAL, busy timeout."""
        if isinstance(target, Store):
            conn = target._c
            lock = target._lock
        else:
            conn = target
            lock = None

        def _exec():
            # Apply production pragmas
            conn.execute(f"PRAGMA busy_timeout = {busy_timeout_ms};")
            # In-memory databases do not support WAL mode
            db_path = conn.execute("PRAGMA database_list").fetchone()
            path_str = db_path[2] if db_path and len(db_path) > 2 else ""
            if path_str and path_str != "":
                conn.execute("PRAGMA journal_mode = WAL;")
                conn.execute("PRAGMA synchronous = NORMAL;")
            conn.execute("PRAGMA foreign_keys = ON;")

            cur_mode = conn.execute("PRAGMA journal_mode;").fetchone()[0]
            cur_sync = conn.execute("PRAGMA synchronous;").fetchone()[0]
            cur_timeout = conn.execute("PRAGMA busy_timeout;").fetchone()[0]
            return {
                "journal_mode": cur_mode,
                "synchronous": cur_sync,
                "busy_timeout_ms": cur_timeout,
            }

        if lock:
            with lock:
                res = _exec()
        else:
            res = _exec()

        logger.info(f"Configured SQLite persistence: journal_mode={res['journal_mode']}, timeout={res['busy_timeout_ms']}ms")
        return res

    @staticmethod
    def checkpoint_wal(target: Union[sqlite3.Connection, Store], mode: str = "PASSIVE") -> tuple[int, int, int]:
        """Runs PRAGMA wal_checkpoint to consolidate WAL pages into main DB."""
        if isinstance(target, Store):
            conn = target._c
            lock = target._lock
        else:
            conn = target
            lock = None

        query = f"PRAGMA wal_checkpoint({mode});"
        if lock:
            with lock:
                row = conn.execute(query).fetchone()
        else:
            row = conn.execute(query).fetchone()

        # Returns (busy, log, checkpointed)
        return (row[0], row[1], row[2]) if row else (0, 0, 0)

    @staticmethod
    def verify_integrity(target: Union[sqlite3.Connection, Store]) -> bool:
        """Verifies database integrity using PRAGMA integrity_check."""
        if isinstance(target, Store):
            conn = target._c
            lock = target._lock
        else:
            conn = target
            lock = None

        if lock:
            with lock:
                row = conn.execute("PRAGMA integrity_check;").fetchone()
        else:
            row = conn.execute("PRAGMA integrity_check;").fetchone()

        result = str(row[0]) if row else ""
        is_ok = result.lower() == "ok"
        if not is_ok:
            logger.error(f"Database integrity check failed: {result}")
        return is_ok
