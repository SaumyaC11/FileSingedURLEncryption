"""Fixtures for tests that hit the real (DigitalOcean-managed) Postgres instance
configured via DATABASE_URL.

Every test gets its own DB session bound to a connection-level transaction that
is rolled back on teardown, so tests never leave rows behind and can run
against the same shared dev database without interfering with each other.
"""

import socket
from urllib.parse import urlparse

import pytest
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings
from app.database import Base


def _database_reachable(database_url: str) -> bool:
    parsed = urlparse(database_url)
    if not parsed.hostname:
        return False
    try:
        with socket.create_connection((parsed.hostname, parsed.port or 5432), timeout=5):
            return True
    except OSError:
        return False


@pytest.fixture(scope="session")
def integration_engine() -> Engine:
    database_url = get_settings().database_url
    if not _database_reachable(database_url):
        pytest.skip("Postgres integration database is not reachable from this environment")

    engine = create_engine(database_url, future=True)
    Base.metadata.create_all(bind=engine)
    yield engine
    engine.dispose()


@pytest.fixture
def db_session(integration_engine: Engine) -> Session:
    """A session scoped to a transaction that is always rolled back.

    Repositories call `session.commit()` internally; `join_transaction_mode
    ="create_savepoint"` makes those commits release a SAVEPOINT instead of
    the outer transaction, so the final rollback still undoes everything.
    """
    connection = integration_engine.connect()
    transaction = connection.begin()
    session_factory = sessionmaker(
        bind=connection,
        autoflush=False,
        autocommit=False,
        future=True,
        join_transaction_mode="create_savepoint",
    )
    session = session_factory()

    yield session

    session.close()
    transaction.rollback()
    connection.close()
