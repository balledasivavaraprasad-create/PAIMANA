import pytest
from httpx import ASGITransport, AsyncClient

from app.db.mongodb import connect_to_mongo
from app.main import app
from app.security.jwt import create_access_token
from app.models.user import UserRole


@pytest.fixture
async def client():
    await connect_to_mongo()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


def admin_header():
    token = create_access_token({"sub": "admin", "role": UserRole.ADMIN.value})
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_monitoring_status_contract(client):
    resp = await client.get("/api/system/monitoring-status", headers=admin_header())
    assert resp.status_code == 200
    body = resp.json()
    assert "status" in body
    assert "projects_monitored" in body
    assert "stale_projects" in body


@pytest.mark.asyncio
async def test_analytics_overview_does_not_fabricate_average(client):
    resp = await client.get("/api/analytics/overview-contract", headers=admin_header())
    assert resp.status_code == 200
    body = resp.json()
    assert "average_dphis" in body
    if body["project_count"] == 0:
        assert body["average_dphis"] is None
    else:
        assert body["average_dphis"] is None or isinstance(body["average_dphis"], (int, float))


@pytest.mark.asyncio
async def test_investigations_list_contract(client):
    resp = await client.get("/api/investigations", headers=admin_header())
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_missing_project_structured_error(client):
    resp = await client.get("/api/projects/DOES-NOT-EXIST/risk-summary", headers=admin_header())
    assert resp.status_code == 404
    body = resp.json()
    assert body["error"]["code"] == "PROJECT_NOT_FOUND"
    assert "request_id" in body["error"]
