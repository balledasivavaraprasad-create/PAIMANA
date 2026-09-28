import pytest
from pydantic import ValidationError
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.models.project import ProjectCreate, ProjectThresholdUpdate, Cost, Schedule, Location
from app.models.snapshot import SnapshotCreate
from app.models.alert import Alert
from app.db.mongodb import connect_to_mongo

@pytest.fixture(autouse=True)
async def setup_db():
    await connect_to_mongo()
    yield

def test_cost_validation():
    # Valid cost
    c = Cost(original=100.0, revised=120.0)
    assert c.original == 100.0
    assert c.revised == 120.0
    assert c.currency == "INR_CR"

    # Invalid: original cost <= 0
    with pytest.raises(ValidationError):
        Cost(original=0.0, revised=100.0)

    # Invalid: revised cost <= 0
    with pytest.raises(ValidationError):
        Cost(original=100.0, revised=-10.0)

def test_location_validation():
    # Valid location
    loc = Location(latitude=19.076, longitude=72.877, district="Mumbai", state="Maharashtra")
    assert loc.state == "Maharashtra"

    # Invalid latitude > 90
    with pytest.raises(ValidationError):
        Location(latitude=95.0, longitude=72.877, district="Mumbai", state="Maharashtra")

    # Invalid longitude < -180
    with pytest.raises(ValidationError):
        Location(latitude=19.076, longitude=-185.0, district="Mumbai", state="Maharashtra")

def test_project_create_missing_required_fields():
    # Missing project_name, ministry, cost, schedule
    with pytest.raises(ValidationError):
        ProjectCreate(
            project_id="P_VAL_1",
            department="Railways",
            sector="Railways",
            state="Delhi"
        )

def test_project_threshold_validation():
    # Valid threshold
    p = ProjectThresholdUpdate(dphis_threshold=75.0, threshold_enabled=True)
    assert p.dphis_threshold == 75.0

    # Invalid threshold < 1.0
    with pytest.raises(ValidationError):
        ProjectThresholdUpdate(dphis_threshold=0.0)

    # Invalid threshold > 100.0
    with pytest.raises(ValidationError):
        ProjectThresholdUpdate(dphis_threshold=105.0)

def test_snapshot_create_validation():
    # Valid snapshot
    snap = SnapshotCreate(
        project_id="P_VAL_1",
        snapshot_date="2026-08-01",
        physical_progress=45.5,
        financial_progress=50.0,
        cumulative_expenditure=500.0
    )
    assert snap.physical_progress == 45.5

    # Invalid physical progress > 100
    with pytest.raises(ValidationError):
        SnapshotCreate(
            project_id="P_VAL_1",
            snapshot_date="2026-08-01",
            physical_progress=105.0,
            financial_progress=50.0,
            cumulative_expenditure=500.0
        )

    # Invalid physical progress < 0
    with pytest.raises(ValidationError):
        SnapshotCreate(
            project_id="P_VAL_1",
            snapshot_date="2026-08-01",
            physical_progress=-5.0,
            financial_progress=50.0,
            cumulative_expenditure=500.0
        )

@pytest.mark.asyncio
async def test_api_rejects_malformed_project_payload():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Send empty payload to POST /api/v1/projects
        res = await ac.post("/api/v1/projects", json={})
        assert res.status_code == 422
        data = res.json()
        assert "detail" in data

        # Send invalid cost <= 0 to POST /api/v1/projects
        bad_cost_payload = {
            "project_id": "P_INVALID_COST",
            "project_name": "Test Corridor",
            "ministry": "MoRTH",
            "department": "Highways",
            "sector": "Roads",
            "state": "Haryana",
            "location": {"latitude": 28.5, "longitude": 77.0, "district": "Gurgaon", "state": "Haryana"},
            "cost": {"original": -50.0, "revised": 100.0},
            "schedule": {"original_start": "2023-01-01", "original_end": "2025-01-01", "revised_end": "2025-01-01"}
        }
        res_bad = await ac.post("/api/v1/projects", json=bad_cost_payload)
        assert res_bad.status_code == 422
