from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import get_settings
from app.core.database import get_db
from app.core.dependencies import get_activity_dispatcher
from app.core.rate_limit import limiter
from app.main import app
from tests.fixtures.fakes import FakeActivityDispatcher

_settings = get_settings()
_test_engine = create_async_engine(_settings.database_url, poolclass=NullPool)


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """A session bound to a single connection whose outer transaction is
    always rolled back, so each test sees a clean database regardless of
    whether the code under test calls session.commit()."""
    async with _test_engine.connect() as connection:
        await connection.begin()
        async with AsyncSession(
            bind=connection, expire_on_commit=False, join_transaction_mode="create_savepoint"
        ) as session:
            yield session
        await connection.rollback()


@pytest.fixture
async def activity_dispatcher() -> FakeActivityDispatcher:
    """Exposed so tests can assert on dispatched activity events; also
    keeps HTTP-level tests from touching a real Celery broker."""
    return FakeActivityDispatcher()


@pytest.fixture
async def client(
    db_session: AsyncSession, activity_dispatcher: FakeActivityDispatcher
) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    def override_get_activity_dispatcher() -> FakeActivityDispatcher:
        return activity_dispatcher

    # The rate limiter is a process-wide singleton; reset it so calls made
    # by earlier tests never leak into this one's quota.
    limiter.reset()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_activity_dispatcher] = override_get_activity_dispatcher
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        yield async_client
    app.dependency_overrides.clear()
