from typing import Optional

from pydantic_settings import BaseSettings
from pydantic import field_validator


class Settings(BaseSettings):
    PROJECT_NAME: str = "SarcomFasttrack API"
    API_V1_STR: str = "/api/v1"
    DATABASE_URL: Optional[str] = None
    DB_HOST: str
    DB_PORT: int = 5432
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str
    BACKEND_CORS_ORIGINS: list[str] = ["*"]
    SECRET_KEY: str = "change-me"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    ALGORITHM: str = "HS256"
    FHIR_ENABLED: bool = True

    # FHIR Server Configuration
    # Default uses host.docker.internal to access services on the host machine from Docker containers.
    # Override via environment variable (e.g., in .env file) if needed.
    # For local development outside Docker, use: http://localhost:32783/csp/healthshare/demo/fhir/r4
    FHIR_SERVER_URL: str = (
        "http://host.docker.internal:32783/csp/healthshare/demo/fhir/r4"
    )
    FHIR_SERVER_USER: str = "_SYSTEM"
    FHIR_SERVER_PASSWORD: str = "ISCDEMO"
    
    # IRIS Database Configuration (for vector search)
    # Use localhost for local development, override with host.docker.internal in Docker
    IRIS_HOST: str = "localhost"
    IRIS_PORT: int = 32783
    IRIS_NAMESPACE: str = "DEMO"
    IRIS_USERNAME: str = "_SYSTEM"
    IRIS_PASSWORD: str = "ISCDEMO"
    IRIS_SQL_URL: str = "http://localhost:32783/api/atelier/v1/DEMO/action/query"

    @field_validator("DB_PORT", mode="before")
    @classmethod
    def coerce_db_port(cls, v):
        # Treat empty string / None as default 5432 to avoid startup failure when secret is unset.
        if v is None or (isinstance(v, str) and not v.strip()):
            return 5432
        return int(v)

    class Config:
        case_sensitive = True
        env_file = ".env"
        extra = "ignore"


settings = Settings()
