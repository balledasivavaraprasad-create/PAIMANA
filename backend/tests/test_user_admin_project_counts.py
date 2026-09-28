import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.db.mongodb import connect_to_mongo, get_database

@pytest.mark.asyncio
async def test_user_and_admin_project_counts():
    await connect_to_mongo()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 1. Admin account test via /api/v1/projects/my-projects
        res_admin = await ac.get("/api/v1/projects/my-projects?username=admin")
        assert res_admin.status_code == 200
        admin_projects = res_admin.json()
        assert len(admin_projects) >= 25, f"Admin must have at least 25 projects, got {len(admin_projects)}"
        assert len(admin_projects) == 28, f"Expected 28 projects for admin, got {len(admin_projects)}"

        # 2. User account test via /api/v1/projects/my-projects
        res_user = await ac.get("/api/v1/projects/my-projects?username=ramesh.kumar")
        assert res_user.status_code == 200
        user_projects = res_user.json()
        assert len(user_projects) == 10, f"User must have exactly 10 projects, got {len(user_projects)}"

        # 3. Siva user account test
        res_siva = await ac.get("/api/v1/projects/my-projects?username=balledasivavaraprasad")
        assert res_siva.status_code == 200
        siva_projects = res_siva.json()
        assert len(siva_projects) == 10, f"Siva user must have exactly 10 projects, got {len(siva_projects)}"

        # 4. Unknown/New user account test
        res_new = await ac.get("/api/v1/projects/my-projects?username=new_officer_test")
        assert res_new.status_code == 200
        new_projects = res_new.json()
        assert len(new_projects) == 10, f"New user must have exactly 10 projects, got {len(new_projects)}"

        # 5. /api/projects/my-projects route alias test
        res_alias_admin = await ac.get("/api/projects/my-projects?username=admin")
        assert res_alias_admin.status_code == 200
        assert len(res_alias_admin.json()) == 28

        res_alias_user = await ac.get("/api/projects/my-projects?username=ramesh.kumar")
        assert res_alias_user.status_code == 200
        assert len(res_alias_user.json()) == 10
