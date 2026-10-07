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
        await db.investigations.create_index([("investigation_id", ASCENDING)], unique=True)
        await db.investigations.create_index([("status", ASCENDING)])

        # Domain collections for InfraBuild contract layer
        await db.project_snapshots.create_index([("observed_at", DESCENDING)])
        await db.project_snapshots.create_index([("report_period", ASCENDING)])
        await db.project_snapshots.create_index([("snapshot_hash", ASCENDING)])
        await db.predictions.create_index([("snapshot_id", ASCENDING)])
        await db.project_events.create_index([("project_id", ASCENDING), ("created_at", DESCENDING)])
        await db.project_events.create_index([("event_type", ASCENDING)])
        await db.evidence.create_index([("investigation_id", ASCENDING)])
        await db.hypotheses.create_index([("investigation_id", ASCENDING)])
        await db.recommendations.create_index([("investigation_id", ASCENDING)])
        await db.interventions.create_index([("project_id", ASCENDING)])
        await db.intervention_outcomes.create_index([("intervention_id", ASCENDING)])
        await db.peer_analyses.create_index([("project_id", ASCENDING), ("created_at", DESCENDING)])
        await db.data_quality.create_index([("project_id", ASCENDING)])
        await db.audit_logs.create_index([("created_at", DESCENDING)])
        await db.audit_logs.create_index([("target_id", ASCENDING)])
        await db.notification_deliveries.create_index([("status", ASCENDING)])
        await db.outbox_events.create_index([("status", ASCENDING), ("next_retry_at", ASCENDING)])
        await db.outbox_events.create_index([("event_id", ASCENDING)])
        await db.monitoring_cycles.create_index([("created_at", DESCENDING)])
        await db.monitoring_cycles.create_index([("started_at", DESCENDING)])

        logger.info("MongoDB indexes verified and initialized.")

    except Exception as e:
        logger.error(f"Error creating indexes: {e}")
