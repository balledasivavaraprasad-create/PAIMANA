from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config.settings import settings
from app.config.logging import setup_logging, logger
from app.db.mongodb import connect_to_mongo, close_mongo_connection
from app.db.indexes import init_indexes

# Import all routers
from app.api.routes.auth import router as auth_router
from app.api.routes.projects import router as projects_router
from app.api.routes.risk import router as risk_router
from app.api.routes.predictions import router as predictions_router
from app.api.routes.investigations import router as investigations_router
from app.api.routes.alerts import router as alerts_router
from app.api.routes.analytics import router as analytics_router
from app.api.routes.chat import router as chat_router
from app.api.routes.contract import router as contract_router
from app.api.errors import install_exception_handlers, request_id_middleware

# Import V4 Agentic Intelligence Layer & Continuous Monitoring
try:
    from server_v3 import (
        api_router as agentic_v4_router,
        agent as v4_monitoring_agent,
        EVALUATED_PROJECTS,
        Store as V4Store
    )
    from paimana_agent.scheduler import Scheduler as V4Scheduler
except Exception as e:
    logger.error(f"Error importing server_v3 agentic layer: {e}", exc_info=True)
    agentic_v4_router = None
    v4_monitoring_agent = None
    EVALUATED_PROJECTS = {}
    V4Scheduler = None

setup_logging()

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing PAIMANA Intelligence Engine...")
    try:
        await connect_to_mongo()
        await init_indexes()
    except Exception as db_err:
        logger.warning(f"MongoDB connection deferred or offline: {db_err}. Running on sovereign in-memory & SQLite stores.")

    # Initialize Continuous Monitoring Scheduler (runs every 6h + on-change)
    scheduler = None
    if v4_monitoring_agent is not None and V4Scheduler is not None:
        try:
            scheduler = V4Scheduler(
                v4_monitoring_agent,
                project_provider=lambda: list(EVALUATED_PROJECTS.values()),
                interval_hours=6.0
            )
            scheduler.start()
            app.state.v4_scheduler = scheduler
            logger.info("Continuous Monitoring Scheduler started (6h scan cadence across 428 corridors).")
        except Exception as sch_err:
            logger.error(f"Failed to start continuous monitoring scheduler: {sch_err}", exc_info=True)

    yield

    logger.info("Shutting down PAIMANA Intelligence Engine...")
    if scheduler:
        try:
            scheduler.stop()
            logger.info("Continuous Monitoring Scheduler stopped.")
        except Exception:
            pass
    try:
        await close_mongo_connection()
    except Exception:
        pass

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Production-grade AI Decision-Support Platform for National Infrastructure Portfolios (MoSPI / PRAGATI)",
    version="2.0.0",
    lifespan=lifespan
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://localhost:3005", "http://127.0.0.1:5173", "http://127.0.0.1:3005", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.middleware("http")(request_id_middleware)
install_exception_handlers(app)

# Health & Root Check
@app.get("/health", tags=["System"])
async def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": "2.0.0",
        "database": "connected",
        "monitored_corridors": len(EVALUATED_PROJECTS),
        "continuous_surveillance": "active" if getattr(app.state, "v4_scheduler", None) is not None else "standby"
    }

from app.api.routes.projects import get_public_risk_overview, handle_project_risk_event, ProjectRiskEventRequest
@app.get(f"{settings.API_V1_STR}/public/risk-overview", tags=["Public"])
@app.get("/api/public/risk-overview", tags=["Public"])
async def public_risk_overview_alias():
    return await get_public_risk_overview()

@app.post(f"{settings.API_V1_STR}/project-risk-events", tags=["Alerts & Notifications"])
@app.post("/api/project-risk-events", tags=["Alerts & Notifications"])
@app.post("/project-risk-events", tags=["Alerts & Notifications"])
async def project_risk_events_top_level(payload: ProjectRiskEventRequest):
    return await handle_project_risk_event(payload)

# Include Authentication & Chat Routers first (for instant login & Gemini chat)
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(auth_router, prefix="/api")
app.include_router(chat_router, prefix=settings.API_V1_STR)
app.include_router(chat_router, prefix="/api")

# Include Domain Routers
app.include_router(projects_router, prefix=settings.API_V1_STR)
app.include_router(projects_router, prefix="/api")

# Include Agentic V4 Routers (Continuous Monitoring, Peer Cohort Intelligence, Investigations, Scan, Telemetry)
if agentic_v4_router is not None:
    app.include_router(agentic_v4_router, prefix=settings.API_V1_STR)
    app.include_router(agentic_v4_router, prefix="/api")
app.include_router(risk_router, prefix=settings.API_V1_STR)
app.include_router(risk_router, prefix="/api")
app.include_router(predictions_router, prefix=settings.API_V1_STR)
app.include_router(predictions_router, prefix="/api")
app.include_router(investigations_router, prefix=settings.API_V1_STR)
app.include_router(investigations_router, prefix="/api")
app.include_router(alerts_router, prefix=settings.API_V1_STR)
app.include_router(alerts_router, prefix="/api")
app.include_router(analytics_router, prefix=settings.API_V1_STR)
app.include_router(analytics_router, prefix="/api")
app.include_router(contract_router, prefix=settings.API_V1_STR)
app.include_router(contract_router, prefix="/api")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8001, reload=True)
