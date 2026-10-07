"""Production Concurrency Management and Multi-Worker Safety.

Ensures thread-safe Store operations, prevents SQLite lock contention under high
load, and provides a multi-worker concurrency stress tester.
"""
from __future__ import annotations
import concurrent.futures
import logging
import threading
import time
from typing import Dict, List, Any, Callable

from ..store import Store
from .persistence import PersistenceHardener

logger = logging.getLogger("paimana_agent.hardening.concurrency")


class ThreadSafeStore:
    """Thread-safe facade over Store with re-entrant locking and WAL tuning."""

    def __init__(self, store: Store):
        self._store = store
        self._rlock = threading.RLock()
        # Ensure WAL mode and busy timeout are configured
        PersistenceHardener.configure_wal(self._store, busy_timeout_ms=15000)

    @property
    def raw_store(self) -> Store:
        return self._store

    def execute_locked(self, fn: Callable[[Store], Any]) -> Any:
        with self._rlock:
            return fn(self._store)


class ConcurrencyTester:
    """Stress-tests Store and Agent under high multi-threaded concurrent access."""

    @classmethod
    def test_concurrent_writes(
        cls,
        store: Store,
        num_workers: int = 10,
        writes_per_worker: int = 20
    ) -> Dict[str, Any]:
        """Executes concurrent writes from multiple threads simultaneously."""
        t0 = time.time()
        errors: List[str] = []
        completed = 0

        def _worker(worker_id: int):
            nonlocal completed
            for i in range(writes_per_worker):
                p_code = f"CONC-P{worker_id}-{i}"
                try:
                    store.save_snapshot(p_code, 1, {"project_code": p_code, "test": True})
                    store.add_prediction(p_code, "test", {
                        "cost_overrun_pct": 5.0,
                        "slippage_months": 2.0,
                        "risk_score": 45.0,
                        "combined_score": 40.0,
                        "tier": "Medium"
                    })
                    completed += 1
                except Exception as ex:
                    errors.append(f"Worker {worker_id} iteration {i} failed: {ex}")

        with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = [executor.submit(_worker, w) for w in range(num_workers)]
            concurrent.futures.wait(futures)

        duration = time.time() - t0
        total_ops = num_workers * writes_per_worker
        return {
            "num_workers": num_workers,
            "total_operations": total_ops,
            "completed_operations": completed,
            "errors_count": len(errors),
            "errors": errors[:5],
            "duration_sec": round(duration, 3),
            "ops_per_second": round(total_ops / max(0.001, duration), 1),
            "success": len(errors) == 0 and completed == total_ops,
        }
