"""測試資料產生器：欄位格式與 2026-10-29 實測的真實 API 回應相同。"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any


def trading_days(end: date, count: int) -> list[date]:
    """截至 end（含）往前數 count 個平日，依日期由舊到新排列。"""
    days, day = [], end
    while len(days) < count:
        if day.weekday() < 5:
            days.append(day)
        day -= timedelta(days=1)
    return days[::-1]


def tw_info_rows() -> list[dict[str, Any]]:
    return [
        {"industry_category": "半導體業", "stock_id": "2330", "stock_name": "台積電", "type": "twse", "date": "2026-10-29"},
        {"industry_category": "電子工業", "stock_id": "2330", "stock_name": "台積電舊資料", "type": "twse", "date": "2020-06-03"},
        {"industry_category": "其他電子業", "stock_id": "2317", "stock_name": "鴻海", "type": "twse", "date": "2026-10-29"},
        {"industry_category": "半導體業", "stock_id": "6488", "stock_name": "環球晶", "type": "tpex", "date": "2026-10-29"},
        {"industry_category": "Index", "stock_id": "TAIEX", "stock_name": "加權指數", "type": "twse", "date": "2026-10-29"},
        {"industry_category": "生技醫療業", "stock_id": "6999", "stock_name": "興櫃測試", "type": "emerging", "date": "2026-10-29"},
    ]


def us_info_rows() -> list[dict[str, Any]]:
    base = {"Country": "United States", "IPOYear": 1980.0, "MarketCap": 3.4e12}
    return [
        {**base, "date": "2026-10-29", "stock_id": "AAPL", "Subsector": "Computer Manufacturing", "stock_name": "Apple Inc. Common Stock"},
        {**base, "date": "2023-03-18", "stock_id": "AAPL", "Subsector": "Old", "stock_name": "Apple Old Name"},
        {**base, "date": "2026-10-29", "stock_id": "NVDA", "Subsector": "Semiconductors", "stock_name": "NVIDIA Corporation Common Stock"},
        {**base, "date": "2026-10-29", "stock_id": "bad symbol!", "Subsector": "x", "stock_name": "Invalid"},
    ]


def tw_price_rows(stock_id: str, closes: list[float], end: date = date(2026, 10, 28)) -> list[dict[str, Any]]:
    return [
        {
            "date": day.isoformat(),
            "stock_id": stock_id,
            "Trading_Volume": 20_000_000 + index,
            "Trading_money": int(close * 20_000_000),
            "open": close - 1,
            "max": close + 5,
            "min": close - 5,
            "close": close,
            "spread": 0.0,
            "Trading_turnover": 100_000,
        }
        for index, (day, close) in enumerate(zip(trading_days(end, len(closes)), closes))
    ]


def us_price_rows(stock_id: str, closes: list[float], end: date = date(2026, 10, 28)) -> list[dict[str, Any]]:
    return [
        {
            "date": day.isoformat(),
            "stock_id": stock_id,
            "Adj_Close": close,
            "Close": close,
            "High": close + 2,
            "Low": close - 2,
            "Open": close - 0.5,
            "Volume": 35_000_000 + index,
        }
        for index, (day, close) in enumerate(zip(trading_days(end, len(closes)), closes))
    ]


def mis_item(
    code: str,
    name: str,
    *,
    z: str,
    y: str,
    d: str = "20261029",
    t: str = "10:15:30",
    v: str = "12345",
    ex: str = "tse",
    trade: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """TWSE MIS msgArray 的一筆資料（只保留本專案會用到的欄位與幾個實際會出現的欄位）。"""
    item = {
        "@": f"{code}.tw",
        "c": code,
        "n": name,
        "ex": ex,
        "z": z,
        "y": y,
        "o": "2420.0000" if z != "-" else "-",
        "h": "2425.0000" if z != "-" else "-",
        "l": "2390.0000" if z != "-" else "-",
        "v": v,
        "d": d,
        "t": t,
        "%": t,
        "a": "2415.0000_2420.0000_",
        "b": "2410.0000_2405.0000_",
        "tlong": "1793255400000",
    }
    if trade is not None:
        item["trade"] = trade
    return item


def usd_rate_rows() -> list[dict[str, Any]]:
    return [
        {"date": "2026-10-27", "currency": "USD", "cash_buy": 32.055, "cash_sell": 32.725, "spot_buy": 32.405, "spot_sell": 32.505},
        {"date": "2026-10-29", "currency": "USD", "cash_buy": 32.09, "cash_sell": 32.76, "spot_buy": 32.44, "spot_sell": 32.54},
        {"date": "2026-10-28", "currency": "USD", "cash_buy": 32.02, "cash_sell": 32.69, "spot_buy": -1, "spot_sell": -1},
    ]


def twse_company_row(code: str, short_name: str, shares: int) -> dict[str, Any]:
    """t187ap03_L（上市公司基本資料）的一筆資料，只保留排行會用到的欄位與幾個實際會出現的欄位。"""
    return {
        "出表日期": "1151028",
        "公司代號": code,
        "公司名稱": f"{short_name}股份有限公司",
        "公司簡稱": short_name,
        "外國企業註冊地國": "－ ",
        "產業別": "24",
        "普通股每股面額": "新台幣                 10.0000元",
        "已發行普通股數或TDR原股發行股數": str(shares),
    }


def twse_day_row(code: str, name: str, close: float, change: float = 0.0) -> dict[str, Any]:
    """STOCK_DAY_ALL（上市個股日成交資訊）的一筆資料。"""
    return {
        "Date": "1151028",
        "Code": code,
        "Name": name,
        "TradeVolume": "21866835",
        "OpeningPrice": f"{close:.2f}",
        "HighestPrice": f"{close + 5:.2f}",
        "LowestPrice": f"{close - 5:.2f}",
        "ClosingPrice": f"{close:.2f}",
        "Change": f"{change:.4f}",
    }
