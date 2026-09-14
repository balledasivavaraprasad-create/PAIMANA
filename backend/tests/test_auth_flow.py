import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.db.mongodb import connect_to_mongo

@pytest.fixture(autouse=True)
async def setup_db():
    await connect_to_mongo()
    yield

@pytest.mark.asyncio
async def test_invalid_credentials_rejected():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.post("/api/auth/login", json={"email": "admin", "password": "wrongpassword"})
        assert res.status_code == 401
        assert "Invalid official email or password" in res.json().get("detail", "")

@pytest.mark.asyncio
async def test_valid_admin_credentials_returns_user():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.post("/api/auth/login", json={"email": "admin", "password": "paimana2026"})
        assert res.status_code == 200
        data = res.json()
        assert "access_token" in data
        assert data["username"] == "admin"
        assert data["role"] == "ADMIN"
        assert "MoSPI" in data["ministry"] or "Statistics" in data["ministry"]

@pytest.mark.asyncio
async def test_valid_morth_credentials_returns_user():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.post("/api/auth/login", json={"email": "ramesh.kumar@morth.gov.in", "password": "Password1234!"})
        assert res.status_code == 200
        data = res.json()
        assert "access_token" in data
        assert data["username"] == "ramesh.kumar"
        assert data["full_name"] == "Dr. Ramesh Kumar"
        assert data["ministry"] == "Road Transport & Highways"

@pytest.mark.asyncio
async def test_auth_me_protected_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Without token -> 401
        unauth_res = await ac.get("/api/auth/me")
        assert unauth_res.status_code == 401

        # With valid token
        login_res = await ac.post("/api/auth/login", json={"email": "ramesh.kumar@morth.gov.in", "password": "Password1234!"})
        token = login_res.json()["access_token"]

        me_res = await ac.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert me_res.status_code == 200
        me_data = me_res.json()
        assert me_data["username"] == "ramesh.kumar"
        assert me_data["full_name"] == "Dr. Ramesh Kumar"
        assert me_data["ministry"] == "Road Transport & Highways"
