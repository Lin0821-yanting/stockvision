"""Pandas 歷史資料整理、漲跌幅與報酬率計算。"""

from datetime import date

import pandas as pd
import pytest

from app.services import analytics
from tests.factories import tw_price_rows, us_price_rows


def _row(day: str, close: float, volume: int = 1000) -> dict:
    return {"date": day, "stock_id": "2330", "Trading_Volume": volume, "open": close, "max": close, "min": close, "close": close}


def test_clean_history_sorts_dedupes_and_drops_invalid_rows():
    rows = [
        _row("2026-10-02", 102),
        _row("2026-10-01", 100),
        _row("2026-10-02", 103),  # 同一天重複，保留最後一筆
        _row("2026-10-05", 0),  # 停牌的 0 元資料
        _row("not-a-date", 99),
    ]

    frame = analytics.clean_history(rows, "TW")

    assert frame["date"].dt.strftime("%Y-%m-%d").tolist() == ["2026-10-01", "2026-10-02"]
    assert frame["close"].tolist() == [100.0, 103.0]
    assert frame["volume"].dtype == "int64"


def test_clean_history_maps_us_columns_and_fills_missing_open():
    rows = us_price_rows("AAPL", [200.0, 210.0])
    rows[1]["Open"] = 0

    frame = analytics.clean_history(rows, "US")

    assert frame.columns.tolist()[:6] == ["date", "open", "high", "low", "close", "volume"]
    assert frame["open"].iloc[1] == 210.0  # 0 元開盤價以收盤價補上


def test_clean_history_rejects_unexpected_format():
    with pytest.raises(ValueError):
        analytics.clean_history([{"date": "2026-10-01", "price": 1}], "TW")


def test_daily_change_and_change_percent():
    frame = analytics.clean_history(tw_price_rows("2330", [100.0, 110.0, 99.0]), "TW")

    assert frame["change"].tolist()[1:] == pytest.approx([10.0, -11.0])
    assert frame["change_pct"].tolist()[1:] == pytest.approx([10.0, -10.0])


def test_slice_period_keeps_base_day_before_window():
    frame = analytics.clean_history(tw_price_rows("2330", [100.0 + i for i in range(60)]), "TW")
    last_day = frame["date"].iloc[-1]

    window = analytics.slice_period(frame, 1)

    first_day = window["date"].iloc[0]
    one_month_ago = last_day - pd.DateOffset(months=1)
    assert first_day <= one_month_ago
    assert window["date"].iloc[1] > one_month_ago
    assert window["date"].iloc[-1] == last_day


def test_summarize_computes_period_return():
    frame = analytics.clean_history(tw_price_rows("2330", [100.0, 90.0, 125.0]), "TW")

    stats = analytics.summarize(frame)

    assert stats["period_return_pct"] == 25.0
    assert stats["start_close"] == 100.0 and stats["end_close"] == 125.0
    assert stats["high"] == 130.0 and stats["low"] == 85.0
    assert stats["trading_days"] == 3


def test_return_pct_handles_zero_base():
    assert analytics.return_pct(0, 10) is None
    assert analytics.return_pct(50, 40) == pytest.approx(-20.0)


def test_recent_low_excludes_today():
    closes = [120.0 - i for i in range(20)] + [80.0]  # 最後一天大跌
    frame = analytics.clean_history(tw_price_rows("2330", closes), "TW")
    last_day = frame["date"].iloc[-1].date()

    assert analytics.recent_low(frame, 20) == 80.0
    assert analytics.recent_low(frame, 20, exclude_date=last_day) == 101.0
    assert analytics.recent_low(frame.head(10), 20) is None


def test_to_bar_records_converts_nan_to_none():
    frame = analytics.clean_history(tw_price_rows("2330", [100.0, 101.0]), "TW")

    records = analytics.to_bar_records(frame)

    assert records[0]["change"] is None and records[0]["change_pct"] is None
    assert records[1]["change"] == 1.0
    assert isinstance(records[0]["date"], date)
