"""測試共用設定。

在匯入 app 之前先把環境變數指到記憶體資料庫並關閉排程，
所以測試不會碰到開發用的 SQLite 檔案，也不受本機 .env 影響。
"""

from __future__ import annotations

import os

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["ALERT_SCHEDULER_ENABLED"] = "false"
os.environ["FINMIND_TOKEN"] = ""
os.environ["FINNHUB_API_KEY"] = ""

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.database.session import Base, SessionLocal, engine, init_db  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(autouse=True)
def fresh_database():
    Base.metadata.drop_all(bind=engine)
    init_db()
    yield


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client
