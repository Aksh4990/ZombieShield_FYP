import os
import sys
from pathlib import Path

os.environ["DATABASE_URL"] = "sqlite+pysqlite:///./test_zombieshield.db"

ROOT = Path(__file__).resolve().parents[1]
os.environ["DISCOVERY_GIT_ROOT"] = str(ROOT / "tests" / "fixtures")
sys.path.insert(0, str(ROOT / "backend"))

import pytest
from fastapi.testclient import TestClient

from app.db.base import Base
from app.db.session import engine
from app.main import app


@pytest.fixture(autouse=True)
def reset_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client
