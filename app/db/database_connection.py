import psycopg
from psycopg.rows import dict_row
from typing import Any, Iterator, Optional
from urllib.parse import quote_plus

from sqlmodel import Session, create_engine

from app.core.config import settings


def _database_url() -> str:
    # URL-encode password to be safe with special chars
    password = quote_plus(settings.DB_PASSWORD)
    return f"postgresql+psycopg://{settings.DB_USER}:{password}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"


# SQLModel engine/session for ORM-style access
engine = create_engine(_database_url(), pool_pre_ping=True)


def get_session() -> Iterator[Session]:
    with Session(engine) as session:
        yield session


# Legacy raw connection helpers (still available if needed)
def get_connection() -> psycopg.Connection:
    """
    Create a new psycopg connection to Postgres using environment-based settings.
    Relies on DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD being set.
    """
    return psycopg.connect(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        dbname=settings.DB_NAME,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        row_factory=dict_row,
    )


def yield_connection() -> Iterator[psycopg.Connection]:
    """
    Simple generator for dependency injection / context-managed use.
    """
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()


class Database:
    """
    Convenience wrapper to manage a single connection and provide simple helpers.
    Usage:
        with Database() as db:
            rows = db.fetch_all("SELECT 1")
    """

    def __init__(self) -> None:
        self.conn: Optional[psycopg.Connection] = None

    def __enter__(self) -> "Database":
        self.conn = get_connection()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if self.conn:
            self.conn.close()

    def _execute(self, query: str, params: Any = None):
        if not self.conn:
            raise RuntimeError("Database connection not initialized")
        return self.conn.execute(query, params or ())

    def fetch_one(self, query: str, params: Any = None, commit: bool = False) -> Any:
        cur = self._execute(query, params)
        if commit and self.conn:
            self.conn.commit()
        return cur.fetchone()

    def fetch_all(self, query: str, params: Any = None, commit: bool = False) -> list[Any]:
        cur = self._execute(query, params)
        if commit and self.conn:
            self.conn.commit()
        return cur.fetchall()

    def execute(self, query: str, params: Any = None) -> int:
        """
        Execute a statement and commit the transaction.
        Returns affected row count when available.
        """
        cur = self._execute(query, params)
        if self.conn:
            self.conn.commit()
        return cur.rowcount
