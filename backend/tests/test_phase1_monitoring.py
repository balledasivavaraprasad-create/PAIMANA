"""Phase 1 Continuous Monitoring Tests.

Validates the 12 explicit Phase 1 requirements:
  1. First snapshot (canonical fields, hashing, freshness, persistence)
  2. Unchanged snapshot (bypasses ML & SHAP, records project check, no duplicate events)
  3. Material snapshot change (detects mutation, reruns evaluation, records change check)
  4. Stale data (detects lag >= 3 months, flags STALE, issues warning)
  5. Unavailable data (detects missing/invalid reporting date, flags UNAVAILABLE)
  6. User edit (tags source as USER_EDIT, persists in snapshot provenance)
  7. Scheduled scan (tags source as SCHEDULED_SCAN, runs scheduler with error isolation)
  8. Duplicate alert suppression (persistent high risk with no material change does not alert)
  9. Genuine risk transition (escalation Low/Medium -> High alerts immediately)
 10. Event triggering (operational events trigger investigation decoupled from outbound alerts)
 11. Process restart (canonical snapshots and monitoring state survive database reload)
 12. Provider failure (raises ProviderUnavailableError, scheduler handles gracefully without fabricating fake data)
"""
import os
import sys
import tempfile
import time
from datetime import date
from pathlib import Path
import pytest

_tests_dir = Path(__file__).resolve().parent
_agent_dir = _tests_dir.parent
if str(_agent_dir) not in sys.path:
    sys.path.insert(0, str(_agent_dir))
sys.path.insert(0, ".")

from paimana_agent import MonitoringAgent, Scheduler
from paimana_agent.store import Store, compute_snapshot_hash
from paimana_agent.notify import FileNotifier
from paimana_agent.snapshot import SnapshotSource, FreshnessState, CanonicalSnapshot
from paimana_agent.sync import PaimanaDataSync, MemoryDataProvider, FileDataProvider, ProviderUnavailableError
import paimana_agent.features as F


@pytest.fixture
def monitoring_env():
    tmp = tempfile.mkdtemp()
    agent = MonitoringAgent.from_config("config.yaml")
    db_path = os.path.join(tmp, "monitoring_test.db")
    agent.store = Store(db_path)
    agent.notifiers = [FileNotifier(os.path.join(tmp, "alerts.jsonl"))]
    return agent, tmp, db_path


def current_report_month() -> str:
    return date.today().strftime("%Y-%m")


# ============================================================================
# 1. First Snapshot
# ============================================================================

def test_first_snapshot(monitoring_env):
    """Requirement 1 & 11: Evaluates first snapshot and ensures all canonical fields are persisted."""
    agent, _, db_path = monitoring_env
    rep_month = current_report_month()

    proj = {
        "project_code": "CANON-1", "project_name": "Hydroelectric Plant",
        "ministry": "Ministry of Power", "sector": "Power",
        "implementing_agency": "NHPC", "state": "Himachal Pradesh",
        "approval_date": "01/2021", "start_date": "06/2021",
        "original_completion_date": "06/2026", "original_cost_cr": 3200.0,
        "cumulative_expenditure_cr": 960.0, "physical_progress_pct": 30.0,
        "report_month": rep_month
    }

    res = agent.evaluate_project(proj, event="add")

    # Verification of canonical attributes in response
    assert res["material_change"] is True
    assert res["snapshot_id"].startswith("SNAP-CANON-1-")
    assert res["snapshot_hash"] == compute_snapshot_hash(proj)
    assert res["schema_version"] if "schema_version" in res else res["canonical_snapshot"]["schema_version"] == "1.0"
    assert res["source"] == "USER_EDIT"
    assert res["freshness_state"] == "FRESH"
    assert res["data_freshness_months"] <= 1

    # Verification of concept separation
    assert "current_risk_state" in res
    assert "risk_change" in res
    assert "material_data_change" in res
    assert res["material_data_change"] is True
    assert res["risk_change"]["prev_score"] is None

    # Verification of DB persistence of canonical fields
    snap = agent.store.latest_snapshot("CANON-1")
    assert snap is not None
    assert snap["snapshot_id"] == res["snapshot_id"]
    assert snap["snapshot_hash"] == res["snapshot_hash"]
    assert snap["source"] == "USER_EDIT"
    assert snap["freshness_state"] == "FRESH"

    # Verification of project check record
    check = agent.store.last_project_check("CANON-1")
    assert check is not None
    assert check["was_material_change"] == 1
    assert check["reason"] == "material_change"


# ============================================================================
# 2. Unchanged Snapshot
# ============================================================================

def test_unchanged_snapshot(monitoring_env):
    """Requirement 3 & 11: Unchanged snapshots bypass expensive ML/SHAP and emit no duplicate events."""
    agent, _, _ = monitoring_env
    rep_month = current_report_month()

    proj = {
        "project_code": "UNCHANGED-1", "project_name": "Freight Corridor Segment",
        "ministry": "Ministry of Railways", "sector": "Railways",
        "implementing_agency": "DFCCIL", "state": "Uttar Pradesh",
        "approval_date": "01/2020", "start_date": "06/2020",
        "original_completion_date": "06/2025", "original_cost_cr": 4500.0,
        "cumulative_expenditure_cr": 1800.0, "physical_progress_pct": 40.0,
        "report_month": rep_month
    }

    r1 = agent.evaluate_project(proj, event="add")
    assert r1["material_change"] is True

    # Re-evaluate with identical data
    r2 = agent.evaluate_project(dict(proj), event="edit")

    assert r2["material_change"] is False
    assert r2["material_data_change"] is False
    assert r2["snapshot_hash"] == r1["snapshot_hash"]
    assert r2["risk_score"] == r1["risk_score"]
    assert r2["detail"]["shap"] is None, "SHAP evaluation must be bypassed on unmutated snapshot"
    assert r2["events"] == [], "Unchanged snapshot must not emit duplicate events"

    # Verification that unmutated check was recorded
    check = agent.store.last_project_check("UNCHANGED-1")
    assert check is not None
    assert check["was_material_change"] == 0
    assert check["reason"] == "unmutated_check"


# ============================================================================
# 3. Material Snapshot Change
# ============================================================================

def test_material_snapshot_change(monitoring_env):
    """Requirement 3 & 11: Material data mutation triggers evaluation and hash update."""
    agent, _, _ = monitoring_env
    rep_month = current_report_month()

    proj = {
        "project_code": "MUTATE-1", "project_name": "Metro Rail Link",
        "ministry": "Ministry of Housing and Urban Affairs", "sector": "Urban Development",
        "implementing_agency": "DMRC", "state": "Delhi",
        "approval_date": "01/2021", "start_date": "06/2021",
        "original_completion_date": "06/2025", "original_cost_cr": 2000.0,
        "cumulative_expenditure_cr": 600.0, "physical_progress_pct": 30.0,
        "report_month": rep_month
    }

    r1 = agent.evaluate_project(proj, event="add")
    h1 = r1["snapshot_hash"]

    # Material mutation: spend increases by 500 Cr with zero physical progress
    mutated = dict(proj, cumulative_expenditure_cr=1100.0)
    r2 = agent.evaluate_project(mutated, event="edit")

    assert r2["material_change"] is True
    assert r2["snapshot_hash"] != h1

    check = agent.store.last_project_check("MUTATE-1")
    assert check["was_material_change"] == 1
    assert check["reason"] == "material_change"


# ============================================================================
# 4. Stale Data
# ============================================================================

def test_stale_data(monitoring_env):
    """Requirement 5 & 11: Submissions with reporting dates >= 3 months old are marked STALE."""
    agent, _, _ = monitoring_env

    proj = {
        "project_code": "STALE-1", "project_name": "Rural Water Supply",
        "ministry": "Ministry of Jal Shakti", "sector": "Water Resources",
        "implementing_agency": "DWS", "state": "Bihar",
        "approval_date": "01/2020", "start_date": "06/2020",
        "original_completion_date": "06/2024", "original_cost_cr": 800.0,
        "cumulative_expenditure_cr": 400.0, "physical_progress_pct": 50.0,
        "report_month": "2024-01"  # Well over 3 months old
    }

    res = agent.evaluate_project(proj, event="add")

    assert res["freshness_state"] == FreshnessState.STALE.value
    assert res["is_stale"] is True
    assert res["data_freshness_months"] >= 3
    assert any("stale submission" in w for w in res["warnings"])


# ============================================================================
# 5. Unavailable Data
# ============================================================================

def test_unavailable_data(monitoring_env):
    """Requirement 5 & 11: Missing or unparseable reporting date flags UNAVAILABLE freshness."""
    agent, _, _ = monitoring_env

    proj = {
        "project_code": "UNAVAIL-1", "project_name": "Telecom Towers Expansion",
        "ministry": "Ministry of Communications", "sector": "Telecommunications",
        "implementing_agency": "BSNL", "state": "Assam",
        "approval_date": "01/2022", "start_date": "06/2022",
        "original_completion_date": "06/2026", "original_cost_cr": 1100.0,
        "cumulative_expenditure_cr": 330.0, "physical_progress_pct": 30.0,
        # report_month omitted
    }

    res = agent.evaluate_project(proj, event="add")

    assert res["freshness_state"] == FreshnessState.UNAVAILABLE.value
    assert res["data_freshness_months"] == 999
    assert any("freshness is UNAVAILABLE" in w for w in res["warnings"])


# ============================================================================
# 6. User Edit Source
# ============================================================================

def test_user_edit(monitoring_env):
    """Requirement 2 & 11: on_project_saved tags snapshot provenance as USER_EDIT."""
    agent, _, _ = monitoring_env

    proj = {
        "project_code": "USER-EDIT-1", "project_name": "Bridge Rehabilitation",
        "ministry": "Ministry of Road Transport & Highways", "sector": "Roads & Highways",
        "implementing_agency": "NHAI", "state": "Kerala",
        "approval_date": "01/2021", "start_date": "06/2021",
        "original_completion_date": "06/2025", "original_cost_cr": 500.0,
        "cumulative_expenditure_cr": 200.0, "physical_progress_pct": 40.0,
        "report_month": current_report_month()
    }

    res = agent.on_project_saved(proj, event="edit")
    assert res["source"] == SnapshotSource.USER_EDIT.value
    assert res["canonical_snapshot"]["source"] == SnapshotSource.USER_EDIT.value

    snap = agent.store.latest_snapshot("USER-EDIT-1")
    assert snap["source"] == SnapshotSource.USER_EDIT.value


# ============================================================================
# 7. Scheduled Scan
# ============================================================================

def test_scheduled_scan(monitoring_env):
    """Requirement 6 & 11: Scheduled scan tags provenance as SCHEDULED_SCAN and isolates corrupt records."""
    agent, _, _ = monitoring_env
    rep_month = current_report_month()

    valid_1 = {
        "project_code": "SCHED-1", "project_name": "Solar Park Phase 1",
        "ministry": "Ministry of New and Renewable Energy", "sector": "Power",
        "implementing_agency": "SECI", "state": "Rajasthan",
        "approval_date": "01/2021", "start_date": "06/2021",
        "original_completion_date": "06/2025", "original_cost_cr": 1200.0,
        "cumulative_expenditure_cr": 480.0, "physical_progress_pct": 40.0,
        "report_month": rep_month
    }
    corrupt = {"project_code": "CORRUPT-1", "project_name": "Broken"}
    valid_2 = {
        "project_code": "SCHED-2", "project_name": "Expressway Bypass",
        "ministry": "Ministry of Road Transport & Highways", "sector": "Roads & Highways",
        "implementing_agency": "NHAI", "state": "Punjab",
        "approval_date": "01/2020", "start_date": "06/2020",
        "original_completion_date": "06/2024", "original_cost_cr": 1800.0,
        "cumulative_expenditure_cr": 900.0, "physical_progress_pct": 50.0,
        "report_month": rep_month
    }

    # Error isolation: corrupt record must not fail batch
    batch_results = agent.run_scheduled_scan([valid_1, corrupt, valid_2])
    assert len(batch_results) == 2
    for r in batch_results:
        assert r["source"] == SnapshotSource.SCHEDULED_SCAN.value
        assert r["event"] == "scheduled"

    # Scheduler class integration
    sch = Scheduler(agent, project_provider=lambda: [valid_1], interval_hours=1.0)
    sch_results = sch.run_once()
    assert len(sch_results) == 1
    assert sch_results[0]["project_code"] == "SCHED-1"
    assert sch_results[0]["source"] == SnapshotSource.SCHEDULED_SCAN.value


# ============================================================================
# 8. Duplicate Alert Suppression
# ============================================================================

def test_duplicate_alert_suppression(monitoring_env):
    """Requirement 4, 7 & 11: Persistent high risk with no new material change does not generate duplicate alerts."""
    agent, _, _ = monitoring_env
    rep_month = current_report_month()

    high_risk_proj = {
        "project_code": "DEDUP-ALERT-1", "project_name": "Stalled Rail Tunnel",
        "ministry": "Ministry of Railways", "sector": "Railways",
        "implementing_agency": "RVNL", "state": "Uttarakhand",
        "approval_date": "01/2018", "start_date": "06/2018",
        "original_completion_date": "06/2021", "revised_completion_date": "06/2028",
        "original_cost_cr": 3000.0, "revised_cost_cr": 6000.0,
        "cumulative_expenditure_cr": 4500.0, "physical_progress_pct": 45.0,
        "report_month": rep_month
    }

    # First evaluation: new at-risk project emits alert
    r1 = agent.evaluate_project(high_risk_proj, event="add")
    assert r1["tier"] == "High"
    assert r1["alert"] is not None

    # Immediate second evaluation on unchanged data: suppressed
    r2 = agent.evaluate_project(dict(high_risk_proj), event="edit")
    assert r2["alert"] is None, "Repeated evaluation with no material change must NOT alert"
    assert r2["tier"] == "High", "Project remains visible as High risk"

    # Only 1 alert row in store
    alerts = agent.store.list_alerts()
    dedup_alerts = [a for a in alerts if a["project_code"] == "DEDUP-ALERT-1"]
    assert len(dedup_alerts) == 1


# ============================================================================
# 9. Genuine Risk Transition
# ============================================================================

def test_genuine_risk_transition(monitoring_env):
    """Requirement 4 & 11: Real risk escalation (Medium -> High) bypasses suppression and triggers alert."""
    agent, _, _ = monitoring_env

    # Month 1: Moderate project
    proj_m1 = {
        "project_code": "TRANS-1", "project_name": "Thermal Plant Expansion",
        "ministry": "Ministry of Power", "sector": "Power",
        "implementing_agency": "NTPC", "state": "Jharkhand",
        "approval_date": "01/2021", "start_date": "06/2021",
        "original_completion_date": "06/2026", "original_cost_cr": 2500.0,
        "cumulative_expenditure_cr": 750.0, "physical_progress_pct": 30.0,
        "report_month": "2026-01"
    }

    r1 = agent.evaluate_project(proj_m1, event="add", report_month="2026-01")
    # Store threshold high enough to prevent initial Low/Medium from alerting
    agent.store.set_threshold("TRANS-1", 75.0)

    # Month 2: Severe deterioration - cost doubles and completion pushed by 6 years
    proj_m2 = dict(
        proj_m1,
        revised_cost_cr=5500.0,
        revised_completion_date="06/2032",
        cumulative_expenditure_cr=3500.0,
        physical_progress_pct=35.0,
        report_month="2026-02"
    )

    r2 = agent.evaluate_project(proj_m2, event="edit", report_month="2026-02")

    assert r2["risk_change"]["is_escalation"] is True
    assert r2["tier"] == "High"
    assert r2["alert"] is not None
    assert "escalated" in r2["alert"]["reason"]


# ============================================================================
# 10. Event Triggering
# ============================================================================

def test_event_triggering(monitoring_env):
    """Requirement 4, 8 & 11: Material operational anomalies emit events and trigger investigations."""
    agent, _, _ = monitoring_env
    rep_month = current_report_month()

    # Project with 50% spend but only 15% physical progress (>35 pt gap)
    decoupled_proj = {
        "project_code": "EV-TRIG-1", "project_name": "Irrigation Canal System",
        "ministry": "Ministry of Jal Shakti", "sector": "Water Resources",
        "implementing_agency": "CWC", "state": "Andhra Pradesh",
        "approval_date": "01/2022", "start_date": "06/2022",
        "original_completion_date": "06/2026", "original_cost_cr": 1000.0,
        "cumulative_expenditure_cr": 500.0, "physical_progress_pct": 15.0,
        "report_month": rep_month
    }

    res = agent.evaluate_project(decoupled_proj, event="add")

    # Operational events must be emitted
    ev_types = [e["type"] for e in res["events"]]
    assert "COST_PROGRESS_MISMATCH" in ev_types

    # Events persisted in DB
    db_events = agent.store.list_events("EV-TRIG-1")
    assert len(db_events) >= 1
    assert any(e["type"] == "COST_PROGRESS_MISMATCH" for e in db_events)

    # Investigation triggered by operational event
    assert res["investigation"] is not None


# ============================================================================
# 11. Process Restart
# ============================================================================

def test_process_restart(monitoring_env):
    """Requirement 10 & 11: Snapshots, canonical metadata, and project checks survive process restart."""
    agent, tmp, db_path = monitoring_env
    rep_month = current_report_month()

    proj = {
        "project_code": "RESTART-1", "project_name": "Coastal Highway Link",
        "ministry": "Ministry of Road Transport & Highways", "sector": "Roads & Highways",
        "implementing_agency": "NHAI", "state": "Maharashtra",
        "approval_date": "01/2021", "start_date": "06/2021",
        "original_completion_date": "06/2025", "original_cost_cr": 1400.0,
        "cumulative_expenditure_cr": 420.0, "physical_progress_pct": 30.0,
        "report_month": rep_month
    }

    r1 = agent.evaluate_project(proj, event="add")

    # Simulate process death: recreate Store instance from the SQLite file
    reopened_store = Store(db_path)

    # Reopened store must have identical canonical snapshot
    reloaded_snap = reopened_store.latest_snapshot("RESTART-1")
    assert reloaded_snap is not None
    assert reloaded_snap["snapshot_id"] == r1["snapshot_id"]
    assert reloaded_snap["snapshot_hash"] == r1["snapshot_hash"]
    assert reloaded_snap["source"] == "USER_EDIT"
    assert reloaded_snap["freshness_state"] == "FRESH"

    # Reopened store must have project check record
    check = reopened_store.last_project_check("RESTART-1")
    assert check is not None
    assert check["was_material_change"] == 1

    # Reopened store must retain predictions
    last_p = reopened_store.last_prediction("RESTART-1")
    assert last_p is not None
    assert round(last_p["risk_score"]) == round(r1["risk_score"])


# ============================================================================
# 12. Provider Failure
# ============================================================================

def test_provider_failure(monitoring_env):
    """Requirement 9 & 11: Authoritative provider failure raises ProviderUnavailableError without fabricating data."""
    agent, _, _ = monitoring_env

    # 1. Memory provider offline
    mem_provider = MemoryDataProvider([{"project_code": "FAIL-1"}])
    mem_provider.set_online(False)

    sync = PaimanaDataSync(agent, provider=mem_provider)
    with pytest.raises(ProviderUnavailableError):
        sync.sync_from_provider()

    # 2. File provider missing file
    file_provider = FileDataProvider("nonexistent_paimana_export.json")
    sync_file = PaimanaDataSync(agent, provider=file_provider)
    with pytest.raises(ProviderUnavailableError):
        sync_file.sync_from_provider()

    # 3. Scheduler with failed provider must log and return empty without crashing or fabricating data
    sch = Scheduler(agent, project_provider=mem_provider)
    sch_res = sch.run_once()
    assert sch_res == []

    # Store must not contain fabricated project
    assert agent.store.latest_snapshot("FAIL-1") is None
