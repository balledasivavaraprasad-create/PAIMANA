"""Storage Abstraction & Project Repository Adapters for Peer Intelligence.

Provides a decoupled repository pattern:
- ProjectRepository (ABC): formal abstract interface
- InMemoryProjectRepository: fast in-memory store for datasets/testing
- SQLiteProjectRepository: adapter over existing Store (monitoring.db)
- Future-proof for MongoDB integration without changing any peer engine code.
"""
from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class ProjectRepository(ABC):
    """Abstract interface for project universe and snapshot retrieval."""

    @abstractmethod
    def get_project(self, project_code: str) -> Optional[Dict[str, Any]]:
        """Retrieve the latest record for a project by code."""
        pass

    @abstractmethod
    def get_candidates(self, sector: Optional[str] = None, exclude_code: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieve candidate peers, optionally filtered by sector and excluding target."""
        pass

    @abstractmethod
    def get_history(self, project_code: str, limit: int = 12) -> List[Dict[str, Any]]:
        """Retrieve chronological snapshots for a project (oldest to newest)."""
        pass


class InMemoryProjectRepository(ProjectRepository):
    """In-memory implementation backed by dictionaries. Ideal for unit tests & CSV datasets."""

    def __init__(self, projects: Optional[List[Dict[str, Any]]] = None,
                 snapshots: Optional[Dict[str, List[Dict[str, Any]]]] = None):
        self._projects: Dict[str, Dict[str, Any]] = {}
        self._snapshots: Dict[str, List[Dict[str, Any]]] = snapshots or {}

        if projects:
            for p in projects:
                code = str(p.get("project_code", "")).strip()
                if code:
                    self._projects[code] = dict(p)

    def add_project(self, project: Dict[str, Any]) -> None:
        code = str(project.get("project_code", "")).strip()
        if code:
            self._projects[code] = dict(project)

    def add_snapshot(self, project_code: str, snapshot: Dict[str, Any]) -> None:
        code = str(project_code).strip()
        if code not in self._snapshots:
            self._snapshots[code] = []
        self._snapshots[code].append(dict(snapshot))

    def get_project(self, project_code: str) -> Optional[Dict[str, Any]]:
        return self._projects.get(str(project_code).strip())

    def get_candidates(self, sector: Optional[str] = None, exclude_code: Optional[str] = None) -> List[Dict[str, Any]]:
        ex = str(exclude_code).strip() if exclude_code else None
        res = []
        for code, p in self._projects.items():
            if ex and code == ex:
                continue
            if sector and str(p.get("sector", "")).strip().lower() != str(sector).strip().lower():
                continue
            res.append(dict(p))
        return res

    def get_history(self, project_code: str, limit: int = 12) -> List[Dict[str, Any]]:
        code = str(project_code).strip()
        snaps = self._snapshots.get(code, [])
        # Return sorted by report_index / report_month if available
        def _sort_key(s: Dict[str, Any]):
            return s.get("report_index", 0) or s.get("report_month", "")
        sorted_snaps = sorted(snaps, key=_sort_key)
        return [dict(s) for s in sorted_snaps[-limit:]]


class SQLiteProjectRepository(ProjectRepository):
    """Adapter over existing paimana_agent.store.Store SQLite database."""

    def __init__(self, store: Any):
        self.store = store

    def get_project(self, project_code: str) -> Optional[Dict[str, Any]]:
        snap = self.store.latest_snapshot(project_code)
        if snap:
            return snap
        return None

    def get_candidates(self, sector: Optional[str] = None, exclude_code: Optional[str] = None) -> List[Dict[str, Any]]:
        if sector and exclude_code:
            return self.store.peers(sector=sector, exclude_code=exclude_code, limit=500)
        # Fallback to querying all project codes from store
        codes = self.store.all_project_codes()
        ex = str(exclude_code).strip() if exclude_code else None
        res = []
        for c in codes:
            if ex and c == ex:
                continue
            p = self.store.latest_snapshot(c)
            if not p:
                continue
            if sector and str(p.get("sector", "")).strip().lower() != str(sector).strip().lower():
                continue
            res.append(p)
        return res

    def get_history(self, project_code: str, limit: int = 12) -> List[Dict[str, Any]]:
        with self.store._lock:
            rows = self.store._c.execute(
                "SELECT report_index, payload FROM snapshots WHERE project_code=? "
                "ORDER BY report_index ASC", (project_code,)).fetchall()
        snaps = []
        for r in rows:
            d = json.loads(r["payload"])
            d["report_index"] = r["report_index"]
            snaps.append(d)
        return snaps[-limit:]
