"""Continuous monitoring trigger (PAIMANA architecture review, problem #1).

Before: the agent only reacted to on_project_saved(event="add"|"edit") -- pure
event-driven monitoring. This adds the second trigger from the review's diagram:

                    MONITORING ENGINE
                         |
             +-----------+-----------+
             v                       v
      Project Changed          Scheduled Run
       immediately             every N hours
             |                       |
             +-----------+-----------+
                         v
                  Evaluate Project

A periodic scan re-evaluates every project this agent knows about (Store.all_project_codes,
i.e. everything with at least one snapshot) even if nobody edited it, so slow drift
(e.g. a milestone quietly slipping while no one touches the record) still surfaces.

The agent doesn't own the source-of-truth project database, so the scan needs a
`project_provider` callback: () -> list[project_dict], supplied by whoever embeds this
package (a DB query, an API call, or -- for a cron/n8n-triggered single pass -- a JSON
export). Two ways to run it:

  - Long-lived process:  Scheduler(agent, project_provider, interval_hours=6).start()
  - Cron / n8n / one-shot:  python -m paimana_agent.scheduler config.yaml projects.json
"""
from __future__ import annotations
import json, logging, sys, threading, time
from typing import Callable, Optional, Union

from .sync import AuthoritativeDataProvider, ProviderUnavailableError

log = logging.getLogger(__name__)


class Scheduler:
    """Continuous scheduled monitoring runner.
    
    Coordinates periodic scans across authoritative data sources:
    continuous scheduled monitoring + event-triggered investigation.
    (Note: This is periodic polling/scanning, not real-time streaming).
    """
    def __init__(
        self,
        agent,
        project_provider: Union[Callable[[], list], AuthoritativeDataProvider],
        interval_hours: float = 6.0
    ):
        self.agent, self.project_provider, self.interval_hours = agent, project_provider, interval_hours
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def run_once(self) -> list[dict]:
        try:
            if isinstance(self.project_provider, AuthoritativeDataProvider):
                projects = self.project_provider.fetch_batch()
            elif callable(self.project_provider):
                projects = self.project_provider()
            else:
                raise TypeError(f"Invalid project_provider type: {type(self.project_provider)}")
        except ProviderUnavailableError as pue:
            log.error("scheduled scan: authoritative data provider unavailable: %s", pue)
            return []
        except Exception as ex:
            log.error("scheduled scan: project_provider failed: %s", ex)
            return []
        results = self.agent.run_scheduled_scan(projects)
        log.info("scheduled scan: %d projects evaluated, %d produced new events",
                 len(projects), sum(1 for r in results if r.get("events")))
        return results

    def _loop(self):
        while not self._stop.is_set():
            self.run_once()
            self._stop.wait(self.interval_hours * 3600)

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=5)


def _file_project_provider(path: str) -> Callable[[], list]:
    def _load():
        with open(path) as f:
            return json.load(f)
    return _load


if __name__ == "__main__":
    from .agent import MonitoringAgent
    cfg_path = sys.argv[1] if len(sys.argv) > 1 else "config.yaml"
    projects_path = sys.argv[2] if len(sys.argv) > 2 else "projects.json"
    ag = MonitoringAgent.from_config(cfg_path)
    sch = Scheduler(ag, _file_project_provider(projects_path))
    out = sch.run_once()
    print(json.dumps([{"project_code": r["project_code"], "tier": r["tier"],
                        "risk_score": round(r["risk_score"]), "events": [e["type"] for e in r.get("events", [])]}
                       for r in out], indent=2))
