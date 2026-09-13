from pymongo import ASCENDING, DESCENDING
from app.db.mongodb import get_database
from app.config.logging import logger

async def init_indexes():
    db = get_database()
    if db is None:
        logger.warning("Database not connected, skipping index creation.")
        return

    try:
        # Projects: unique on project_id
        await db.projects.create_index([("project_id", ASCENDING)], unique=True)
        await db.projects.create_index([("state", ASCENDING)])
        await db.projects.create_index([("sector", ASCENDING)])
        await db.projects.create_index([("dphis", DESCENDING)])

        # Project Snapshots: compound unique on project_id + snapshot_date
        await db.project_snapshots.create_index(
            [("project_id", ASCENDING), ("snapshot_date", ASCENDING)],
            unique=True
        )

        # Users: unique on username and email
        await db.users.create_index([("username", ASCENDING)], unique=True)
        await db.users.create_index([("email", ASCENDING)], unique=True)

        # Alerts: index on project_id, severity, and created_at
        await db.alerts.create_index([("project_id", ASCENDING), ("created_at", DESCENDING)])
        await db.alerts.create_index([("status", ASCENDING)])

        # Predictions & Risk Scores
        await db.predictions.create_index([("project_id", ASCENDING), ("timestamp", DESCENDING)])
        await db.risk_scores.create_index([("project_id", ASCENDING), ("timestamp", DESCENDING)])
        
        # Investigations
        await db.investigations.create_index([("project_id", ASCENDING), ("created_at", DESCENDING)])

        logger.info("MongoDB indexes verified and initialized.")
    except Exception as e:
        logger.error(f"Error creating indexes: {e}")
