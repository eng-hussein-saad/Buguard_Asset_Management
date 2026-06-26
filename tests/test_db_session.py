import pytest
from app.core.config import Settings
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker



# Verify that create_engine() builds an async SQLAlchemy engine
# using the DATABASE_URL provided through Settings.
@pytest.mark.asyncio
async def test_async_engine_uses_configured_database_url() -> None:
    from app.db.session import create_engine

    settings = Settings(
        DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/buguard"
    )

    engine = create_engine(settings)

    try:
        assert isinstance(engine, AsyncEngine)
        assert str(engine.url).startswith("postgresql+asyncpg://")
    finally:
        await engine.dispose()



# Smoke test to confirm the database reachability helper exists.
# This does not call the database; it only verifies the helper is available.
def test_database_reachability_smoke_helper_is_documented() -> None:
    from app.db.session import check_database_reachability

    assert callable(check_database_reachability)


# Verify that an async session factory can be created from the async engine.
@pytest.mark.asyncio
async def test_async_sessionmaker_can_be_configured() -> None:
    from app.db.session import create_engine

    settings = Settings(
        DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/buguard"
    )
    engine = create_engine(settings)

    try:
        session_factory = async_sessionmaker(engine, expire_on_commit=False)

        assert session_factory.kw["expire_on_commit"] is False
    finally:
        await engine.dispose()
