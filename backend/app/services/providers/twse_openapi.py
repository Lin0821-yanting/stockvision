"""臺灣證券交易所 OpenAPI（https://openapi.twse.com.tw/）：上市個股最新一日成交資訊。"""

from __future__ import annotations

from typing import Any

from app.core.money import to_decimal
from app.services.providers.base import DailySnapshot, parse_roc_date
from app.services.providers.http import get_json

STOCK_DAY_ALL_URL = "https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL"
SOURCE = "TWSE OpenAPI STOCK_DAY_ALL"


def parse_stock_day_all(payload: Any) -> dict[str, DailySnapshot]:
    snapshots: dict[str, DailySnapshot] = {}
    for row in payload if isinstance(payload, list) else []:
        code = str(row.get("Code", "")).strip()
        trade_date = parse_roc_date(row.get("Date", ""))
        if not code or trade_date is None:
            continue
        volume = to_decimal(row.get("TradeVolume"))
        snapshots[code] = DailySnapshot(
            symbol=code,
            name=str(row.get("Name", "")).strip(),
            trade_date=trade_date,
            open=to_decimal(row.get("OpeningPrice")),
            high=to_decimal(row.get("HighestPrice")),
            low=to_decimal(row.get("LowestPrice")),
            close=to_decimal(row.get("ClosingPrice")),
            change=to_decimal(row.get("Change")),
            volume=int(volume) if volume is not None else None,
            source=SOURCE,
        )
    return snapshots


async def fetch_stock_day_all() -> dict[str, DailySnapshot]:
    return parse_stock_day_all(await get_json(STOCK_DAY_ALL_URL, source=SOURCE))
