"""PAIMANA Authoritative Data Synchronization Service.

Provides continuous, automated data ingestion and change-driven synchronization between
the external MoSPI PAIMANA portal/database and the local MonitoringAgent:
  1. Authoritative Data Provider Abstraction (Boundary Separation).
  2. Authoritative Snapshot Ingestion (API, JSON/CSV feeds, DB replicas).
  3. Early Deterministic Snapshot Hashing (bypasses unmutated project records).
  4. Change-Driven Event & Investigation Triggering.
  5. Batch Audit Reporting & Sync Telemetry.
"""
from __future__ import annotations
import json
import logging
import os
import urllib.request
from typing import Optional, Callable, List, Dict, Any

from .agent import MonitoringAgent
from .store import compute_snapshot_hash
from .snapshot import SnapshotSource

logger = logging.getLogger("paimana_agent.sync")


class ProviderUnavailableError(RuntimeError):
    """Raised when the authoritative data provider is unreachable, offline, or failed."""
    pass


class AuthoritativeDataProvider:
    """Abstract interface defining the boundary for authoritative project data sources."""

    def fetch_project(self, project_code: str) -> Optional[dict]:
        """Fetches the latest authoritative snapshot for a single project code."""
        raise NotImplementedError

    def fetch_batch(self) -> List[dict]:
        """Fetches the latest authoritative batch of project snapshots."""
        raise NotImplementedError


class FileDataProvider(AuthoritativeDataProvider):
    """Authoritative data provider reading from a vetted export file (JSON)."""

    def __init__(self, file_path: str):
        self.file_path = file_path

    def fetch_batch(self) -> List[dict]:
        if not os.path.exists(self.file_path):
            raise ProviderUnavailableError(f"Authoritative source file unavailable: {self.file_path}")
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data if isinstance(data, list) else data.get("projects", [])
        except Exception as ex:
            raise ProviderUnavailableError(f"Failed to read authoritative source file: {ex}") from ex

    def fetch_project(self, project_code: str) -> Optional[dict]:
        batch = self.fetch_batch()
        for p in batch:
            if p.get("project_code") == project_code:
                return p
        return None


class ApiDataProvider(AuthoritativeDataProvider):
    """Authoritative data provider fetching from a remote PAIMANA / PMIS REST API."""

    def __init__(self, endpoint_url: str, api_token: Optional[str] = None, timeout_sec: int = 30):
        self.endpoint_url = endpoint_url
        self.api_token = api_token
        self.timeout_sec = timeout_sec

    def fetch_batch(self) -> List[dict]:
        if not self.endpoint_url:
            raise ProviderUnavailableError("API endpoint URL is not configured.")
        headers = {"Content-Type": "application/json"}
        if self.api_token:
            headers["Authorization"] = f"Bearer {self.api_token}"

        try:
            req = urllib.request.Request(self.endpoint_url, headers=headers)
            with urllib.request.urlopen(req, timeout=self.timeout_sec) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            return data if isinstance(data, list) else data.get("projects", [])
        except Exception as ex:
            raise ProviderUnavailableError(f"Authoritative API endpoint unreachable at {self.endpoint_url}: {ex}") from ex

    def fetch_project(self, project_code: str) -> Optional[dict]:
        url = f"{self.endpoint_url.rstrip('/')}/{project_code}"
        headers = {"Content-Type": "application/json"}
        if self.api_token:
            headers["Authorization"] = f"Bearer {self.api_token}"

        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=self.timeout_sec) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as he:
            if he.code == 404:
                return None
            raise ProviderUnavailableError(f"Authoritative API error for {project_code}: {he}") from he
        except Exception as ex:
            raise ProviderUnavailableError(f"Authoritative API unreachable for {project_code}: {ex}") from ex


class MemoryDataProvider(AuthoritativeDataProvider):
    """In-memory data provider for testing and isolated simulation."""

    def __init__(self, projects: Optional[List[dict]] = None):
        self.projects = projects or []
        self.is_online = True

    def set_online(self, online: bool):
        self.is_online = online

    def fetch_batch(self) -> List[dict]:
        if not self.is_online:
            raise ProviderUnavailableError("Authoritative memory data provider is currently offline.")
        return list(self.projects)

    def fetch_project(self, project_code: str) -> Optional[dict]:
        if not self.is_online:
            raise ProviderUnavailableError("Authoritative memory data provider is currently offline.")
        for p in self.projects:
            if p.get("project_code") == project_code:
                return p
        return None


class PaimanaDataSync:
    """Authoritative synchronization service connecting the agent directly to external PAIMANA data sources."""

    def __init__(
        self,
        agent: MonitoringAgent,
        provider: Optional[AuthoritativeDataProvider] = None,
        source_url: Optional[str] = None,
        api_token: Optional[str] = None
    ):
        self.agent = agent
        self.provider = provider
        if not self.provider and source_url:
            self.provider = ApiDataProvider(source_url, api_token=api_token)
        self.source_url = source_url
        self.api_token = api_token

    def sync_project(self, project: dict, event: str = "sync", report_month: Optional[str] = None,
                     source: str = "PAIMANA_SYNC") -> dict:
        """Syncs a single project record against agent memory, detecting material changes."""
        code = project.get("project_code")
        if not code:
            raise ValueError("project_code is required for synchronization")

        cur_hash = compute_snapshot_hash(project)
        latest_snap = self.agent.store.latest_snapshot(code)
        prev_hash = compute_snapshot_hash(latest_snap) if latest_snap else None

        # Check if identical data already persisted
        if prev_hash and cur_hash == prev_hash:
            logger.debug(f"[Sync Skipped] Project {code} is unmutated (hash: {cur_hash[:8]}).")
            self.agent.store.record_project_check(code, False, "sync_unmutated_skipped")
            return {
                "project_code": code,
                "status": "unmutated_skipped",
                "snapshot_hash": cur_hash,
                "material_change": False,
                "evaluated": False,
            }

        # Material change detected or new project -> trigger evaluation
        result = self.agent.evaluate_project(
            project, event=event, report_month=report_month, source=source
        )
        return {
            "project_code": code,
            "status": "evaluated",
            "snapshot_hash": cur_hash,
            "material_change": True,
            "evaluated": True,
            "tier": result.get("tier"),
            "risk_score": result.get("risk_score"),
            "investigation_triggered": result.get("investigation") is not None,
            "alert_triggered": result.get("alert") is not None,
        }

    def sync_batch(self, projects: list[dict], event: str = "sync", report_month: Optional[str] = None) -> dict:
        """Synchronizes an array of project records from an authoritative feed."""
        summary = {
            "total_projects": len(projects),
            "total_records": len(projects),
            "evaluated": 0,
            "unmutated_skipped": 0,
            "skipped_unmutated": 0,
            "investigations_triggered": 0,
            "alerts_triggered": 0,
            "results": [],
        }

        for p in projects:
            try:
                res = self.sync_project(p, event=event, report_month=report_month)
                summary["results"].append(res)
                if res.get("status") == "evaluated":
                    summary["evaluated"] += 1
                    if res.get("investigation_triggered"):
                        summary["investigations_triggered"] += 1
                    if res.get("alert_triggered"):
                        summary["alerts_triggered"] += 1
                else:
                    summary["unmutated_skipped"] += 1
                    summary["skipped_unmutated"] += 1
            except Exception as ex:
                logger.error(f"Error syncing project {p.get('project_code')}: {ex}")
                summary["results"].append({
                    "project_code": p.get("project_code"),
                    "status": "error",
                    "error": str(ex),
                })

        logger.info(
            f"PAIMANA Sync completed: {summary['total_projects']} total, "
            f"{summary['evaluated']} evaluated, {summary['unmutated_skipped']} skipped (unmutated)."
        )
        return summary

    def sync_from_provider(self, event: str = "sync") -> dict:
        """Synchronizes from the registered authoritative data provider."""
        if not self.provider:
            raise ProviderUnavailableError("No authoritative data provider configured.")
        projects = self.provider.fetch_batch()
        return self.sync_batch(projects, event=event)

    def sync_from_file(self, file_path: str) -> dict:
        """Synchronizes projects from a local authoritative export file (JSON)."""
        provider = FileDataProvider(file_path)
        projects = provider.fetch_batch()
        return self.sync_batch(projects, event="file_sync")

    def sync_from_api(self, endpoint_url: Optional[str] = None, token: Optional[str] = None) -> dict:
        """Polls an authoritative remote PAIMANA API endpoint."""
        url = endpoint_url or self.source_url
        auth_token = token or self.api_token
        if not url:
            raise ValueError("Endpoint URL must be provided or configured in PaimanaDataSync")
        provider = ApiDataProvider(url, api_token=auth_token)
        projects = provider.fetch_batch()
        return self.sync_batch(projects, event="api_sync")
