from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "PAIMANA AI Decision-Support Platform"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "paimana-super-secret-production-grade-security-token-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # MongoDB
    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "paimana_intelligence"

    # Environmental & GIS
    OPEN_METEO_BASE_URL: str = "https://api.open-meteo.com/v1/forecast"
    OPEN_ELEVATION_BASE_URL: str = "https://api.open-meteo.com/v1/elevation"

    # Alerting & Webhooks
    N8N_WEBHOOK_URL: str = "http://localhost:5678/webhook/paimana-risk-alert"
    N8N_RISK_WEBHOOK_URL: str = "https://sivavaraprasad.app.n8n.cloud/webhook/project-risk-event"
    N8N_TEST_WEBHOOK_URL: str = "https://sivavaraprasad.app.n8n.cloud/webhook-test/project-risk-event"
    ALERT_COOLDOWN_HOURS: int = 24

    # LLM Settings
    LLM_PROVIDER: str = "gemini"  # gemini, openai, groq, mock
    GEMINI_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    GROQ_API_KEY: Optional[str] = None
    LLM_MODEL: str = "gemini-2.0-flash"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
