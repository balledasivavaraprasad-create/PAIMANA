import pytest
from datetime import datetime, timezone

from app.db.mongodb import connect_to_mongo, get_database
from app.services.monitoring_pipeline import monitoring_service


@pytest.fixture
async def db():
    await connect_to_mongo()
    database = get_database()
    assert database is not None
    await database.projects.delete_many({"project_id": "PIPE-1"})
    await database.project_snapshots.delete_many({"project_id": "PIPE-1"})
    await database.project_events.delete_many({"project_id": "PIPE-1"})
    await database.investigations.delete_many({"project_id": "PIPE-1"})
    await database.predictions.delete_many({"project_id": "PIPE-1"})
    now = datetime.now(timezone.utc)
    await database.projects.insert_one(
        {
            "project_id": "PIPE-1",
            "project_name": "Pipeline Test Corridor",
            "ministry": "Road Transport & Highways",
            "department": "NHAI",
            "sector": "Roads & Highways",
            "state": "Uttar Pradesh",
            "cost": {"original": 1000.0, "revised": 1200.0},
            "schedule": {"original_start": "2023-01-01", "original_end": "2025-12-31", "revised_end": "2026-06-30"},
            "physical_progress_pct": 40.0,
            "financial_progress_pct": 62.0,
            "dphis": 55.0,
            "current_dphis": 55.0,
            "previous_dphis": 48.0,
            "dphis_threshold": 70.0,
            "schedule_slippage_months": 6.0,
            "last_observed_at": now,
            "updated_at": now,
        }
    )
    return database


@pytest.mark.asyncio
async def test_pipeline_persists_snapshot_and_prediction(db):
    result = await monitoring_service.ingest_project_update(
        "PIPE-1",
        {"physical_progress_pct": 44.0},
        trigger="test",
        force=True,
        queue_investigation=False,
    )
    assert result.project_id == "PIPE-1"
    assert result.material_change is True
    assert result.snapshot_hash
    assert result.dphis is None or isinstance(result.dphis, float)
    snap = await db.project_snapshots.find_one({"project_id": "PIPE-1", "snapshot_id": result.snapshot_id})
    assert snap is not None
    assert snap.get("snapshot_hash") == result.snapshot_hash


@pytest.mark.asyncio
async def test_pipeline_skips_without_material_change(db):
    first = await monitoring_service.ingest_project_update("PIPE-1", trigger="test", force=True, queue_investigation=False)
    second = await monitoring_service.ingest_project_update("PIPE-1", trigger="test", force=False, queue_investigation=False)
    assert first.material_change is True
    assert second.material_change is False
    assert second.skipped_reason == "no_material_change"
