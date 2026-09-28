from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.config.settings import settings
from app.config.logging import logger

class DatabaseManager:
    client: AsyncIOMotorClient = None
    db: AsyncIOMotorDatabase = None

db_manager = DatabaseManager()

async def connect_to_mongo():
    try:
        db_manager.client = AsyncIOMotorClient(settings.MONGODB_URL, serverSelectionTimeoutMS=2000)
        db_manager.db = db_manager.client[settings.MONGODB_DB_NAME]
        # Quick ping
        await db_manager.client.admin.command('ping')
        logger.info(f"Connected successfully to MongoDB at {settings.MONGODB_URL}, database: {settings.MONGODB_DB_NAME}")
    except Exception as e:
        logger.warning(f"Failed to connect directly to MongoDB: {e}. Initializing in-memory AsyncMongoMockClient fallback.")
        try:
            from mongomock_motor import AsyncMongoMockClient
            if db_manager.client is None or not isinstance(db_manager.client, AsyncMongoMockClient):
                db_manager.client = AsyncMongoMockClient()
                db_manager.db = db_manager.client[settings.MONGODB_DB_NAME]
                logger.info("Initialized in-memory AsyncMongoMockClient successfully.")
            await _seed_mock_db_if_empty(db_manager.db)
        except Exception as mock_err:
            logger.error(f"Could not initialize mock MongoDB: {mock_err}")

async def _seed_mock_db_if_empty(db):
    try:
        from datetime import datetime, timezone, timedelta
        from app.security.hashing import get_password_hash
        from app.models.user import UserRole
        from app.db.seeded_data import (
            DEFAULT_USER_10_IDS,
            DEFAULT_ADMIN_28_IDS,
            get_all_seeded_projects
        )

        now = datetime.now(timezone.utc)
        user_10_ids = DEFAULT_USER_10_IDS
        admin_28_ids = DEFAULT_ADMIN_28_IDS

        # 1. Seed Default Users if not present
        existing_user = await db.users.find_one({"email": "ramesh.kumar@morth.gov.in"})
        if not existing_user:
            users_to_seed = [
                {
                    "username": "ramesh.kumar",
                    "email": "ramesh.kumar@morth.gov.in",
                    "full_name": "Dr. Ramesh Kumar",
                    "ministry": "Road Transport & Highways",
                    "designation": "Project Director",
                    "role": UserRole.PROJECT_OFFICER,
                    "hashed_password": get_password_hash("Password1234!"),
                    "is_active": True,
                    "is_verified": True,
                    "dphis_alert_threshold": 75.0,
                    "assigned_projects": user_10_ids,
                    "created_at": now
                },
                {
                    "username": "balledasivavaraprasad",
                    "email": "balledasivavaraprasad@gmail.com",
                    "full_name": "Balleda Siva Vara Prasad",
                    "ministry": "Ministry of Housing & Urban Affairs",
                    "designation": "Project Director",
                    "role": UserRole.PROJECT_OFFICER,
                    "hashed_password": get_password_hash("paimana2026"),
                    "is_active": True,
                    "is_verified": True,
                    "dphis_alert_threshold": 75.0,
                    "assigned_projects": user_10_ids,
                    "created_at": now
                },
                {
                    "username": "balledasivavaraprasad123",
                    "email": "balledasivavaraprasad123@gmail.com",
                    "full_name": "B Siva",
                    "ministry": "Ministry of Housing & Urban Affairs",
                    "designation": "Project Officer",
                    "role": UserRole.PROJECT_OFFICER,
                    "hashed_password": get_password_hash("paimana2026"),
                    "is_active": True,
                    "is_verified": True,
                    "dphis_alert_threshold": 75.0,
                    "assigned_projects": user_10_ids,
                    "created_at": now
                },
                {
                    "username": "admin",
                    "email": "admin@paimana.gov.in",
                    "full_name": "National Director (MoSPI)",
                    "ministry": "Ministry of Statistics and Programme Implementation",
                    "designation": "National Director",
                    "role": UserRole.ADMIN,
                    "hashed_password": get_password_hash("paimana2026"),
                    "is_active": True,
                    "is_verified": True,
                    "dphis_alert_threshold": 75.0,
                    "assigned_projects": admin_28_ids,
                    "created_at": now
                },
                {
                    "username": "analyst",
                    "email": "analyst@paimana.gov.in",
                    "full_name": "Senior Project Intelligence Analyst",
                    "ministry": "Ministry of Statistics and Programme Implementation",
                    "designation": "Lead Analyst",
                    "role": UserRole.MO_SPI_ANALYST,
                    "hashed_password": get_password_hash("paimana2026"),
                    "is_active": True,
                    "is_verified": True,
                    "dphis_alert_threshold": 75.0,
                    "assigned_projects": admin_28_ids,
                    "created_at": now
                }
            ]
            await db.users.insert_many(users_to_seed)

        # 2. Seed All Sovereign Projects into db.projects
        proj_count = await db.projects.count_documents({})
        if proj_count < 25:
            all_projects = get_all_seeded_projects()
            existing_pids = set()
            async for p in db.projects.find({}, {"project_id": 1}):
                existing_pids.add(p.get("project_id"))

            to_insert = []
            for p in all_projects:
                if p["project_id"] not in existing_pids:
                    p_copy = dict(p)
                    # Ensure assigned_users are populated
                    if p["project_id"] in user_10_ids:
                        p_copy["assigned_users"] = ["ramesh.kumar", "balledasivavaraprasad", "balledasivavaraprasad123", "admin", "analyst"]
                    else:
                        p_copy["assigned_users"] = ["admin", "analyst"]
                    to_insert.append(p_copy)

            # Ensure P1024 is included
            if "P1024" not in existing_pids and not any(x.get("project_id") == "P1024" for x in to_insert):
                to_insert.append({
                    "project_id": "P1024",
                    "project_name": "NH-48 Varanasi-Ranchi Expressway",
                    "ministry": "Ministry of Road Transport and Highways",
                    "department": "National Highway Authority",
                    "sector": "Roads & Highways",
                    "state": "Uttar Pradesh",
                    "location": {"latitude": 25.3176, "longitude": 82.9739, "district": "Varanasi", "state": "Uttar Pradesh"},
                    "cost": {"original": 4200.0, "revised": 5400.0, "currency": "INR_CR"},
                    "schedule": {"original_start": "2023-01-01", "original_end": "2025-12-31", "revised_end": "2027-04-30"},
                    "metadata": {"project_type": "Roads", "implementing_agency": "NHAI"},
                    "dphis": 91.0,
                    "current_dphis": 91.0,
                    "dphis_threshold": 75.0,
                    "threshold_status": "triggered",
                    "threshold_history": [],
                    "risk_level": "critical",
                    "schedule_slippage_months": 28.0,
                    "physical_progress_pct": 45.0,
                    "financial_progress_pct": 68.0,
                    "assigned_users": ["ramesh.kumar", "balledasivavaraprasad", "admin", "analyst"],
                    "data_quality_score": 95.0,
                    "created_at": now,
                    "updated_at": now
                })

            if to_insert:
                await db.projects.insert_many(to_insert)

            # 3. Seed snapshots
            snapshots_count = await db.project_snapshots.count_documents({})
            if snapshots_count == 0:
                snapshots = []
                for p in to_insert:
                    pid = p["project_id"]
                    for i in range(6):
                        s_date = (now - timedelta(days=(5 - i) * 30)).strftime("%Y-%m-%d")
                        snapshots.append({
                            "project_id": pid,
                            "snapshot_date": s_date,
                            "physical_progress": min(100.0, float(p.get("physical_progress_pct", 50.0)) - (5 - i) * 2.0),
                            "financial_progress": min(100.0, float(p.get("financial_progress_pct", 50.0)) - (5 - i) * 2.5),
                            "cumulative_expenditure": float(p.get("cost", {}).get("revised", 2000.0)) * 0.5,
                            "milestones": {"completed": 4 + i, "delayed": 2, "pending": 4, "total": 10},
                            "weather": {"rainfall_mm": 40.0, "temperature_c": 30.0, "wind_speed_kmh": 10.0, "disruption_flag": False},
                            "created_at": now
                        })
                if snapshots:
                    await db.project_snapshots.insert_many(snapshots)
    except Exception as seed_err:
        logger.warning(f"Error seeding mock database: {seed_err}")

async def close_mongo_connection():
    if db_manager.client:
        db_manager.client.close()
        logger.info("Closed MongoDB connection.")

def get_database() -> AsyncIOMotorDatabase:
    return db_manager.db
