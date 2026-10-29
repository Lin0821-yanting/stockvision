"""證券櫃檯買賣中心 OpenAPI（https://www.tpex.org.tw/openapi/）：上櫃股票每日收盤行情。"""

from __future__ import annotations

from typing import Any

from app.core.money import to_decimal
from app.services.providers.base import DailySnapshot, parse_roc_date
from app.services.providers.http import get_json

DAILY_CLOSE_URL = "https://www.tpex.org.tw/openapi/v1/tpex_mainboard_daily_close_quotes"
SOURCE = "TPEx OpenAPI daily_close_quotes"


def parse_daily_close(payload: Any) -> dict[str, DailySnapshot]:
    snapshots: dict[str, DailySnapshot] = {}
    for row in payload if isinstance(payload, list) else []:
        code = str(row.get("SecuritiesCompanyCode", "")).strip()
        trade_date = parse_roc_date(row.get("Date", ""))
        if not code or trade_date is None:
            continue
        volume = to_decimal(row.get("TradingShares"))
        snapshots[code] = DailySnapshot(
            symbol=code,
            name=str(row.get("CompanyName", "")).strip(),
            trade_date=trade_date,
            open=to_decimal(row.get("Open")),
            high=to_decimal(row.get("High")),
            low=to_decimal(row.get("Low")),
            close=to_decimal(row.get("Close")),
            change=to_decimal(row.get("Change")),
            volume=int(volume) if volume is not None else None,
            source=SOURCE,
        )
    return snapshots


async def fetch_daily_close() -> dict[str, DailySnapshot]:
    return parse_daily_close(await get_json(DAILY_CLOSE_URL, source=SOURCE))
