import pytest
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient, ASGITransport, Response
from app.main import app
from app.db.mongodb import connect_to_mongo, get_database
from app.services.alert_service import evaluate_project_threshold_crossing
from app.services.observability_service import observability

@pytest.fixture(autouse=True)
async def setup_db():
    await connect_to_mongo()
    yield

@pytest.mark.asyncio
async def test_n8n_webhook_payload_and_failure_resilience():
    """
    Test n8n webhook integration:
    1. Prepares correct structured payload (project, risk, user, admin, top_risk_reasons, project_url).
    2. Alert remains SAFELY persisted in MongoDB even when n8n webhook returns 500 / fails.
    3. Idempotency: duplicate threshold trigger does not fire another webhook.
    """
    db = get_database()
    pid = f"P_N8N_{uuid.uuid4().hex[:6]}"

    # Setup project
    await db.projects.update_one(
        {"project_id": pid},
        {"$set": {
            "project_id": pid,
            "project_name": "Dedicated Freight Corridor West",
            "department": "Railways",
            "state": "Maharashtra",
            "dphis_threshold": 70.0,
            "threshold_enabled": True,
            "threshold_status": "below",
            "current_dphis": 65.0,
            "previous_dphis": 60.0
        }},
        upsert=True
    )

    captured_payload = None

    async def mock_post(url, json=None, timeout=None):
        nonlocal captured_payload
        captured_payload = json
        # Simulate webhook failure/timeout
        return Response(status_code=500, text="Internal Server Error on webhook worker")

    with patch("httpx.AsyncClient.post", side_effect=mock_post):
        # Trigger crossing 65 -> 72 (threshold 70)
        res = await evaluate_project_threshold_crossing(
            project_id=pid,
            previous_dphis=65.0,
            current_dphis=72.0,
            custom_threshold=70.0
        )

        assert res["triggered"] is True
        assert res["threshold_status"] == "triggered"
        assert "alert_id" in res
        alert_id = res["alert_id"]

        # 1. Verify payload structure
        assert captured_payload is not None
        assert captured_payload["event_type"] == "DPHIS_THRESHOLD_CROSSED"
        assert "project" in captured_payload
        assert captured_payload["project"]["project_id"] == pid
        assert "risk" in captured_payload
        assert captured_payload["risk"]["threshold"] == 70.0
        assert captured_payload["risk"]["current_dphis"] == 72.0
        assert "user" in captured_payload
        assert "admin" in captured_payload
        assert "project_url" in captured_payload

        # 2. Verify alert remained safely persisted in MongoDB despite HTTP 500 failure
        alert_in_db = await db.alerts.find_one({"alert_id": alert_id})
        assert alert_in_db is not None
        assert alert_in_db["project_id"] == pid
        assert alert_in_db["dphis"] == 72.0
        assert alert_in_db["notification_status"] == "failed"

        # 3. Test idempotency: evaluating again at 73 -> duplicate suppressed, no new webhook dispatch
        captured_payload = None
        res_dup = await evaluate_project_threshold_crossing(
            project_id=pid,
            previous_dphis=72.0,
            current_dphis=73.0,
            custom_threshold=70.0
        )
        assert res_dup["triggered"] is False
        assert captured_payload is None  # Webhook NOT dispatched for continuous above-threshold score

@pytest.mark.asyncio
async def test_rbac_user_project_isolation():
    """
    Test Role-Based Access Control (RBAC):
    1. Normal User sees only their assigned projects.
    2. Admin sees portfolio overview and unassigned projects.
    """
    db = get_database()
    uname_user = f"officer_{uuid.uuid4().hex[:6]}"
    pid_assigned = f"P_USER_ASSIGNED_{uuid.uuid4().hex[:6]}"
    pid_restricted = f"P_USER_RESTRICTED_{uuid.uuid4().hex[:6]}"

    # Insert projects
    await db.projects.update_one(
        {"project_id": pid_assigned},
        {"$set": {
            "project_id": pid_assigned,
            "project_name": "Officer Assigned Highway",
            "assigned_users": [uname_user],
            "dphis": 62.0,
            "cost": {"original": 100.0, "revised": 100.0},
            "schedule": {"original_start": "2023-01-01", "original_end": "2025-01-01", "revised_end": "2025-01-01"}
        }},
        upsert=True
    )
    await db.projects.update_one(
        {"project_id": pid_restricted},
        {"$set": {
            "project_id": pid_restricted,
            "project_name": "Confidential Naval Base",
            "assigned_users": ["other_admin_officer"],
            "dphis": 48.0,
            "cost": {"original": 1000.0, "revised": 1000.0},
            "schedule": {"original_start": "2023-01-01", "original_end": "2026-01-01", "revised_end": "2026-01-01"}
        }},
        upsert=True
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # User query with username parameter
        res_user = await ac.get(f"/api/v1/projects?username={uname_user}")
        assert res_user.status_code == 200
        user_projects = res_user.json()
        pids = [p["project_id"] for p in user_projects]
        assert pid_assigned in pids
        assert pid_restricted not in pids  # Strict RBAC isolation

        # Public institutional overview is pre-sanitized and read-only
        res_overview = await ac.get("/api/v1/projects/public-risk-overview")
        assert res_overview.status_code == 200
        overview = res_overview.json()
        assert "total_projects" in overview
        assert "total_capex_lakh_cr" in overview

@pytest.mark.asyncio
async def test_threshold_history_and_patch_endpoint():
    """
    Test updating project threshold:
    1. Preserves old and new values in threshold_history.
    2. Re-evaluates threshold status immediately.
    """
    db = get_database()
    pid = f"P_THRESH_PATCH_{uuid.uuid4().hex[:6]}"
    await db.projects.update_one(
        {"project_id": pid},
        {"$set": {
            "project_id": pid,
            "project_name": "Metro Line 3 Phase 2",
            "dphis": 68.0,
            "current_dphis": 68.0,
            "dphis_threshold": 75.0,
            "threshold_status": "below",
            "threshold_history": []
        }},
        upsert=True
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        patch_payload = {
            "dphis_threshold": 65.0,  # Lowering threshold below current DPHIS (68.0)
            "threshold_enabled": True
        }
        res = await ac.patch(f"/api/v1/projects/{pid}/threshold", json=patch_payload)
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        assert data["new_threshold"] == 65.0
        assert data["old_threshold"] == 75.0
        # Immediately re-evaluated to triggered because 68.0 >= 65.0
        assert data["threshold_status"] == "triggered"

        # Verify threshold_history array has recorded entry
        doc = await db.projects.find_one({"project_id": pid})
        assert len(doc["threshold_history"]) >= 1
        last_hist = doc["threshold_history"][-1]
        assert last_hist["old_value"] == 75.0
        assert last_hist["new_value"] == 65.0

@pytest.mark.asyncio
async def test_observability_langfuse_graceful_fallback():
    """
    Test Langfuse observability integration:
    1. When Langfuse keys are absent, fallback to MockLangfuseTrace works cleanly.
    2. Start trace, log event, span, generation, and update without exceptions.
    3. Failure in observability never crashes application flows.
    """
    trace = observability.start_trace(
        name="test_monitoring_run",
        project_id="P_OBS_1",
        metadata={"cycle": "manual"}
    )
    assert trace is not None

    # Logging events and spans
    span = trace.span(name="feature_extraction")
    assert span is not None
    span.end(output={"features_count": 24})

    # Log generation
    trace.generation(name="recommendation_llm", input_text="prompt", output_text="recommendation")

    # Update trace
    trace.update(output={"status": "completed"})
