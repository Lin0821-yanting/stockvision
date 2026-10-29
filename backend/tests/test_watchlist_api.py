"""自選股：新增、重複、刪除、資料保存在資料庫，並附上報價。"""

import pytest

from app.models.watchlist import WatchlistItem
from app.services.cache import cache
from tests.factories import mis_item, tw_price_rows, us_price_rows


@pytest.fixture
def client(auth_client):
    """這個檔案的 API 都需要登入：預設使用已登入的 client。"""
    return auth_client


@pytest.fixture
def market_data(upstream):
    upstream.finmind[("TaiwanStockPrice", "2330")] = tw_price_rows("2330", [2400.0] * 25)
    upstream.finmind[("USStockPrice", "AAPL")] = us_price_rows("AAPL", [340.0, 343.83])
    upstream.mis_items["2330"] = mis_item("2330", "台積電", z="2415.0000", y="2425.0000")
    return upstream


def test_add_list_and_remove_watchlist(client, db, market_data):
    created = client.post("/api/watchlist", json={"symbol": "2330"})
    client.post("/api/watchlist", json={"symbol": "aapl"})

    assert created.status_code == 201
    assert created.json()["name"] == "台積電"
    assert db.query(WatchlistItem).count() == 2

    items = client.get("/api/watchlist").json()["items"]
    assert [item["symbol"] for item in items] == ["2330", "AAPL"]
    assert items[0]["quote"]["source"] == "TWSE MIS"
    assert items[1]["quote"]["source"] == "FinMind USStockPrice"

    removed = client.delete("/api/watchlist/2330")
    assert removed.status_code == 204
    assert [item["symbol"] for item in client.get("/api/watchlist").json()["items"]] == ["AAPL"]


def test_duplicate_watchlist_item_returns_409(client, market_data):
    client.post("/api/watchlist", json={"symbol": "2330"})

    response = client.post("/api/watchlist", json={"symbol": "2330.TW"})

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "CONFLICT"


def test_unknown_symbol_cannot_be_added(client, market_data):
    response = client.post("/api/watchlist", json={"symbol": "9999"})

    assert response.status_code == 404


def test_remove_missing_item_returns_404(client, market_data):
    response = client.delete("/api/watchlist/2317")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


def test_watchlist_keeps_items_when_quote_fails(client, market_data):
    client.post("/api/watchlist", json={"symbol": "2330"})
    market_data.mis_items.clear()
    market_data.finmind[("TaiwanStockPrice", "2330")] = []  # 沒有任何價格資料
    cache.clear()

    item = client.get("/api/watchlist").json()["items"][0]

    assert item["quote"] is None
    assert item["quote_error"]["code"] == "SYMBOL_NOT_FOUND"
