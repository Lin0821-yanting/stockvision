"""大盤總覽：市值排行、指數、走勢、單檔失敗與參數檢查。"""

from datetime import UTC, datetime
from decimal import Decimal

import httpx
import pytest

from app.core.config import get_settings
from app.services import catalog_service, universe_service
from app.services.entities import StockEntry
from app.services.providers import twse_openapi
from tests.factories import mis_item, tw_price_rows, twse_company_row, twse_day_row, us_price_rows

TW_COMPANIES = [
    ("2330", "台積電", 25_932_370_067, 2415.0),
    ("2317", "鴻海", 14_075_746_497, 250.0),
    ("2454", "聯發科", 1_600_000_000, 1500.0),
    ("1101", "台泥", 7_523_181_742, 30.0),
]


def rising(start: float, count: int = 90, step: float = 1.0) -> list[float]:
    return [round(start + step * index, 2) for index in range(count)]


@pytest.fixture
def tw_market(upstream):
    upstream.twse_companies = [twse_company_row(code, name, shares) for code, name, shares, _ in TW_COMPANIES] + [
        twse_company_row("9105", "泰金寶-DR", 2_000_000_000),  # TDR 不列入
        twse_company_row("2412", "中華電", 7_757_446_545),  # 沒有收盤價，不列入
    ]
    upstream.twse_day_all = [twse_day_row(code, name, close) for code, name, _, close in TW_COMPANIES] + [
        twse_day_row("9105", "泰金寶-DR", 500.0),
    ]
    upstream.mis_items["t00"] = mis_item("t00", "發行量加權股價指數", z="46368.33", y="46000.00", v="5000")
    upstream.finmind[("TaiwanStockPrice", "TAIEX")] = tw_price_rows("TAIEX", rising(44000, step=20))
    for code, name, _, close in TW_COMPANIES:
        upstream.mis_items[code] = mis_item(code, name, z=f"{close + 5:.4f}", y=f"{close:.4f}")
        upstream.finmind[("TaiwanStockPrice", code)] = tw_price_rows(code, rising(close - 60))
    return upstream


US_INFO = [
    ("NVDA", "NVIDIA Corporation Common Stock", 5.25e12, "2026-10-29"),
    ("AAPL", "Apple Inc. Common Stock", 5.06e12, "2026-10-29"),
    ("MSFT", "Microsoft Corporation Common Stock", 3.94e12, "2026-10-29"),
    ("GOOGL", "Alphabet Inc. Class A Common Stock", 3.92e12, "2026-10-29"),
    ("GOOG", "Alphabet Inc. Class C Capital Stock", 3.87e12, "2026-10-29"),
    ("GOOGM", "Alphabet Inc. Depositary Shares representing a 1/20th Interest in a Share of Series A Mandatory Convertible Preferred Stock", 5.6e11, "2026-10-29"),
    ("LTM", "LATAM Airlines Group S.A.", 1.49e13, "2024-07-26"),  # 停在舊日期的錯誤市值
    ("BRK/B", "Berkshire Hathaway Inc.", 1.19e12, "2026-10-29"),  # 代號含「/」無法查詢
    ("AMZN", "Amazon.com Inc. Common Stock", 2.73e12, "2026-10-29"),
]


def us_info(with_caps: bool = True) -> list[dict]:
    return [
        {"date": day, "stock_id": symbol, "Country": "United States", "IPOYear": 2000.0,
         "MarketCap": cap if with_caps else None, "Subsector": "Tech", "stock_name": name}
        for symbol, name, cap, day in US_INFO
    ]


@pytest.fixture
def us_market(upstream):
    upstream.finmind[("USStockInfo", None)] = us_info()
    for symbol, start in (("^GSPC", 6800.0), ("^IXIC", 23000.0), ("^DJI", 47000.0)):
        upstream.finmind[("USStockPrice", symbol)] = us_price_rows(symbol, rising(start, step=5))
    for symbol, _, _, _ in US_INFO:
        upstream.finmind[("USStockPrice", symbol)] = us_price_rows(symbol, rising(200.0))
    return upstream


# ---------------------------------------------------------------- 排行


def test_tw_ranking_is_shares_times_close_without_tdr():
    companies = twse_openapi.parse_company_basics(
        [twse_company_row(code, name, shares) for code, name, shares, _ in TW_COMPANIES]
        + [twse_company_row("9105", "泰金寶-DR", 2_000_000_000), {"公司代號": "", "已發行普通股數或TDR原股發行股數": "1"}]
    )
    from app.services.providers.twse_openapi import parse_stock_day_all

    snapshots = parse_stock_day_all(
        [twse_day_row(code, name, close) for code, name, _, close in TW_COMPANIES] + [twse_day_row("9105", "泰金寶-DR", 500.0)]
    )

    ranked = universe_service.rank_tw(companies, snapshots)

    assert [item.entry.symbol for item in ranked] == ["2330", "2317", "2454", "1101"]
    assert ranked[0].market_cap == Decimal("2415.00") * 25_932_370_067
    assert ranked[0].entry.name == "台積電" and ranked[0].entry.exchange == "TWSE"


def test_us_ranking_merges_share_classes_and_skips_preferred():
    candidates = [
        (StockEntry("US", symbol, name, "US"), cap)
        for symbol, name, cap in [
            ("NVDA", "NVIDIA Corporation", 5.25e12),
            ("GOOGL", "Alphabet Inc. Class A", 3.92e12),
            ("GOOG", "Alphabet Inc. Class C Capital Stock", 3.87e12),
            ("GOOGM", "Alphabet Inc. Depositary Shares representing Series A Preferred Stock", 5.6e11),
            ("SKHY", "SK hynix Inc. American Depositary Shares", 1.06e12),
        ]
    ]

    ranked = universe_service.rank_us(candidates)

    assert [item.entry.symbol for item in ranked] == ["NVDA", "GOOGL", "SKHY"]
    assert universe_service.company_key("Alphabet Inc. Class C Capital Stock") == universe_service.company_key(
        "Alphabet Inc. Class A"
    )


def test_us_market_caps_ignore_stale_rows():
    caps = catalog_service.parse_us_market_caps(us_info())

    assert caps["NVDA"] == 5.25e12
    assert "LTM" not in caps  # 資料日期 2024-07-26，市值不可信
    assert "BRK/B" not in caps


# ---------------------------------------------------------------- API


def test_tw_overview_has_index_and_large_caps(client, tw_market):
    response = client.get("/api/market/overview", params={"market": "TW", "period": "1M", "limit": 4})

    assert response.status_code == 200
    body = response.json()
    [index] = body["indices"]
    assert index["symbol"] == "TAIEX" and index["is_index"] is True and index["rank"] is None
    assert index["quote"]["price"] == 46368.33 and index["quote"]["kind"] == "realtime"
    assert index["quote"]["volume"] is None
    assert index["points"][-1] == {"date": "2026-10-28", "close": 45780.0}

    stocks = body["stocks"]
    assert [item["symbol"] for item in stocks] == ["2330", "2317", "2454", "1101"]
    assert [item["rank"] for item in stocks] == [1, 2, 3, 4]
    assert stocks[0]["market_cap"] == pytest.approx(2415 * 25_932_370_067)
    assert stocks[0]["quote"]["price"] == 2420.0 and stocks[0]["quote"]["source"] == "TWSE MIS"

    points = stocks[0]["points"]
    assert 20 <= len(points) <= 24  # 約一個月的交易日（含期初基準日）
    assert stocks[0]["period_return_pct"] == pytest.approx((points[-1]["close"] / points[0]["close"] - 1) * 100, abs=0.01)
    assert stocks[0]["history_end"] == "2026-10-28"

    assert body["ranking"]["method"] == "已發行普通股數 × 收盤價"
    assert body["ranking"]["as_of"] == "2026-10-28"
    assert body["market_open"] is True and body["warnings"] == []
    # 指數和 4 檔個股合併成一次 MIS 請求
    assert len(tw_market.mis_calls) == 1 and "tse_t00.tw" in tw_market.mis_calls[0]


def test_longer_period_returns_more_points(client, tw_market):
    one_month = client.get("/api/market/overview", params={"market": "TW", "period": "1M", "limit": 4}).json()
    three_months = client.get("/api/market/overview", params={"market": "TW", "period": "3M", "limit": 4}).json()

    assert len(three_months["stocks"][0]["points"]) > len(one_month["stocks"][0]["points"])
    assert three_months["period"] == "3M"


def test_us_overview_without_finnhub_marks_close(client, us_market):
    body = client.get("/api/market/overview", params={"market": "US", "limit": 4}).json()

    assert [item["symbol"] for item in body["indices"]] == ["^GSPC", "^IXIC", "^DJI"]
    assert all(item["quote"]["kind"] == "close" for item in body["indices"])
    assert "指數只有每日收盤" in body["indices"][0]["quote"]["note"]
    # LTM 的舊市值、BRK/B 與 Alphabet 的其他股票類別都不會出現
    assert [item["symbol"] for item in body["stocks"]] == ["NVDA", "AAPL", "MSFT", "GOOGL"]
    assert body["stocks"][0]["quote"]["kind"] == "close"
    assert body["ranking"]["source"] == "FinMind USStockInfo"


def test_us_indices_never_use_finnhub(client, us_market, set_now, monkeypatch):
    monkeypatch.setattr(get_settings(), "finnhub_api_key", "test-key")
    set_now(datetime(2026, 10, 29, 14, 30, tzinfo=UTC))  # 紐約 10:30 盤中
    us_market.finnhub["NVDA"] = {"c": 210.0, "d": 1.0, "dp": 0.48, "h": 211.0, "l": 205.0, "o": 206.0, "pc": 209.0,
                                 "t": int(datetime(2026, 10, 29, 14, 29, tzinfo=UTC).timestamp())}

    body = client.get("/api/market/overview", params={"market": "US", "limit": 4}).json()

    assert body["stocks"][0]["quote"]["kind"] == "realtime"
    assert not any(symbol.startswith("^") for symbol in us_market.finnhub_calls)
    assert all(item["quote"]["kind"] == "close" for item in body["indices"])


def test_one_failing_stock_only_affects_its_card(client, tw_market):
    tw_market.finmind[("TaiwanStockPrice", "2454")] = httpx.Response(500)
    del tw_market.mis_items["1101"]  # MIS 沒有資料時改用日資料收盤

    response = client.get("/api/market/overview", params={"market": "TW", "limit": 4})

    assert response.status_code == 200
    stocks = {item["symbol"]: item for item in response.json()["stocks"]}
    assert stocks["2454"]["points"] == [] and "FinMind" in stocks["2454"]["history_error"]
    assert stocks["2454"]["quote"]["source"] == "TWSE MIS"
    assert stocks["1101"]["quote"]["kind"] == "close" and stocks["1101"]["points"]
    assert stocks["2330"]["history_error"] is None


def test_ranking_failure_still_shows_indices(client, tw_market):
    tw_market.twse_companies = []

    body = client.get("/api/market/overview", params={"market": "TW"}).json()

    assert body["stocks"] == [] and body["ranking"] is None
    assert "大型股排行暫時無法取得" in body["warnings"][0]
    assert body["indices"][0]["quote"]["price"] == 46368.33


def test_old_catalog_without_market_caps_is_refreshed_once(client, us_market):
    us_market.finmind[("USStockInfo", None)] = us_info(with_caps=False)

    first = client.get("/api/market/overview", params={"market": "US", "limit": 4}).json()
    second = client.get("/api/market/overview", params={"market": "US", "limit": 5}).json()

    # 第一次：下載清單後發現沒有市值，再強制重新下載一次；之後 12 小時內不再重試
    assert us_market.finmind_calls.count(("USStockInfo", None)) == 2
    assert first["stocks"] == [] and second["stocks"] == []
    assert "沒有市值資料" in second["warnings"][0]


@pytest.mark.parametrize("params", [{"market": "JP"}, {"period": "5Y"}, {"limit": 2}, {"limit": 31}])
def test_invalid_parameters_return_422(client, params):
    response = client.get("/api/market/overview", params=params)

    assert response.status_code == 422
