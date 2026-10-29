"""多使用者資料隔離：自選股、模擬帳戶、交易、提醒與通知彼此看不到。"""

import pytest

from app.services.cache import cache
from tests.factories import mis_item, tw_price_rows


@pytest.fixture
def market_data(upstream):
    upstream.finmind[("TaiwanStockPrice", "2330")] = tw_price_rows("2330", [2400.0] * 25)
    upstream.mis_items["2330"] = mis_item("2330", "台積電", z="2415.0000", y="2425.0000")
    return upstream


def set_price(upstream, price: str) -> None:
    upstream.mis_items["2330"] = mis_item("2330", "台積電", z=price, y="2425.0000")
    cache.clear()


def test_watchlists_accounts_and_trades_are_separate(make_client, market_data):
    alice, bob = make_client("alice"), make_client("bob")

    assert alice.post("/api/watchlist", json={"symbol": "2330"}).status_code == 201
    assert bob.post("/api/watchlist", json={"symbol": "2330"}).status_code == 201  # 同一檔股票可以各自加入
    alice.post("/api/trades", json={"symbol": "2330", "side": "BUY", "shares": 100})
    bob.post("/api/account/reset")

    assert len(alice.get("/api/watchlist").json()["items"]) == 1
    assert alice.get("/api/account").json()["cash"] == 758_500
    assert [t["symbol"] for t in alice.get("/api/trades").json()["trades"]] == ["2330"]
    assert bob.get("/api/account").json()["cash"] == 1_000_000
    assert bob.get("/api/portfolio").json()["positions"] == []
    assert bob.get("/api/trades").json()["trades"] == []


def test_alerts_and_notifications_are_private(make_client, market_data):
    alice, bob = make_client("alice"), make_client("bob")
    created = alice.post("/api/alerts", json={"symbol": "2330", "condition": "PRICE_LTE", "target_price": 2500}).json()
    alert_id = created["alert"]["id"]
    event_id = created["triggered"][0]["id"]

    assert alice.get("/api/notifications").json()["unread_count"] == 1
    assert bob.get("/api/notifications").json() == {"items": [], "unread_count": 0}
    assert bob.get("/api/alerts").json()["alerts"] == []
    assert bob.patch(f"/api/alerts/{alert_id}", json={"is_active": False}).status_code == 404
    assert bob.delete(f"/api/alerts/{alert_id}").status_code == 404
    assert bob.post(f"/api/notifications/{event_id}/read").status_code == 404
    assert bob.post("/api/notifications/read-all").json()["updated"] == 0
    assert alice.get("/api/notifications").json()["unread_count"] == 1


def test_quote_triggered_alerts_reach_only_their_owner(make_client, client, market_data):
    alice, bob = make_client("alice"), make_client("bob")
    alice.post(
        "/api/alerts",
        json={"symbol": "2330", "condition": "PRICE_LTE", "target_price": 2400, "trigger_mode": "EVERY_CROSS"},
    )
    set_price(market_data, "2390.0000")

    seen_by_bob = bob.get("/api/stocks/2330").json()["triggered_alerts"]

    assert seen_by_bob == []  # 伺服器端照樣檢查了 alice 的提醒，但不會回傳給 bob
    assert alice.get("/api/notifications").json()["unread_count"] == 1
    set_price(market_data, "2410.0000")
    client.get("/api/stocks/2330")  # 未登入的訪客取得行情也會更新提醒狀態
    set_price(market_data, "2380.0000")
    assert len(alice.get("/api/stocks/2330").json()["triggered_alerts"]) == 1
