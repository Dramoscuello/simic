import os
import subprocess
from pathlib import Path
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

BACKEND_DIR = Path(__file__).resolve().parents[1]

os.environ.setdefault("DATABASE_URL", "postgresql://postgres:postgres@localhost:54329/icfes_test")
os.environ.setdefault("REDIS_URL", "redis://localhost:6389/0")
os.environ.setdefault("APP_BOOTSTRAP_ON_STARTUP", "false")
os.environ.setdefault("SECRET_KEY", "test_secret_key")

from app.database.config import get_db  # noqa: E402
from app.main import create_app  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def migrated_database() -> Generator[None, None, None]:
    env = os.environ.copy()
    subprocess.run(["alembic", "upgrade", "head"], cwd=str(BACKEND_DIR), env=env, check=True)
    yield


@pytest.fixture(scope="session")
def test_engine() -> Generator[Engine, None, None]:
    engine = create_engine(os.environ["DATABASE_URL"])
    try:
        yield engine
    finally:
        engine.dispose()


@pytest.fixture(scope="function")
def db_session(test_engine: Engine) -> Generator[Session, None, None]:
    connection = test_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    session.begin_nested()

    def _restart_savepoint(sess: Session, trans) -> None:
        parent = getattr(trans, "_parent", None)
        if trans.nested and parent is not None and not parent.nested:
            sess.begin_nested()

    event.listen(session, "after_transaction_end", _restart_savepoint)
    try:
        yield session
    finally:
        event.remove(session, "after_transaction_end", _restart_savepoint)
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture(scope="function")
def app(db_session: Session):
    application = create_app()

    def _override_get_db():
        yield db_session

    application.dependency_overrides[get_db] = _override_get_db
    yield application
    application.dependency_overrides.clear()


@pytest.fixture(scope="function")
def client(app) -> Generator[TestClient, None, None]:
    with TestClient(app) as test_client:
        yield test_client
