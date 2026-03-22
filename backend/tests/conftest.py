import os
import sys
import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

BACKEND_DIR = Path(__file__).resolve().parent.parent
TEST_DB_FILE = Path(tempfile.gettempdir()) / "autoviral_test.db"

sys.path.insert(0, str(BACKEND_DIR))

# Ensure app/database modules initialize against test DB.
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_FILE}"

import app as app_module  # noqa: E402
from app import app  # noqa: E402
from core.database import Base, get_db  # noqa: E402


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    if TEST_DB_FILE.exists():
        TEST_DB_FILE.unlink()

    test_engine = create_engine(
        f"sqlite:///{TEST_DB_FILE}",
        connect_args={"check_same_thread": False},
        future=True,
    )
    testing_session_local = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_engine,
        class_=Session,
    )

    Base.metadata.create_all(bind=test_engine)

    def override_get_db() -> Generator[Session, None, None]:
        db = testing_session_local()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    original_init_db = app_module.init_db
    app_module.init_db = lambda: None

    with TestClient(app) as test_client:
        yield test_client

    app_module.init_db = original_init_db
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=test_engine)
    test_engine.dispose()
    if TEST_DB_FILE.exists():
        TEST_DB_FILE.unlink()
