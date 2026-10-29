"""臺灣證券交易所「基本市況報導」MIS 盤中報價。

這是證交所網站本身使用的公開端點，不在官方 OpenAPI 文件內，約每 5 秒更新一次。
請求太頻繁可能被暫時封鎖，因此 quote_service 會把多檔股票合併成一次請求，
並加上 5 秒快取與最小請求間隔。
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from app.core.market_hours import TAIPEI
from app.core.money import to_decimal
from app.services.providers.http import get_json

URL = "https://mis.twse.com.tw/stock/api/getStockInfo.jsp"
SOURCE = "TWSE MIS"


@dataclass(frozen=True)
class MisQuote:
    symbol: str
    name: str
    exchange: str  # tse / otc
    price: Decimal | None  # 最近成交價；當日尚無成交時為 None
    prev_close: Decimal | None
    open: Decimal | None
    high: Decimal | None
    low: Decimal | None
    volume: int | None  # 累積成交量（股）；MIS 原始單位是張
    trade_date: date | None
    trade_time: datetime | None  # 最近成交時間（台北時間）


def _parse_datetime(day: str, clock_time: str) -> datetime | None:
    try:
        return datetime.strptime(f"{day} {clock_time}", "%Y%m%d %H:%M:%S").replace(tzinfo=TAIPEI)
    except ValueError:
        return None


def _parse_date(day: str) -> date | None:
    try:
        return datetime.strptime(day, "%Y%m%d").date()
    except ValueError:
        return None


def parse_mis_payload(payload: Any) -> dict[str, MisQuote]:
    quotes: dict[str, MisQuote] = {}
    items = payload.get("msgArray", []) if isinstance(payload, dict) else []
    for item in items:
        code = str(item.get("c", "")).strip()
        if not code:
            continue
        trade = item.get("trade") if isinstance(item.get("trade"), dict) else {}
        price = to_decimal(item.get("z"))
        if price is None:
            price = to_decimal(trade.get("z"))
        day = str(item.get("d", "")).strip()
        lots = to_decimal(item.get("v"))
        quotes[code] = MisQuote(
            symbol=code,
            name=str(item.get("n", "")).strip(),
            exchange=str(item.get("ex", "")).strip(),
            price=price if price is not None and price > 0 else None,
            prev_close=to_decimal(item.get("y")),
            open=to_decimal(item.get("o")),
            high=to_decimal(item.get("h")),
            low=to_decimal(item.get("l")),
            volume=int(lots * 1000) if lots is not None else None,
            trade_date=_parse_date(day),
            trade_time=_parse_datetime(day, str(item.get("t") or trade.get("t") or "")),
        )
    return quotes


async def fetch_quotes(channels: list[tuple[str, str]]) -> dict[str, MisQuote]:
    """channels 例如 [("tse", "2330"), ("otc", "6488")]，一次請求取得全部報價。"""
    params = {
        "ex_ch": "|".join(f"{exchange}_{code}.tw" for exchange, code in channels),
        "json": "1",
        "delay": "0",
        "_": str(int(time.time() * 1000)),
    }
    payload = await get_json(URL, source=SOURCE, params=params, retries=1)
    return parse_mis_payload(payload)
