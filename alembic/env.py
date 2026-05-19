from __future__ import annotations

import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# Interpret the config file for Python logging.
if context.config.config_file_name is not None:
    fileConfig(context.config.config_file_name)


def get_url() -> str:
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        return db_url
    host = os.getenv("DB_HOST", "")
    name = os.getenv("DB_NAME", "")
    user = os.getenv("DB_USER", "")
    password = os.getenv("DB_PASSWORD", "")
    port = os.getenv("DB_PORT", "5432")
    return f"postgresql+psycopg://{user}:{password}@{host}:{port}/{name}"


from sqlmodel import SQLModel
from app.models import *  # noqa

config = context.config
config.set_main_option("sqlalchemy.url", get_url())
target_metadata = SQLModel.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
