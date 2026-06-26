"""Database engine and session management.

This module configures the async SQLAlchemy database engine using the
application DATABASE_URL, creates a reusable async session factory, and
provides helper functions for FastAPI database access.

The `get_async_session` dependency should be used by API routes and services
that need database access. It creates one `AsyncSession` per request and closes
it automatically after the request finishes.

The `check_database_reachability` helper runs a lightweight `SELECT 1` query
and can be used by health checks to verify that PostgreSQL is reachable.
"""

from collections.abc import AsyncIterator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

import app.db.base  # noqa: F401
from app.core.config import Settings, get_settings


# Build the async database engine from application settings.
def create_engine(settings: Settings | None = None) -> AsyncEngine:
    active_settings = settings or get_settings()
    return create_async_engine(str(active_settings.database_url), pool_pre_ping=True)

# Global engine reused by the application.
engine = create_engine()

# Session factory used to create database sessions.
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


# Dependency that gives routes a database session and closes it afterward.
async def get_async_session() -> AsyncIterator[AsyncSession]:
    async with AsyncSessionLocal() as session:
        yield session



# Check that the database connection works.
async def check_database_reachability() -> int:
    async with AsyncSessionLocal() as session:
        result = await session.execute(text("SELECT 1"))
        return int(result.scalar_one())
