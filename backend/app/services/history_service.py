"""歷史日資料：一次向 FinMind 抓約 400 天後快取 30 分鐘，再依期間切出 1M/3M/6M/1Y。"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from typing import TYPE_CHECKING

import pandas as pd

from app.core import clock
from app.core.errors import AppError, SymbolNotFoundError, UpstreamError
from app.core.market_hours import session_for
from app.core.money import to_decimal
from app.schemas.stock import HistoryOut, HistoryStats, PriceBar
from app.services import analytics
from app.services.cache import cache
from app.services.entities import StockEntry
from app.services.providers import finmind

if TYPE_CHECKING:
    from app.schemas.stock import QuoteOut

HISTORY_TTL_SECONDS = 30 * 60
LOOKBACK_DAYS = 400
PERIOD_MONTHS = {"1M": 1, "3M": 3, "6M": 6, "1Y": 12}
SOURCE_NAMES = {"TW": "FinMind TaiwanStockPrice", "US": "FinMind USStockPrice"}
DATA_NOTE = "每日收盤資料（非即時報價），最新一筆為最近已收盤的交易日"


@dataclass(frozen=True)
class DailyData:
    frame: pd.DataFrame
    fetched_at: datetime


async def get_daily_data(entry: StockEntry) -> DailyData:
    async def load() -> DailyData:
        end = session_for(entry.market).today()
        start = end - timedelta(days=LOOKBACK_DAYS)
        fetch = finmind.taiwan_stock_price if entry.market == "TW" else finmind.us_stock_price
        rows = await fetch(entry.symbol, start, end)
        try:
            frame = analytics.clean_history(rows, entry.market)
        except ValueError as exc:
            raise UpstreamError(f"FinMind 歷史資料格式不正確：{exc}", details={"source": "FinMind"}) from exc
        return DailyData(frame=frame, fetched_at=clock.now())

    return await cache.get_or_set(f"history:{entry.key}", HISTORY_TTL_SECONDS, load)


async def get_history(entry: StockEntry, period: str) -> HistoryOut:
    daily = await get_daily_data(entry)
    if daily.frame.empty:
        raise SymbolNotFoundError(
            f"{entry.symbol} 沒有可用的歷史價格資料",
            details={"symbol": entry.symbol, "market": entry.market},
        )
    window = analytics.slice_period(daily.frame, PERIOD_MONTHS[period])
    return HistoryOut(
        symbol=entry.symbol,
        market=entry.market,
        name=entry.name,
        currency=entry.currency,
        period=period,
        source=SOURCE_NAMES[entry.market],
        data_note=DATA_NOTE,
        fetched_at=daily.fetched_at,
        bars=[PriceBar(**record) for record in analytics.to_bar_records(window)],
        stats=HistoryStats(**analytics.summarize(window)),
    )


async def twenty_day_low(entry: StockEntry, quote: QuoteOut) -> tuple[Decimal | None, bool]:
    """回傳（前 20 個交易日最低收盤價, 最新價格是否創 20 日新低）。"""
    try:
        daily = await get_daily_data(entry)
    except AppError:
        return None, False
    low = analytics.recent_low(daily.frame, 20, exclude_date=quote.trade_date)
    low_value = to_decimal(low)
    if low_value is None or quote.price is None:
        return low_value, False
    return low_value, quote.price < low_value
