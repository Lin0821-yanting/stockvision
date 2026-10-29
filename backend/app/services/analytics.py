"""Pandas 數據分析：歷史資料清理、漲跌幅、區間報酬、20 日新低。

這裡的函式都是純函式（不呼叫網路也不碰資料庫），方便單元測試。
"""

from __future__ import annotations

from datetime import date
from typing import Any

import pandas as pd

PRICE_COLUMNS = ["open", "high", "low", "close"]

# FinMind 台股與美股日資料的欄位名稱不同，統一轉成 date/open/high/low/close/volume
FIELD_MAP: dict[str, dict[str, str]] = {
    "TW": {
        "date": "date",
        "open": "open",
        "max": "high",
        "min": "low",
        "close": "close",
        "Trading_Volume": "volume",
    },
    "US": {
        "date": "date",
        "Open": "open",
        "High": "high",
        "Low": "low",
        "Close": "close",
        "Volume": "volume",
    },
}


def empty_history() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "date": pd.Series(dtype="datetime64[ns]"),
            **{column: pd.Series(dtype="float64") for column in PRICE_COLUMNS},
            "volume": pd.Series(dtype="int64"),
            "change": pd.Series(dtype="float64"),
            "change_pct": pd.Series(dtype="float64"),
        }
    )


def clean_history(records: list[dict[str, Any]], market: str) -> pd.DataFrame:
    """把 FinMind 日資料整理成依日期排序、去除重複與無效價格的 DataFrame。"""
    if not records:
        return empty_history()

    mapping = FIELD_MAP[market]
    frame = pd.DataFrame.from_records(records)
    missing = [field for field in mapping if field not in frame.columns]
    if missing:
        raise ValueError(f"歷史資料缺少欄位：{', '.join(missing)}")

    frame = frame[list(mapping)].rename(columns=mapping)
    frame["date"] = pd.to_datetime(frame["date"], errors="coerce")
    for column in [*PRICE_COLUMNS, "volume"]:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")

    # 停牌或資料錯誤時 FinMind 可能回傳 0 元，這些列不能拿來計算報酬
    frame = frame.dropna(subset=["date", "close"])
    frame = frame[frame["close"] > 0]
    # 穩定排序：同一天重複出現時保留 API 回傳順序中的最後一筆
    frame = frame.sort_values("date", kind="stable").drop_duplicates(subset="date", keep="last").reset_index(drop=True)

    for column in ("open", "high", "low"):
        frame[column] = frame[column].where(frame[column] > 0, frame["close"])
    frame["volume"] = frame["volume"].fillna(0).clip(lower=0).astype("int64")
    frame["change"] = frame["close"].diff()
    frame["change_pct"] = frame["close"].pct_change() * 100
    return frame


def slice_period(frame: pd.DataFrame, months: int) -> pd.DataFrame:
    """取最近 months 個月的資料，並保留期初前最後一個交易日當作報酬率的基準。"""
    if frame.empty:
        return frame
    start = frame["date"].iloc[-1] - pd.DateOffset(months=months)
    base_rows = frame.index[frame["date"] <= start]
    first_index = base_rows[-1] if len(base_rows) else 0
    return frame.iloc[first_index:].reset_index(drop=True)


def return_pct(start_price: float, end_price: float) -> float | None:
    if not start_price:
        return None
    return (end_price / start_price - 1) * 100


def summarize(frame: pd.DataFrame) -> dict[str, Any]:
    """區間統計：期初/期末收盤、累積報酬率、最高、最低與平均成交量。"""
    if frame.empty:
        return {
            "start_date": None,
            "end_date": None,
            "start_close": None,
            "end_close": None,
            "period_return_pct": None,
            "high": None,
            "low": None,
            "avg_volume": None,
            "trading_days": 0,
        }
    start_close = float(frame["close"].iloc[0])
    end_close = float(frame["close"].iloc[-1])
    period_return = return_pct(start_close, end_close)
    return {
        "start_date": frame["date"].iloc[0].date(),
        "end_date": frame["date"].iloc[-1].date(),
        "start_close": start_close,
        "end_close": end_close,
        "period_return_pct": round(period_return, 2) if period_return is not None else None,
        "high": float(frame["high"].max()),
        "low": float(frame["low"].min()),
        "avg_volume": int(frame["volume"].mean()),
        "trading_days": int(len(frame)),
    }


def recent_low(frame: pd.DataFrame, window: int = 20, exclude_date: date | None = None) -> float | None:
    """最近 window 個交易日的最低收盤價；exclude_date 用來排除「今天」本身。"""
    data = frame if exclude_date is None else frame[frame["date"].dt.date != exclude_date]
    if len(data) < window:
        return None
    return float(data["close"].iloc[-window:].min())


def to_bar_records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    """DataFrame → API 回應用的 list[dict]（NaN 轉成 None）。"""
    records = []
    for row in frame.itertuples(index=False):
        records.append(
            {
                "date": row.date.date(),
                "open": round(float(row.open), 4),
                "high": round(float(row.high), 4),
                "low": round(float(row.low), 4),
                "close": round(float(row.close), 4),
                "volume": int(row.volume),
                "change": None if pd.isna(row.change) else round(float(row.change), 4),
                "change_pct": None if pd.isna(row.change_pct) else round(float(row.change_pct), 4),
            }
        )
    return records
