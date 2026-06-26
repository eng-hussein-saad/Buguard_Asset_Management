from __future__ import annotations

import asyncio
from logging.config import fileConfig

from alembic import context
from app.core.config import get_settings
from app.db.base import metadata
from sqlalchemy import Connection, pool
from sqlalchemy.ext.asyncio import async_engine_from_config

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Alembic reads sqlalchemy.url from alembic.ini by default, but this project
# injects the real database URL from application settings at runtime.
config.set_main_option("sqlalchemy.url", str(get_settings().database_url))
target_metadata = metadata


def run_migrations_offline() -> None:
    """Run migrations without opening a database connection.

    Alembic uses this mode to emit SQL scripts directly from the configured URL,
    which is useful for reviewing or applying migrations manually.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Configure Alembic with an active connection and execute migrations."""
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Create the async SQLAlchemy engine used by normal online migrations."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Bridge Alembic's synchronous entry point to the async migration runner."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
