"""模擬交易 API：下單、資金/持股檢查、投資組合、交易紀錄、重置與資料庫一致性。"""

from decimal import Decimal

import pytest

from app.models.account import Account, Position, Trade
from app.services.cache import cache
from tests.factories import mis_item, tw_price_rows, us_price_rows


@pytest.fixture
def market_data(upstream):
    upstream.finmind[("TaiwanStockPrice", "2330")] = tw_price_rows("2330", [2400.0] * 25)
    upstream.finmind[("TaiwanStockPrice", "2317")] = tw_price_rows("2317", [250.0] * 25)
    upstream.finmind[("USStockPrice", "AAPL")] = us_price_rows("AAPL", [340.0, 343.83])
    upstream.mis_items["2330"] = mis_item("2330", "台積電", z="2415.0000", y="2425.0000")
    upstream.mis_items["2317"] = mis_item("2317", "鴻海", z="248.0000", y="251.5000")
    return upstream


def buy(client, symbol, shares):
    return client.post("/api/trades", json={"symbol": symbol, "side": "BUY", "shares": shares})


def sell(client, symbol, shares):
    return client.post("/api/trades", json={"symbol": symbol, "side": "SELL", "shares": shares})


def test_account_starts_with_one_million(client):
    body = client.get("/api/account").json()

    assert body["initial_cash"] == 1_000_000
    assert body["cash"] == 1_000_000
    assert body["cycle"] == 1


def test_buy_updates_cash_position_and_history(client, db, market_data):
    response = buy(client, "2330", 100)

    assert response.status_code == 201
    body = response.json()
    assert body["trade"]["price"] == 2415.0
    assert body["trade"]["price_source"] == "TWSE MIS"
    assert body["trade"]["amount_twd"] == 241_500.0
    assert body["account"]["cash"] == 758_500.0
    assert "模擬成交" in body["disclaimer"]

    position = db.query(Position).one()
    assert (position.symbol, position.shares, position.cost_basis_twd) == ("2330", 100, Decimal("241500.00"))
    assert db.query(Trade).count() == 1


def test_buy_with_insufficient_funds_changes_nothing(client, db, market_data):
    response = buy(client, "2330", 1000)  # 需要 NT$2,415,000

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INSUFFICIENT_FUNDS"
    assert db.get(Account, 1).cash == Decimal("1000000")
    assert db.query(Position).count() == 0
    assert db.query(Trade).count() == 0


def test_sell_more_than_held_is_rejected(client, market_data):
    buy(client, "2317", 1000)

    response = sell(client, "2317", 1001)

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INSUFFICIENT_SHARES"


def test_sell_without_position_is_rejected(client, market_data):
    response = sell(client, "2330", 1)

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INSUFFICIENT_SHARES"


def test_sell_realizes_pnl_and_closes_position(client, db, market_data):
    buy(client, "2317", 1000)  # 248 × 1000
    market_data.mis_items["2317"] = mis_item("2317", "鴻海", z="260.0000", y="251.5000")
    cache.clear()

    body = sell(client, "2317", 1000).json()

    assert body["trade"]["realized_pnl_twd"] == 12_000.0
    assert body["account"]["cash"] == 1_012_000.0
    assert db.query(Position).count() == 0


def test_preview_reports_problem_without_trading(client, db, market_data):
    ok = client.post("/api/trades/preview", json={"symbol": "2330", "side": "BUY", "shares": 10}).json()
    too_big = client.post("/api/trades/preview", json={"symbol": "2330", "side": "BUY", "shares": 1000}).json()

    assert ok["can_execute"] is True and ok["cash_after"] == 975_850.0 and ok["shares_after"] == 10
    assert too_big["can_execute"] is False and too_big["reason_code"] == "INSUFFICIENT_FUNDS"
    assert db.query(Trade).count() == 0


def test_us_stock_trade_uses_fx_rate(client, market_data):
    body = buy(client, "AAPL", 10).json()

    assert body["trade"]["currency"] == "USD"
    assert body["trade"]["fx_rate"] == 32.49
    assert body["trade"]["amount_twd"] == 111_710.37
    assert body["trade"]["price_kind"] == "close"


def test_portfolio_values_positions(client, market_data):
    buy(client, "2330", 100)
    buy(client, "AAPL", 10)

    body = client.get("/api/portfolio").json()

    assert body["cash_twd"] == pytest.approx(1_000_000 - 241_500 - 111_710.37)
    assert body["market_value_twd"] == pytest.approx(241_500 + 111_710.37)
    assert body["unrealized_pnl_twd"] == 0
    assert body["total_assets_twd"] == pytest.approx(1_000_000)
    assert body["roi_pct"] == 0
    # 241,500 ÷ 353,210.37 = 68.3725%
    assert {p["symbol"]: p["weight_pct"] for p in body["positions"]} == {"2330": 68.37, "AAPL": 31.63}
    assert body["incomplete"] is False


def test_portfolio_flags_missing_prices(client, market_data):
    buy(client, "2330", 100)
    market_data.mis_items.clear()
    market_data.finmind[("TaiwanStockPrice", "2330")] = []
    cache.clear()

    body = client.get("/api/portfolio").json()

    assert body["incomplete"] is True
    assert body["positions"][0]["market_value_twd"] is None
    assert "未計入總市值" in body["warnings"][0]


def test_trade_history_and_reset_keeps_old_cycle(client, db, market_data):
    buy(client, "2330", 10)
    buy(client, "2317", 100)

    reset = client.post("/api/account/reset").json()
    current = client.get("/api/trades").json()
    everything = client.get("/api/trades", params={"scope": "all"}).json()

    assert reset["account"]["cash"] == 1_000_000 and reset["account"]["cycle"] == 2
    assert db.query(Position).count() == 0
    assert current["trades"] == [] and current["current_cycle"] == 2
    assert [t["symbol"] for t in everything["trades"]] == ["2317", "2330"]  # 新到舊


def test_invalid_trade_request_returns_422(client):
    response = client.post("/api/trades", json={"symbol": "2330", "side": "HOLD", "shares": -5})

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
