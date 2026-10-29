"""測試共用設定。

在匯入 app 之前先把環境變數指到記憶體資料庫並關閉排程，
所以測試不會碰到開發用的 SQLite 檔案，也不受本機 .env 影響。
所有外部股票 API 都用 respx 模擬（upstream fixture），測試結果不依賴網路。
"""

from __future__ import annotations

import os

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["ALERT_SCHEDULER_ENABLED"] = "false"
os.environ["FINMIND_TOKEN"] = ""
os.environ["FINNHUB_API_KEY"] = ""

from datetime import datetime  # noqa: E402
from typing import Any  # noqa: E402

import httpx  # noqa: E402
import pytest  # noqa: E402
import respx  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.core import clock, security  # noqa: E402
from app.core.market_hours import TAIPEI  # noqa: E402
from app.database.session import Base, SessionLocal, engine, init_db  # noqa: E402
from app.main import app  # noqa: E402
from app.services import auth_service, quote_service  # noqa: E402
from app.services.cache import cache  # noqa: E402
from app.services.providers import http  # noqa: E402

from tests import factories  # noqa: E402

# 預設時間：2026-10-29（週四）10:15 台北時間，台股盤中、美股休市
DEFAULT_NOW = datetime(2026, 10, 29, 10, 15, 30, tzinfo=TAIPEI)


@pytest.fixture(autouse=True)
def fresh_state(monkeypatch):
    Base.metadata.drop_all(bind=engine)
    init_db()
    cache.clear()
    quote_service.reset_state()
    auth_service.throttle.reset()
    monkeypatch.setattr(http, "RETRY_BACKOFF_SECONDS", 0)
    monkeypatch.setattr(quote_service, "MIS_MIN_INTERVAL_SECONDS", 0)
    monkeypatch.setattr(security, "SCRYPT_N", 2**10)  # 測試用較低的雜湊成本；格式與驗證流程完全相同
    monkeypatch.setattr(clock, "now", lambda: DEFAULT_NOW)
    yield


@pytest.fixture
def set_now(monkeypatch):
    def _set(value: datetime) -> None:
        monkeypatch.setattr(clock, "now", lambda: value)

    return _set


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client():
    """未登入的 client。"""
    with TestClient(app) as test_client:
        yield test_client


PASSWORD = "correct-horse-42"


def register(test_client: TestClient, username: str = "alice", password: str = PASSWORD):
    response = test_client.post(
        "/api/auth/register",
        json={"username": username, "password": password, "display_name": username.title()},
    )
    assert response.status_code == 201, response.text
    return response


@pytest.fixture
def auth_client():
    """已註冊並登入為 alice 的 client（cookie 保存在 TestClient 內）。"""
    with TestClient(app) as test_client:
        register(test_client)
        yield test_client


@pytest.fixture
def make_client():
    """建立多個各自獨立 cookie 的 client，用來測試不同使用者之間的資料隔離。"""
    opened: list[TestClient] = []

    def _make(username: str | None = None) -> TestClient:
        test_client = TestClient(app)
        test_client.__enter__()
        opened.append(test_client)
        if username:
            register(test_client, username)
        return test_client

    yield _make
    for test_client in opened:
        test_client.__exit__(None, None, None)


class FakeUpstream:
    """模擬 FinMind、TWSE MIS、TWSE/TPEx OpenAPI 與 Finnhub。

    finmind[(dataset, data_id)] 可以放資料列（list）或 httpx.Response（模擬錯誤）。
    """

    def __init__(self, router: respx.Router) -> None:
        self.finmind: dict[tuple[str, str | None], Any] = {
            ("TaiwanStockInfo", None): factories.tw_info_rows(),
            ("USStockInfo", None): factories.us_info_rows(),
            ("TaiwanExchangeRate", "USD"): factories.usd_rate_rows(),
        }
        self.finmind_calls: list[tuple[str, str | None]] = []
        self.mis_items: dict[str, dict[str, Any]] = {}
        self.mis_response: httpx.Response | None = None
        self.mis_calls: list[str] = []
        self.twse_day_all: list[dict[str, Any]] = []
        self.twse_companies: list[dict[str, Any]] = []
        self.tpex_daily: list[dict[str, Any]] = []
        self.finnhub: dict[str, dict[str, Any]] = {}
        self.finnhub_calls: list[str] = []

        router.route(host="api.finmindtrade.com", path="/api/v4/data").mock(side_effect=self._finmind)
        router.route(host="mis.twse.com.tw").mock(side_effect=self._mis)
        router.route(host="openapi.twse.com.tw", path="/v1/opendata/t187ap03_L").mock(
            side_effect=lambda _: httpx.Response(200, json=self.twse_companies)
        )
        router.route(host="openapi.twse.com.tw").mock(side_effect=lambda _: httpx.Response(200, json=self.twse_day_all))
        router.route(host="www.tpex.org.tw").mock(side_effect=lambda _: httpx.Response(200, json=self.tpex_daily))
        router.route(host="finnhub.io").mock(side_effect=self._finnhub)

    def _finmind(self, request: httpx.Request) -> httpx.Response:
        dataset = request.url.params.get("dataset")
        data_id = request.url.params.get("data_id")
        self.finmind_calls.append((dataset, data_id))
        value = self.finmind.get((dataset, data_id), self.finmind.get((dataset, None), []))
        if isinstance(value, httpx.Response):
            return value
        return httpx.Response(200, json={"msg": "success", "status": 200, "data": value})

    def _mis(self, request: httpx.Request) -> httpx.Response:
        ex_ch = request.url.params.get("ex_ch", "")
        self.mis_calls.append(ex_ch)
        if self.mis_response is not None:
            return self.mis_response
        codes = [part.split("_", 1)[1].removesuffix(".tw") for part in ex_ch.split("|") if "_" in part]
        items = [self.mis_items[code] for code in codes if code in self.mis_items]
        return httpx.Response(200, json={"msgArray": items, "rtcode": "0000", "rtmessage": "OK"})

    def _finnhub(self, request: httpx.Request) -> httpx.Response:
        empty = {"c": 0, "d": None, "dp": None, "h": 0, "l": 0, "o": 0, "pc": 0, "t": 0}
        symbol = request.url.params.get("symbol")
        self.finnhub_calls.append(symbol)
        return httpx.Response(200, json=self.finnhub.get(symbol, empty))


@pytest.fixture
def upstream():
    with respx.mock(assert_all_called=False) as router:
        yield FakeUpstream(router)
