"""價格提醒 API：建立即檢查、取得行情時同步檢查、不重複通知、停用、編輯、刪除、通知已讀與排程。"""

import asyncio
from datetime import UTC, datetime

import pytest

from app.models.alert import AlertEvent
from app.services.cache import cache
from app.services.scheduler import monitor
from tests.factories import mis_item, tw_price_rows

CLOSES = [2500.0 - i * 5 for i in range(25)]  # 前 20 日最低收盤 2380


@pytest.fixture
def market_data(upstream):
    upstream.finmind[("TaiwanStockPrice", "2330")] = tw_price_rows("2330", CLOSES)
    set_price(upstream, "2415.0000")
    return upstream


def set_price(upstream, price: str) -> None:
    upstream.mis_items["2330"] = mis_item("2330", "台積電", z=price, y="2425.0000")
    cache.clear()


def create(client, **payload):
    return client.post("/api/alerts", json={"symbol": "2330", **payload})


def test_create_alert_that_is_not_met_keeps_monitoring(client, market_data):
    response = create(client, condition="PRICE_LTE", target_price=900)

    assert response.status_code == 201
    body = response.json()
    assert body["triggered"] == []
    assert body["alert"]["status"] == "monitoring"
    assert body["alert"]["last_checked_price"] == 2415.0
    assert body["alert"]["condition_label"] == "價格 ≤ 900.00 TWD"


def test_alert_already_met_triggers_immediately_and_once_mode_disables(client, market_data):
    body = create(client, condition="PRICE_LTE", target_price=2500).json()

    assert len(body["triggered"]) == 1
    assert "最新價格 2,415.00 TWD" in body["triggered"][0]["message"]
    assert body["alert"]["status"] == "triggered"
    assert body["alert"]["is_active"] is False


def test_quote_request_checks_alerts_without_duplicates(client, db, market_data):
    create(client, condition="PRICE_LTE", target_price=2400, trigger_mode="EVERY_CROSS")

    set_price(market_data, "2398.0000")
    first = client.get("/api/stocks/2330").json()["triggered_alerts"]
    set_price(market_data, "2395.0000")
    second = client.get("/api/stocks/quotes", params={"symbols": "2330"}).json()["triggered_alerts"]

    assert len(first) == 1 and first[0]["triggered_price"] == 2398.0
    assert second == []  # 條件一直成立，不重複通知
    assert db.query(AlertEvent).count() == 1


def test_every_cross_alert_triggers_again_after_recovering(client, market_data):
    create(client, condition="PRICE_LTE", target_price=2400, trigger_mode="EVERY_CROSS")

    for price in ("2390.0000", "2410.0000", "2399.0000"):
        set_price(market_data, price)
        client.get("/api/stocks/2330")

    events = client.get("/api/alerts/events").json()
    assert [event["triggered_price"] for event in events] == [2399.0, 2390.0]


def test_disabled_alert_is_not_checked(client, market_data):
    alert_id = create(client, condition="PRICE_LTE", target_price=2400).json()["alert"]["id"]
    client.patch(f"/api/alerts/{alert_id}", json={"is_active": False})

    set_price(market_data, "2300.0000")
    triggered = client.get("/api/stocks/2330").json()["triggered_alerts"]

    assert triggered == []
    assert client.get("/api/alerts").json()["alerts"][0]["status"] == "disabled"


def test_editing_target_rechecks_immediately(client, market_data):
    alert_id = create(client, condition="PRICE_GTE", target_price=3000).json()["alert"]["id"]

    body = client.patch(f"/api/alerts/{alert_id}", json={"target_price": 2400}).json()

    assert body["alert"]["target_price"] == 2400.0
    assert len(body["triggered"]) == 1


def test_twenty_day_low_alert(client, market_data):
    body = create(client, condition="NEW_20D_LOW").json()
    assert body["triggered"] == []  # 2415 高於前 20 日最低收盤 2380

    set_price(market_data, "2370.0000")
    triggered = client.get("/api/stocks/2330").json()["triggered_alerts"]

    assert len(triggered) == 1
    assert triggered[0]["reference_low"] == 2380.0
    assert "創 20 日新低" in triggered[0]["message"]


def test_delete_alert_keeps_trigger_history(client, market_data):
    alert_id = create(client, condition="PRICE_LTE", target_price=2500).json()["alert"]["id"]

    assert client.delete(f"/api/alerts/{alert_id}").status_code == 204
    assert client.get("/api/alerts").json()["alerts"] == []
    events = client.get("/api/alerts/events").json()
    assert len(events) == 1 and events[0]["alert_id"] is None


def test_notifications_unread_and_read_all(client, market_data):
    create(client, condition="PRICE_LTE", target_price=2500)
    create(client, condition="PRICE_GTE", target_price=2000)

    unread = client.get("/api/notifications", params={"unread_only": True}).json()
    first_id = unread["items"][0]["id"]
    client.post(f"/api/notifications/{first_id}/read")
    after_one = client.get("/api/notifications").json()["unread_count"]
    client.post("/api/notifications/read-all")

    assert unread["unread_count"] == 2
    assert after_one == 1
    assert client.get("/api/notifications").json()["unread_count"] == 0


def test_manual_check_endpoint(client, market_data):
    create(client, condition="PRICE_LTE", target_price=2400, trigger_mode="EVERY_CROSS")
    set_price(market_data, "2350.0000")

    body = client.post("/api/alerts/check").json()

    assert body["checked_alerts"] == 1
    assert len(body["triggered"]) == 1


def test_price_alert_requires_target(client, market_data):
    response = create(client, condition="PRICE_LTE")

    assert response.status_code == 422


def test_unknown_alert_returns_404(client):
    assert client.patch("/api/alerts/999", json={"is_active": False}).status_code == 404
    assert client.post("/api/notifications/999/read").status_code == 404


def test_scheduler_skips_closed_markets_and_checks_open_ones(client, market_data, set_now):
    create(client, condition="PRICE_LTE", target_price=2400, trigger_mode="EVERY_CROSS")
    set_price(market_data, "2350.0000")

    set_now(datetime(2026, 10, 31, 2, 0, tzinfo=UTC))  # 週六
    asyncio.run(monitor.run_once())
    skipped = monitor.last_result

    set_now(datetime(2026, 10, 29, 2, 30, tzinfo=UTC))  # 週四 10:30 台北盤中
    asyncio.run(monitor.run_once())

    assert "略過" in skipped
    assert "觸發 1 個" in monitor.last_result
    assert client.get("/api/notifications").json()["unread_count"] == 1


def test_monitor_status_explains_limits(client):
    status = client.get("/api/alerts/monitor").json()

    assert status["enabled"] is False  # 測試環境關閉排程
    assert "無法監控價格" in status["explanation"]
