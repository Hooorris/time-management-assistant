import os
import sys
import uuid
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = PROJECT_ROOT / "backend"
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

TEST_PREFIX = "__test_time_assistant__"


@pytest.fixture(scope="session")
def database_url() -> str:
    url = os.getenv("DATABASE_URL", "")
    if not url:
        pytest.skip("DATABASE_URL is required for integration tests.")
    return url


@pytest.fixture()
def db_session(database_url: str):
    engine = create_engine(database_url, pool_pre_ping=True)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()
        with engine.begin() as connection:
            connection.execute(
                text("DELETE FROM tasks WHERE title LIKE :pattern"),
                {"pattern": f"{TEST_PREFIX}%"},
            )
        engine.dispose()


@pytest.fixture()
def unique_title() -> str:
    return f"{TEST_PREFIX}{uuid.uuid4()}"
