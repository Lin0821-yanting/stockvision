"""多股標準化比較：日期對齊、基準 = 100、累積報酬與 API 驗證。"""

from datetime import date

import pandas as pd
import pytest

from app.services import analytics
from tests.factories import mis_item, tw_price_rows, us_price_rows


def _frame(market: str, days: list[str], closes: list[float]) -> pd.DataFrame:
    if market == "TW":
        rows = [{"date": d, "open": c, "max": c, "min": c, "close": c, "Trading_Volume": 1000} for d, c in zip(days, closes)]
    else:
        rows = [{"date": d, "Open": c, "High": c, "Low": c, "Close": c, "Volume": 1000} for d, c in zip(days, closes)]
    return analytics.clean_history(rows, market)


def test_normalize_aligns_only_common_trading_days():
    # 台股 10/23、10/26 休市；美股 10/27 假設休市 → 只能比較兩邊都有交易的日子
    tw = _frame("TW", ["2026-10-20", "2026-10-21", "2026-10-22", "2026-10-27", "2026-10-28"], [100, 110, 120, 130, 125])
    us = _frame("US", ["2026-10-20", "2026-10-21", "2026-10-22", "2026-10-23", "2026-10-26", "2026-10-28"], [50, 50, 55, 60, 58, 40])

    result = analytics.normalize_prices({"2330": tw, "AAPL": us}, months=1)

    assert [d.date() for d in result.closes.index] == [date(2026, 10, 20), date(2026, 10, 21), date(2026, 10, 22), date(2026, 10, 28)]
    assert result.common_start == date(2026, 10, 20) and result.common_end == date(2026, 10, 28)
    assert result.normalized.iloc[0].tolist() == [100.0, 100.0]
    assert result.normalized["2330"].tolist() == pytest.approx([100, 110, 120, 125])
    assert result.normalized["AAPL"].tolist() == pytest.approx([100, 100, 110, 80])
    assert result.cumulative_return_pct == {"2330": 25.0, "AAPL": -20.0}
    assert result.excluded_dates == {"2330": 1, "AAPL": 2}


def test_normalize_reports_max_drawdown():
    days = ["2026-10-01", "2026-10-02", "2026-10-05", "2026-10-06"]
    result = analytics.normalize_prices(
        {"A": _frame("US", days, [100, 120, 90, 110]), "B": _frame("US", days, [10, 11, 12, 13])}, months=1
    )

    assert result.max_drawdown_pct["A"] == -25.0  # 120 → 90
    assert result.max_drawdown_pct["B"] == 0.0


def test_normalize_window_starts_from_latest_end_date():
    tw = analytics.clean_history(tw_price_rows("2330", [100.0 + i for i in range(80)]), "TW")
    us = analytics.clean_history(us_price_rows("AAPL", [200.0 + i for i in range(80)]), "US")

    result = analytics.normalize_prices({"2330": tw, "AAPL": us}, months=1)

    assert result.common_end == date(2026, 10, 28)
    assert result.common_start >= date(2026, 9, 28)


def test_normalize_rejects_no_common_dates():
    a = _frame("TW", ["2026-10-01", "2026-10-02"], [1, 2])
    b = _frame("US", ["2026-10-05", "2026-10-06"], [1, 2])

    with pytest.raises(ValueError):
        analytics.normalize_prices({"A": a, "B": b}, months=1)


@pytest.fixture
def market_data(upstream):
    upstream.finmind[("TaiwanStockPrice", "2330")] = tw_price_rows("2330", [2400.0 + i for i in range(30)])
    upstream.finmind[("TaiwanStockPrice", "2317")] = tw_price_rows("2317", [250.0 - i for i in range(30)])
    upstream.finmind[("USStockPrice", "AAPL")] = us_price_rows("AAPL", [340.0 + i / 2 for i in range(30)])
    upstream.mis_items["2330"] = mis_item("2330", "台積電", z="2415.0000", y="2425.0000")
    upstream.mis_items["2317"] = mis_item("2317", "鴻海", z="248.0000", y="251.5000")
    return upstream


def test_compare_api_returns_normalized_series(client, market_data):
    response = client.get("/api/stocks/compare", params={"symbols": "2330,2317,AAPL", "period": "1M"})

    assert response.status_code == 200
    body = response.json()
    assert body["computed_by"] == "Python Pandas"
    assert "inner join" in body["method"]
    assert body["series"][0]["values"] == {"2330": 100.0, "2317": 100.0, "AAPL": 100.0}
    assert body["aligned_points"] == len(body["series"])
    stocks = {stock["symbol"]: stock for stock in body["stocks"]}
    assert stocks["2330"]["latest_price"] == 2415.0 and stocks["2330"]["quote_source"] == "TWSE MIS"
    assert stocks["2317"]["cumulative_return_pct"] < 0 < stocks["2330"]["cumulative_return_pct"]
    last = body["series"][-1]
    assert last["values"]["2330"] == pytest.approx(stocks["2330"]["end_close"] / stocks["2330"]["start_close"] * 100, abs=0.01)


def test_compare_requires_two_to_four_symbols(client, market_data):
    one = client.get("/api/stocks/compare", params={"symbols": "2330"})
    same = client.get("/api/stocks/compare", params={"symbols": "2330,2330.TW"})
    five = client.get("/api/stocks/compare", params={"symbols": "2330,2317,AAPL,NVDA,6488"})

    assert one.status_code == 400 and one.json()["error"]["code"] == "INVALID_REQUEST"
    assert same.status_code == 400
    assert five.status_code == 400


def test_compare_route_is_not_treated_as_symbol(client, market_data):
    response = client.get("/api/stocks/compare", params={"symbols": "2330,2317"})

    assert response.status_code == 200
