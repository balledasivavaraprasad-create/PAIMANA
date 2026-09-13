import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.db.mongodb import connect_to_mongo, close_mongo_connection
from app.services.feature_service import engineer_features, FEATURE_COLUMNS
from app.services.dphis_service import calculate_dphis
from app.ml.models.cost_model import cost_model
from app.ml.models.delay_model import delay_model
from app.agents.investigator import run_investigation

@pytest.fixture(autouse=True)
async def setup_db():
    await connect_to_mongo()
    yield
    # Keep connection open for tests

@pytest.mark.asyncio
async def test_health():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get("/health")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "healthy"

@pytest.mark.asyncio
async def test_feature_engineering_and_dphis():
    project = {
        "project_id": "P1024",
        "state": "Uttar Pradesh",
        "sector": "Roads & Highways",
        "cost": {"original": 3800.0, "revised": 4218.0},
        "schedule": {
            "original_start": "2023-01-01",
            "original_end": "2025-12-31",
            "revised_end": "2027-04-30"
        }
    }
    snapshots = [
        {
            "snapshot_date": "2026-06-01",
            "physical_progress": 32.0,
            "financial_progress": 58.0,
            "cumulative_expenditure": 2446.0,
            "milestones": {"completed": 4, "delayed": 3, "pending": 5, "total": 12},
            "weather": {"rainfall_mm": 80.0, "wind_speed_kmh": 14.0}
        },
        {
            "snapshot_date": "2026-07-01",
            "physical_progress": 33.0,
            "financial_progress": 60.0,
            "cumulative_expenditure": 2530.0,
            "milestones": {"completed": 4, "delayed": 3, "pending": 5, "total": 12},
            "weather": {"rainfall_mm": 110.0, "wind_speed_kmh": 16.0}
        },
        {
            "snapshot_date": "2026-08-01",
            "physical_progress": 34.0,
            "financial_progress": 62.0,
            "cumulative_expenditure": 2615.0,
            "milestones": {"completed": 4, "delayed": 3, "pending": 5, "total": 12},
            "weather": {"rainfall_mm": 135.0, "wind_speed_kmh": 18.0}
        }
    ]

    features = engineer_features(project, snapshots)
    for col in FEATURE_COLUMNS:
        assert col in features

    assert features["physical_financial_gap"] == 28.0  # 62 - 34
    assert features["cost_escalation"] == pytest.approx(0.11, abs=0.02)

    c_res = cost_model.predict(features)
    d_res = delay_model.predict(features)

    dphis = calculate_dphis("P1024", features, c_res["cost_risk_score"], d_res["time_risk_score"])
    assert dphis.dphis > 25.0
    assert dphis.level.value in ("moderate", "high", "critical")
    assert dphis.components.time > 0
    assert dphis.components.progress > 0

@pytest.mark.asyncio
async def test_api_projects_and_predictions():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Projects list
        res = await ac.get("/api/v1/projects?limit=5")
        assert res.status_code == 200
        projects = res.json()
        assert len(projects) > 0

        # Predictions for P1024
        pred_res = await ac.get("/api/v1/projects/P1024/predictions")
        assert pred_res.status_code == 200
        pred_data = pred_res.json()
        assert "cost" in pred_data
        assert "delay" in pred_data
        assert len(pred_data["top_shap_factors"]) > 0

        # Risk for P1024
        risk_res = await ac.get("/api/v1/projects/P1024/risk")
        assert risk_res.status_code == 200
        risk_data = risk_res.json()
        assert "dphis" in risk_data
        assert "components" in risk_data

@pytest.mark.asyncio
async def test_agentic_investigation():
    report = await run_investigation("P1024")
    assert report.project_id == "P1024"
    assert len(report.findings) >= 2
    assert len(report.recommendations) >= 2
    assert len(report.tools_executed) >= 4
    assert report.overall_confidence > 0.80

@pytest.mark.asyncio
async def test_chat_api():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        chat_res = await ac.post("/api/v1/chat", json={"message": "Why is P1024 critical?"})
        assert chat_res.status_code == 200
        chat_data = chat_res.json()
        assert "reply" in chat_data
        assert chat_data["intent"] == "RISK_EXPLANATION"
        assert len(chat_data["suggested_actions"]) > 0

@pytest.mark.asyncio
async def test_analytics_overview():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get("/api/v1/analytics/overview")
        assert res.status_code == 200
        data = res.json()
        assert data["total_projects"] >= 1500
        assert data["critical"] > 0
