"""USD/TWD 匯率：FinMind TaiwanExchangeRate（臺灣銀行牌告，日資料），取即期買入與賣出的中價。"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

from app.core import clock
from app.core.errors import UpstreamError
from app.core.market_hours import session_for
from app.core.money import quantize_price, to_decimal
from app.schemas.market import FxRateOut
from app.services.cache import cache
from app.services.providers import finmind

FX_TTL_SECONDS = 60 * 60
SOURCE = "FinMind TaiwanExchangeRate（臺灣銀行牌告）"
NOTE = "臺灣銀行即期買入與賣出匯率的中價（日資料，非即時匯率）；模擬交易不計匯差與手續費"


def parse_usd_twd(rows: list[dict[str, Any]], fetched_at: datetime) -> FxRateOut:
    valid = []
    for row in rows:
        spot_buy = to_decimal(row.get("spot_buy"))
        spot_sell = to_decimal(row.get("spot_sell"))
        if spot_buy and spot_sell and spot_buy > 0 and spot_sell > 0:
            valid.append((str(row.get("date", "")), spot_buy, spot_sell))
    if not valid:
        raise UpstreamError("FinMind 沒有可用的 USD/TWD 匯率資料", details={"source": SOURCE})
    rate_date, spot_buy, spot_sell = max(valid, key=lambda item: item[0])
    return FxRateOut(
        rate=quantize_price((spot_buy + spot_sell) / 2),
        spot_buy=spot_buy,
        spot_sell=spot_sell,
        rate_date=date.fromisoformat(rate_date),
        source=SOURCE,
        note=NOTE,
        fetched_at=fetched_at,
    )


async def get_usd_twd() -> FxRateOut:
    async def load() -> FxRateOut:
        start = session_for("TW").today() - timedelta(days=14)
        return parse_usd_twd(await finmind.exchange_rate("USD", start), clock.now())

    return await cache.get_or_set("fx:USD/TWD", FX_TTL_SECONDS, load)
