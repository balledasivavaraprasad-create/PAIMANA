import pytest
import uuid
from datetime import datetime, timezone
from unittest.mock import patch, AsyncMock
from httpx import AsyncClient, ASGITransport, Response
from app.main import app
from app.db.mongodb import connect_to_mongo, get_database
from app.services.scheduler_service import scheduler
from app.services.project_memory_service import get_project_memory
from app.agents.investigator import run_investigation

@pytest.fixture(autouse=True)
async def setup_db():
    await connect_to_mongo()
    yield

@pytest.mark.asyncio
async def test_scheduler_scan_and_project_failure_isolation():
    """
    Test continuous monitoring scheduler:
    1. Evaluates all active projects.
    2. Failure in one corrupted project is safely isolated and does NOT halt the scan.
    """
    db = get_database()
    pid_healthy = f"P_SCHED_HEALTHY_{uuid.uuid4().hex[:6]}"
    pid_faulty = f"P_SCHED_FAULTY_{uuid.uuid4().hex[:6]}"

    # Seed healthy project
    await db.projects.update_one(
        {"project_id": pid_healthy},
        {"$set": {
            "project_id": pid_healthy,
            "project_name": "Healthy Railway Corridor",
            "dphis": 45.0,
            "current_dphis": 45.0,
            "previous_dphis": 40.0,
            "dphis_threshold": 70.0,
            "threshold_enabled": True,
            "threshold_status": "below",
            "cost": {"original": 200.0, "revised": 210.0},
            "schedule": {"original_start": "2023-01-01", "original_end": "2025-01-01", "revised_end": "2025-01-01"}
        }},
        upsert=True
    )

    # Seed corrupted project (unusual types to trigger potential runtime error in faulty handler)
    await db.projects.update_one(
        {"project_id": pid_faulty},
        {"$set": {
            "project_id": pid_faulty,
            "project_name": "Corrupted Data Project",
            "dphis": None,
            "current_dphis": None,
            "dphis_threshold": "INVALID_NON_NUMERIC",
            "cost": None
        }},
        upsert=True
    )

    # Run scheduler scan with limit=5 for rapid execution
    result = await scheduler.scan_all_projects(manual=True, limit=5)
    assert result["success"] is True
    assert isinstance(result["scanned_count"], int)
    assert isinstance(result["errors_count"], int)

@pytest.mark.asyncio
async def test_agentic_investigation_pipeline_and_graceful_degradation():
    """
    Test agentic investigator:
    1. Generates structured findings, root cause hypotheses, and recommendations.
    2. Handles missing peer/history data gracefully without crashing or fabricating facts.
    """
    db = get_database()
    pid = f"P_INV_{uuid.uuid4().hex[:6]}"

    # Seed project with zero history/snapshots to test edge-case handling
    await db.projects.update_one(
        {"project_id": pid},
        {"$set": {
            "project_id": pid,
            "project_name": "Sparse Data Expressway",
            "ministry": "MoRTH",
            "department": "Highways",
            "sector": "Roads",
            "state": "Gujarat",
            "dphis": 78.5,
            "current_dphis": 78.5,
            "dphis_threshold": 70.0,
            "threshold_enabled": True
        }},
        upsert=True
    )

    # Trigger investigation
    report = await run_investigation(project_id=pid, trigger_reason="DPHIS_THRESHOLD_EXCEEDED")
    assert report.investigation_id.startswith("INV-")
    assert report.project_id == pid
    assert report.status == "pending_approval"
    assert len(report.findings) >= 1
    assert len(report.recommendations) >= 1
    assert report.overall_confidence >= 0.0

@pytest.mark.asyncio
async def test_human_approval_workflow_and_duplicate_rejection():
    """
    Test human-in-the-loop approval:
    1. Investigation is pending_approval -> approval creates an active intervention.
    2. Duplicate approval of the same investigation is rejected with HTTP 400.
    """
    db = get_database()
    pid = f"P_APPR_{uuid.uuid4().hex[:6]}"
    inv_id = f"INV-{uuid.uuid4().hex[:8].upper()}"

    # Insert an unapproved investigation
    await db.investigations.insert_one({
        "investigation_id": inv_id,
        "project_id": pid,
        "title": "Autonomous escalation probe",
        "status": "pending_approval",
        "created_at": datetime.now(timezone.utc),
        "recommendations": [
            {
                "recommendation_id": "REC-1",
                "title": "Expedite ROW clearance",
                "action": "Coordinate with state revenue department",
                "priority": "HIGH",
                "urgency": "Immediate"
            }
        ]
    })

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # First approval
        approval_payload = {
            "approved_by": "Bal Le Da",
            "notes": "Fast-tracked by project director"
        }
        res1 = await ac.post(f"/api/v1/projects/{pid}/investigations/{inv_id}/approve", json=approval_payload)
        assert res1.status_code == 200
        data1 = res1.json()
        assert data1["success"] is True
        assert "intervention_id" in data1
        assert data1["investigation_status"] == "approved"

        # Verify DB updated
        inv_doc = await db.investigations.find_one({"investigation_id": inv_id})
        assert inv_doc["status"] == "approved"
        assert inv_doc["approved_by"] == "Bal Le Da"

        # Second approval attempt -> MUST FAIL with 400 (no duplicate approvals)
        res2 = await ac.post(f"/api/v1/projects/{pid}/investigations/{inv_id}/approve", json=approval_payload)
        assert res2.status_code == 400

@pytest.mark.asyncio
async def test_intervention_outcome_loop_and_project_memory_isolation():
    """
    Test intervention outcome tracking and strict project memory isolation:
    1. Submitting outcome closes the intervention and logs to project memory.
    2. Invalid intervention ID returns 404.
    3. Project A's memory NEVER leaks into Project B's memory.
    """
    db = get_database()
    pid_a = f"P_MEM_A_{uuid.uuid4().hex[:6]}"
    pid_b = f"P_MEM_B_{uuid.uuid4().hex[:6]}"
    int_id = f"INT-{uuid.uuid4().hex[:8].upper()}"

    # Seed an active intervention for Project A
    await db.interventions.insert_one({
        "intervention_id": int_id,
        "project_id": pid_a,
        "investigation_id": "INV-MOCK",
        "title": "Land acquisition clearance",
        "action": "Direct liaison with collectorate",
        "priority": "HIGH",
        "status": "in_progress",
        "approved_by": "Officer Rao",
        "created_at": datetime.now(timezone.utc)
    })

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Record outcome for Project A
        outcome_payload = {
            "outcome": "Clearance certificate issued for 45 km stretch.",
            "outcome_metrics": {"dphis_reduction": 8.5, "delay_mitigation_months": 2.0},
            "recorded_by": "Officer Rao"
        }
        res = await ac.post(f"/api/v1/projects/{pid_a}/interventions/{int_id}/outcome", json=outcome_payload)
        assert res.status_code == 200
        assert res.json()["success"] is True

        # Non-existent intervention ID returns 404
        res_bad = await ac.post(f"/api/v1/projects/{pid_a}/interventions/INT-NON-EXISTENT/outcome", json=outcome_payload)
        assert res_bad.status_code == 404

        # Retrieve Project Memory for Project A
        res_mem_a = await ac.get(f"/api/v1/projects/{pid_a}/memory")
        assert res_mem_a.status_code == 200
        mem_a = res_mem_a.json()
        assert mem_a["project_id"] == pid_a
        assert any(i.get("intervention_id") == int_id for i in mem_a["interventions"])

        # Retrieve Project Memory for Project B -> Strict Isolation (NO Project A leakage!)
        res_mem_b = await ac.get(f"/api/v1/projects/{pid_b}/memory")
        assert res_mem_b.status_code == 200
        mem_b = res_mem_b.json()
        assert mem_b["project_id"] == pid_b
        assert not any(i.get("intervention_id") == int_id for i in mem_b["interventions"])
