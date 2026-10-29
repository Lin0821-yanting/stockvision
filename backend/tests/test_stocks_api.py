"""股票查詢 API：搜尋、報價合併（盤中／收盤／備援）、歷史資料與錯誤回應。"""

from datetime import UTC, datetime

import httpx
import pytest

from app.core.config import get_settings
from tests.factories import mis_item, tw_price_rows, us_price_rows

TW_CLOSES = [2400.0 + (i % 7) * 10 for i in range(45)]


@pytest.fixture
def market_data(upstream):
    upstream.finmind[("TaiwanStockPrice", "2330")] = tw_price_rows("2330", TW_CLOSES)
    upstream.finmind[("TaiwanStockPrice", "2317")] = tw_price_rows("2317", [250.0] * 30)
    upstream.finmind[("USStockPrice", "AAPL")] = us_price_rows("AAPL", [340.0, 345.0, 343.83])
    upstream.mis_items["2330"] = mis_item("2330", "台積電", z="2415.0000", y="2425.0000", v="16828")
    upstream.mis_items["2317"] = mis_item("2317", "鴻海", z="248.0000", y="251.5000")
    return upstream


def test_search_by_code_name_and_english(client, market_data):
    by_code = client.get("/api/stocks/search", params={"q": "2330"}).json()
    by_name = client.get("/api/stocks/search", params={"q": "鴻海"}).json()
    by_english = client.get("/api/stocks/search", params={"q": "apple"}).json()

    assert by_code["results"][0] == {
        "symbol": "2330", "market": "TW", "name": "台積電", "exchange": "TWSE", "industry": "半導體業", "currency": "TWD",
    }
    assert [r["symbol"] for r in by_name["results"]] == ["2317"]
    assert by_english["results"][0]["symbol"] == "AAPL"


def test_search_uses_cached_catalog(client, market_data):
    client.get("/api/stocks/search", params={"q": "2330"})
    client.get("/api/stocks/search", params={"q": "台積"})

    info_calls = [call for call in market_data.finmind_calls if call[0].endswith("StockInfo")]
    assert sorted(info_calls) == [("TaiwanStockInfo", None), ("USStockInfo", None)]


def test_search_reports_partial_failure(client, market_data):
    market_data.finmind[("USStockInfo", None)] = httpx.Response(500)

    body = client.get("/api/stocks/search", params={"q": "2330"}).json()

    assert body["results"][0]["symbol"] == "2330"
    assert "美股清單暫時無法取得" in body["warnings"][0]


def test_stock_detail_uses_realtime_mis_quote(client, market_data):
    body = client.get("/api/stocks/2330").json()
    quote = body["quote"]

    assert quote["kind"] == "realtime"
    assert quote["source"] == "TWSE MIS"
    assert quote["price"] == 2415.0
    assert quote["change"] == -10.0
    assert quote["change_pct"] == pytest.approx(-0.4124)
    assert quote["volume"] == 16_828_000
    assert quote["as_of"].startswith("2026-10-29T10:15:30")
    assert body["low_20d"] == 2400.0
    assert body["is_20d_low"] is False


def test_quote_after_close_is_labelled_close(client, market_data, set_now):
    set_now(datetime(2026, 10, 29, 8, 0, tzinfo=UTC))  # 台北 16:00，已收盤

    quote = client.get("/api/stocks/2330").json()["quote"]

    assert quote["kind"] == "close"
    assert quote["note"] == "今日收盤（TWSE MIS）"


def test_no_trade_yet_falls_back_to_previous_close(client, market_data):
    market_data.mis_items["2330"] = mis_item("2330", "台積電", z="-", y="2425.0000")

    quote = client.get("/api/stocks/2330").json()["quote"]

    assert quote["kind"] == "close"
    assert quote["source"] == "FinMind TaiwanStockPrice"
    assert quote["price"] == TW_CLOSES[-1]
    assert quote["note"] == "今日尚無成交，顯示前一交易日收盤"


def test_official_openapi_is_last_fallback(client, market_data):
    market_data.mis_response = httpx.Response(503)
    market_data.finmind[("TaiwanStockPrice", "2330")] = httpx.Response(
        402, json={"msg": "Requests reach the upper limit.", "status": 402}
    )
    market_data.twse_day_all = [
        {"Date": "1151028", "Code": "2330", "Name": "台積電", "TradeVolume": "21866835", "OpeningPrice": "2420.00",
         "HighestPrice": "2430.00", "LowestPrice": "2400.00", "ClosingPrice": "2425.00", "Change": "25.0000"},
    ]

    quote = client.get("/api/stocks/2330").json()["quote"]

    assert quote["source"] == "TWSE OpenAPI STOCK_DAY_ALL"
    assert quote["price"] == 2425.0
    assert quote["prev_close"] == 2400.0
    assert quote["trade_date"] == "2026-10-28"


def test_us_stock_without_finnhub_key_uses_daily_close(client, market_data):
    quote = client.get("/api/stocks/AAPL").json()["quote"]

    assert quote["kind"] == "close"
    assert quote["source"] == "FinMind USStockPrice"
    assert quote["price"] == 343.83
    assert "未設定 Finnhub API Key" in quote["note"]


def test_us_stock_with_finnhub_key_is_realtime(client, market_data, set_now, monkeypatch):
    monkeypatch.setattr(get_settings(), "finnhub_api_key", "test-key")
    set_now(datetime(2026, 10, 29, 14, 30, tzinfo=UTC))  # 紐約 10:30 盤中
    market_data.finnhub["AAPL"] = {"c": 344.5, "d": 0.67, "dp": 0.1949, "h": 345.0, "l": 343.0, "o": 343.9,
                                   "pc": 343.83, "t": int(datetime(2026, 10, 29, 14, 29, tzinfo=UTC).timestamp())}

    quote = client.get("/api/stocks/AAPL").json()["quote"]

    assert quote["kind"] == "realtime"
    assert quote["source"] == "Finnhub"
    assert quote["price"] == 344.5
    assert "不含成交量" in quote["volume_note"]


def test_history_returns_sorted_bars_and_stats(client, market_data):
    body = client.get("/api/stocks/2330/history", params={"period": "1M"}).json()

    dates = [bar["date"] for bar in body["bars"]]
    assert dates == sorted(dates)
    assert body["source"] == "FinMind TaiwanStockPrice"
    assert "非即時" in body["data_note"]
    assert body["stats"]["trading_days"] == len(body["bars"])
    expected = (body["bars"][-1]["close"] / body["bars"][0]["close"] - 1) * 100
    assert body["stats"]["period_return_pct"] == pytest.approx(expected, abs=0.01)


def test_quotes_batch_reports_errors_per_symbol(client, market_data):
    body = client.get("/api/stocks/quotes", params={"symbols": "2330,2317,9999"}).json()

    assert [q["symbol"] for q in body["quotes"]] == ["2330", "2317"]
    assert body["errors"] == [{"symbol": "9999", "market": None, "code": "SYMBOL_NOT_FOUND", "message": "找不到股票代號 9999"}]
    assert len(market_data.mis_calls) == 1  # 兩檔台股合併成一次 MIS 請求


def test_usd_twd_uses_latest_valid_mid_rate(client, market_data):
    body = client.get("/api/fx/usd-twd").json()

    assert body["rate_date"] == "2026-10-29"
    assert body["rate"] == 32.49


def test_market_status(client):
    markets = {m["market"]: m for m in client.get("/api/market/status").json()["markets"]}

    assert markets["TW"]["is_open"] is True
    assert markets["US"]["is_open"] is False
    assert markets["US"]["session_taipei"] == "21:30–04:00"


# ---------------------------------------------------------------- 錯誤回應


def test_unknown_symbol_returns_404(client, market_data):
    response = client.get("/api/stocks/9999")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "SYMBOL_NOT_FOUND"


def test_invalid_period_returns_422(client, market_data):
    response = client.get("/api/stocks/2330/history", params={"period": "2W"})

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_finmind_rate_limit_returns_503(client, market_data):
    market_data.finmind[("TaiwanStockPrice", "2330")] = httpx.Response(
        402, json={"msg": "Requests reach the upper limit.", "status": 402}
    )

    response = client.get("/api/stocks/2330/history")

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "UPSTREAM_RATE_LIMITED"


def test_upstream_timeout_returns_503(client, market_data):
    market_data.finmind[("TaiwanStockInfo", None)] = httpx.Response(504)

    response = client.get("/api/stocks/search", params={"q": "2330", "market": "TW"})

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "UPSTREAM_UNAVAILABLE"


def test_too_many_symbols_returns_400(client):
    symbols = ",".join(str(1000 + i) for i in range(31))

    response = client.get("/api/stocks/quotes", params={"symbols": symbols})

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_REQUEST"
