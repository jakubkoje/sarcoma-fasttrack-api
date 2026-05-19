from psycopg import sql

from app.db.database_connection import get_connection


def ensure_user_salt_column() -> None:
    """
    Ensure 'salt' column exists on users table.
    Safe to run repeatedly; will only add column if missing.
    """
    query = """
    SELECT 1
    FROM information_schema.columns
    WHERE table_name = 'users' AND column_name = 'salt'
    """
    alter = sql.SQL("ALTER TABLE users ADD COLUMN salt VARCHAR NOT NULL DEFAULT ''")
    backfill = sql.SQL("UPDATE users SET salt = '' WHERE salt IS NULL")

    with get_connection() as conn:
        exists = conn.execute(query).fetchone()
        if not exists:
            conn.execute(alter)
            conn.execute(backfill)
            conn.commit()


def ensure_user_role_column() -> None:
    """
    Ensure 'role' column exists on users table.
    """
    query = """
    SELECT 1
    FROM information_schema.columns
    WHERE table_name = 'users' AND column_name = 'role'
    """
    alter = sql.SQL("ALTER TABLE users ADD COLUMN role VARCHAR NOT NULL DEFAULT 'coordinator'")
    with get_connection() as conn:
        exists = conn.execute(query).fetchone()
        if not exists:
            conn.execute(alter)
            conn.commit()
