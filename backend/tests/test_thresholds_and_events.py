import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.db.mongodb import connect_to_mongo, get_database
from app.services.alert_service import get_centralized_severity, evaluate_project_threshold_crossing
from app.services.event_service import evaluate_project_events, persist_and_deduplicate_events

@pytest.fixture(autouse=True)
async def setup_db():
    await connect_to_mongo()
    yield

def test_centralized_risk_classification_boundaries():
    # Boundary tests for centralized risk classification
    assert get_centralized_severity(0.0) == "LOW"
    assert get_centralized_severity(39.99) == "LOW"
    assert get_centralized_severity(44.9) == "LOW"
    assert get_centralized_severity(45.0) == "MODERATE"
    assert get_centralized_severity(64.9) == "MODERATE"
    assert get_centralized_severity(65.0) == "HIGH"
    assert get_centralized_severity(74.99) == "HIGH"
    assert get_centralized_severity(79.9) == "HIGH"
    assert get_centralized_severity(80.0) == "CRITICAL"
    assert get_centralized_severity(100.0) == "CRITICAL"

def test_risk_level_vs_threshold_status_distinction():
    """
    Risk level is an absolute tier (e.g. HIGH).
    Threshold status is relative to a project's custom threshold (below vs triggered).
    A project at DPHIS 66 has RiskLevel = HIGH, but if its threshold is 75, its ThresholdStatus = below!
    """
    dphis = 66.0
    threshold = 75.0
    risk_level = get_centralized_severity(dphis)
    threshold_status = "triggered" if dphis >= threshold else "below"

    assert risk_level == "HIGH"
    assert threshold_status == "below"
    assert risk_level != threshold_status

@pytest.mark.asyncio
async def test_exact_7_threshold_crossing_cases():
    db = get_database()
    pid = "P_TEST_CASES_7"

    # Setup project with threshold = 70.0
    await db.projects.update_one(
        {"project_id": pid},
        {"$set": {
            "project_id": pid,
            "project_name": "Test Corridor Cases",
            "dphis_threshold": 70.0,
            "threshold_enabled": True,
            "threshold_status": "below",
            "current_dphis": 55.0,
            "previous_dphis": 50.0
        }},
        upsert=True
    )

    # Case 1: 60 -> 65 (threshold 70) => NO TRIGGER
    res1 = await evaluate_project_threshold_crossing(project_id=pid, previous_dphis=60.0, current_dphis=65.0, custom_threshold=70.0)
    assert res1["triggered"] is False
    assert res1["threshold_status"] == "below"

    # Case 2: 69 -> 70 (threshold 70) => TRIGGER (Exact match triggers)
    res2 = await evaluate_project_threshold_crossing(project_id=pid, previous_dphis=69.0, current_dphis=70.0, custom_threshold=70.0)
    assert res2["triggered"] is True
    assert res2["threshold_status"] == "triggered"
    assert "alert_id" in res2
    assert "event_id" in res2

    # Case 3: 69 -> 75 (threshold 70) => TRIGGER (after resetting below)
    await db.projects.update_one({"project_id": pid}, {"$set": {"threshold_status": "below"}})
    res3 = await evaluate_project_threshold_crossing(project_id=pid, previous_dphis=69.0, current_dphis=75.0, custom_threshold=70.0)
    assert res3["triggered"] is True

    # Case 4: 75 -> 80 (threshold 70) => NO DUPLICATE TRIGGER (already above)
    res4 = await evaluate_project_threshold_crossing(project_id=pid, previous_dphis=75.0, current_dphis=80.0, custom_threshold=70.0)
    assert res4["triggered"] is False
    assert res4["threshold_status"] == "triggered"

    # Case 5: 80 -> 65 (threshold 70) => RESET BELOW THRESHOLD
    res5 = await evaluate_project_threshold_crossing(project_id=pid, previous_dphis=80.0, current_dphis=65.0, custom_threshold=70.0)
    assert res5["triggered"] is False
    assert res5["threshold_status"] == "below"

    # Case 6: 65 -> 72 (threshold 70) => TRIGGER AGAIN
    res6 = await evaluate_project_threshold_crossing(project_id=pid, previous_dphis=65.0, current_dphis=72.0, custom_threshold=70.0)
    assert res6["triggered"] is True
    assert res6["threshold_status"] == "triggered"

    # Case 7: New project first valid DPHIS = 72 (threshold 70) => INITIAL TRIGGER
    pid_new = "P_TEST_NEW_72"
    await db.projects.delete_one({"project_id": pid_new})
    await db.projects.update_one(
        {"project_id": pid_new},
        {"$set": {
            "project_id": pid_new,
            "project_name": "New Project",
            "dphis_threshold": 70.0,
            "threshold_enabled": True,
            "threshold_status": "below",
            "current_dphis": None,
            "previous_dphis": None
        }},
        upsert=True
    )
    res7 = await evaluate_project_threshold_crossing(project_id=pid_new, previous_dphis=None, current_dphis=72.0, custom_threshold=70.0)
    assert res7["triggered"] is True
    assert res7["threshold_status"] == "triggered"

@pytest.mark.asyncio
async def test_project_specific_independent_thresholds():
    """Project A (threshold 70) vs Project B (threshold 60)."""
    db = get_database()
    await db.projects.update_one(
        {"project_id": "P_IND_A"},
        {"$set": {"project_id": "P_IND_A", "dphis_threshold": 70.0, "threshold_enabled": True}},
        upsert=True
    )
    await db.projects.update_one(
        {"project_id": "P_IND_B"},
        {"$set": {"project_id": "P_IND_B", "dphis_threshold": 60.0, "threshold_enabled": True}},
        upsert=True
    )

    # At DPHIS 65:
    # Project A should be BELOW (65 < 70)
    resA = await evaluate_project_threshold_crossing(project_id="P_IND_A", previous_dphis=50.0, current_dphis=65.0)
    assert resA["triggered"] is False
    assert resA["threshold_status"] == "below"

    # Project B should TRIGGER (65 >= 60)
    resB = await evaluate_project_threshold_crossing(project_id="P_IND_B", previous_dphis=50.0, current_dphis=65.0)
    assert resB["triggered"] is True
    assert resB["threshold_status"] == "triggered"

@pytest.mark.asyncio
async def test_event_engine_all_five_types():
    db = get_database()
    if db is not None:
        await db.project_events.delete_many({"project_id": "P_EVENT_TEST"})

    project = {
        "project_id": "P_EVENT_TEST",
        "physical_progress_percent": 30.0,
        "expenditure_crores": 600.0,
        "revised_cost_crores": 1000.0,  # 60% financial vs 30% physical = 30% gap
        "schedule_slippage_months": 6.0
    }
    snapshots = [
        {"snapshot_date": "2026-06-01", "physical_progress": 29.8, "milestones": {"delayed": 2, "total": 10}},
        {"snapshot_date": "2026-07-01", "physical_progress": 30.0, "milestones": {"delayed": 2, "total": 10}}
    ]

    events = evaluate_project_events(
        project=project,
        snapshots=snapshots,
        current_dphis=75.0,
        previous_dphis=65.0,  # +10 velocity -> RISK_ACCELERATING
        threshold=70.0        # crossing 65 -> 75 -> THRESHOLD_CROSSED
    )

    types = [e["event_type"] for e in events]
    assert "THRESHOLD_CROSSED" in types
    assert "RISK_ACCELERATING" in types
    assert "MILESTONE_DELAYED" in types
    assert "PROGRESS_STALLED" in types      # delta 0.2 < 0.5
    assert "COST_PROGRESS_MISMATCH" in types # gap 30% >= 15%

    persisted = await persist_and_deduplicate_events(events)
    assert len(persisted) == len(events)
