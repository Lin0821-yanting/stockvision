"""外部 API 回應的解析、重試與錯誤轉換（全部使用 mock，不連網）。"""

import asyncio
from datetime import date, datetime
from decimal import Decimal

import httpx
import pytest
import respx

from app.core.errors import UpstreamError, UpstreamRateLimitedError
from app.core.market_hours import TAIPEI
from app.core.money import to_decimal
from app.core.symbols import parse_symbol
from app.services import catalog_service
from app.services.providers import finmind, finnhub, http, tpex_openapi, twse_mis, twse_openapi
from app.services.providers.base import parse_roc_date
from tests.factories import mis_item, tw_info_rows, us_info_rows


def test_to_decimal_handles_api_values():
    assert to_decimal("1,234.50") == Decimal("1234.50")
    assert to_decimal(0.1) + to_decimal(0.2) == Decimal("0.3")
    assert to_decimal("-0.17 ") == Decimal("-0.17")
    for empty in ("-", "--", "", None, float("nan"), "abc"):
        assert to_decimal(empty) is None


def test_parse_roc_date():
    assert parse_roc_date("1151028") == date(2026, 10, 28)
    assert parse_roc_date("115/10/28") == date(2026, 10, 28)
    assert parse_roc_date("1151332") is None
    assert parse_roc_date("") is None


def test_parse_symbol_detects_market():
    assert parse_symbol("2330").market == "TW"
    assert parse_symbol(" aapl ").symbol == "AAPL"
    assert parse_symbol("2330.TW").symbol == "2330"
    assert parse_symbol("BRK.B").market == "US"


def test_parse_twse_stock_day_all():
    payload = [
        {"Date": "1151028", "Code": "2330", "Name": "台積電", "TradeVolume": "21866835", "TradeValue": "1",
         "OpeningPrice": "2420.00", "HighestPrice": "2430.00", "LowestPrice": "2400.00", "ClosingPrice": "2425.00",
         "Change": "25.0000", "Transaction": "1"},
        {"Date": "1151028", "Code": "9999", "Name": "停牌", "TradeVolume": "0", "OpeningPrice": "",
         "HighestPrice": "", "LowestPrice": "", "ClosingPrice": "", "Change": "0.0000"},
    ]

    snapshots = twse_openapi.parse_stock_day_all(payload)

    assert snapshots["2330"].trade_date == date(2026, 10, 28)
    assert snapshots["2330"].close == Decimal("2425.00")
    assert snapshots["2330"].volume == 21866835
    assert snapshots["9999"].close is None


def test_parse_tpex_daily_close_with_trailing_spaces():
    payload = [{"Date": "1151029", "SecuritiesCompanyCode": "6488", "CompanyName": "環球晶", "Close": "814.00",
                "Change": "-35.00 ", "Open": "850.00", "High": "853.00", "Low": "803.00", "TradingShares": "7033000"}]

    snapshot = tpex_openapi.parse_daily_close(payload)["6488"]

    assert snapshot.change == Decimal("-35.00")
    assert snapshot.trade_date == date(2026, 10, 29)


def test_parse_mis_quote_converts_lots_to_shares():
    payload = {"msgArray": [mis_item("2330", "台積電", z="2415.0000", y="2425.0000", t="13:30:00", v="16828")]}

    quote = twse_mis.parse_mis_payload(payload)["2330"]

    assert quote.price == Decimal("2415.0000")
    assert quote.prev_close == Decimal("2425.0000")
    assert quote.volume == 16_828_000
    assert quote.trade_time == datetime(2026, 10, 29, 13, 30, tzinfo=TAIPEI)


def test_parse_mis_quote_without_trade():
    payload = {"msgArray": [
        mis_item("2330", "台積電", z="-", y="2425.0000"),
        mis_item("2317", "鴻海", z="-", y="251.5", trade={"t": "10:15:20", "v": 3, "z": "248.5000"}),
    ]}

    quotes = twse_mis.parse_mis_payload(payload)

    assert quotes["2330"].price is None  # 尚無成交，不能用其他價格冒充成交價
    assert quotes["2317"].price == Decimal("248.5000")


def test_parse_finnhub_quote():
    valid = finnhub.parse_quote("AAPL", {"c": 343.83, "d": -3.27, "dp": -0.94, "h": 347.18, "l": 343.53,
                                         "o": 346.89, "pc": 347.1, "t": 1793217601})
    unknown = finnhub.parse_quote("ZZZZ", {"c": 0, "d": None, "dp": None, "h": 0, "l": 0, "o": 0, "pc": 0, "t": 0})

    assert valid is not None and valid.price == Decimal("343.83")
    assert unknown is None


def test_catalog_parsing_dedupes_and_filters():
    tw = {entry.symbol: entry for entry in catalog_service.parse_taiwan_info(tw_info_rows())}
    us = {entry.symbol: entry for entry in catalog_service.parse_us_info(us_info_rows())}

    assert set(tw) == {"2330", "2317", "6488"}  # 指數與興櫃被排除
    assert tw["2330"].name == "台積電" and tw["6488"].exchange == "TPEx"
    assert tw["6488"].mis_channel == ("otc", "6488")
    assert set(us) == {"AAPL", "NVDA"}
    assert us["AAPL"].name == "Apple Inc."  # 取最新日期，並去掉 Common Stock


def test_finmind_rate_limit_is_reported():
    with respx.mock as router:
        router.route(host="api.finmindtrade.com").mock(
            return_value=httpx.Response(402, json={"msg": "Requests reach the upper limit.", "status": 402})
        )
        with pytest.raises(UpstreamRateLimitedError):
            asyncio.run(finmind.taiwan_stock_info())


def test_finmind_error_status_is_reported():
    with respx.mock as router:
        router.route(host="api.finmindtrade.com").mock(
            return_value=httpx.Response(200, json={"msg": "parameter error", "status": 400})
        )
        with pytest.raises(UpstreamError) as error:
            asyncio.run(finmind.taiwan_stock_info())
    assert "parameter error" in error.value.message


def test_http_retries_server_errors_then_fails():
    with respx.mock as router:
        route = router.route(host="example.test").mock(return_value=httpx.Response(500))
        with pytest.raises(UpstreamError) as error:
            asyncio.run(http.request_json("https://example.test/data", source="Example", retries=2))
    assert route.call_count == 3
    assert error.value.status_code == 503


def test_http_recovers_after_transient_timeout():
    with respx.mock as router:
        route = router.route(host="example.test").mock(
            side_effect=[httpx.ConnectTimeout("timeout"), httpx.Response(200, json={"ok": True})]
        )
        status, payload = asyncio.run(http.request_json("https://example.test/data", source="Example"))
    assert (status, payload) == (200, {"ok": True})
    assert route.call_count == 2


def test_http_invalid_json_is_upstream_error():
    with respx.mock as router:
        router.route(host="example.test").mock(return_value=httpx.Response(200, text="<html>maintenance</html>"))
        with pytest.raises(UpstreamError):
            asyncio.run(http.request_json("https://example.test/data", source="Example"))
