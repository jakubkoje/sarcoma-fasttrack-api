from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.api import api_router
from app.db.database_connection import get_connection
from app.db.migrations import ensure_user_salt_column, ensure_user_role_column
import psycopg

app = FastAPI(title=settings.PROJECT_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.api_route("/", methods=["GET", "HEAD"])
def read_root():
    return {"Hello": "World", "docs": "/docs"}


@app.get("/health/db")
def db_health():
    """
    Simple database connectivity check.
    """
    try:
        with get_connection() as conn:
            conn.execute("SELECT 1;").fetchone()
        return {"status": "ok"}
    except psycopg.Error as exc:
        # Surface a clear error while avoiding leaking internals
        raise HTTPException(status_code=503, detail=f"DB unavailable: {exc.pgerror or exc.diag.message_primary or str(exc)}")
