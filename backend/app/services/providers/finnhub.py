"""Finnhub 美股即時報價（https://finnhub.io/docs/api/quote）。

需要免費 API Key（FINNHUB_API_KEY），免費方案約每分鐘 60 次。
/quote 回應沒有成交量；不存在的代號會回傳全部為 0 的資料。
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from app.core.config import get_settings
from app.core.errors import UpstreamError
from app.core.money import to_decimal
from app.services.providers.http import request_json

URL = "https://finnhub.io/api/v1/quote"
SOURCE = "Finnhub"


@dataclass(frozen=True)
class FinnhubQuote:
    symbol: str
    price: Decimal
    change: Decimal | None
    change_pct: Decimal | None
    open: Decimal | None
    high: Decimal | None
    low: Decimal | None
    prev_close: Decimal | None
    as_of: datetime


def parse_quote(symbol: str, payload: Any) -> FinnhubQuote | None:
    if not isinstance(payload, dict):
        return None
    price = to_decimal(payload.get("c"))
    timestamp = payload.get("t")
    if price is None or price <= 0 or not timestamp:
        return None
    return FinnhubQuote(
        symbol=symbol,
        price=price,
        change=to_decimal(payload.get("d")),
        change_pct=to_decimal(payload.get("dp")),
        open=to_decimal(payload.get("o")),
        high=to_decimal(payload.get("h")),
        low=to_decimal(payload.get("l")),
        prev_close=to_decimal(payload.get("pc")),
        as_of=datetime.fromtimestamp(int(timestamp), UTC),
    )


async def fetch_quote(symbol: str) -> FinnhubQuote | None:
    api_key = get_settings().finnhub_api_key.strip()
    status, payload = await request_json(
        URL,
        source=SOURCE,
        params={"symbol": symbol},
        headers={"X-Finnhub-Token": api_key},
        retries=1,
    )
    if status in (401, 403):
        raise UpstreamError(
            "Finnhub API Key 無效或沒有權限，請檢查 .env 的 FINNHUB_API_KEY",
            details={"source": SOURCE, "status": status},
        )
    if status >= 400:
        raise UpstreamError(f"Finnhub 回應錯誤（HTTP {status}）", details={"source": SOURCE, "status": status})
    return parse_quote(symbol, payload)
