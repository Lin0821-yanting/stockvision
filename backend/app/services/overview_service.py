"""大盤總覽：一個市場一頁，包含指數與市值前幾大公司的最新報價、走勢與期間報酬。

報價沿用 quote_service（台股的指數與個股合併成一次 MIS 請求），走勢沿用 history_service 的日資料快取。
整份結果快取 30 秒，多個分頁同時輪詢也只會向外部 API 取一次。
"""

from __future__ import annotations

import asyncio
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core import clock
from app.core.errors import AppError
from app.core.market_hours import session_for
from app.models.user import User
from app.schemas.overview import OverviewItemOut, OverviewOut, RankingOut, SparkPoint
from app.schemas.stock import QuoteErrorOut
from app.services import alert_service, analytics, history_service, quote_service, universe_service
from app.services.cache import cache
from app.services.entities import StockEntry
from app.services.history_service import DailyData

OVERVIEW_TTL_SECONDS = 30
HISTORY_CONCURRENCY = 4  # 同時向 FinMind 發出的請求數

INDICES: dict[str, list[StockEntry]] = {
    "TW": [StockEntry("TW", "TAIEX", "加權指數", "TWSE", is_index=True, mis_symbol="t00")],
    "US": [
        StockEntry("US", "^GSPC", "S&P 500", "US", is_index=True),
        StockEntry("US", "^IXIC", "NASDAQ 綜合指數", "US", is_index=True),
        StockEntry("US", "^DJI", "道瓊工業指數", "US", is_index=True),
    ],
}


async def _load_histories(entries: list[StockEntry]) -> list[DailyData | AppError]:
    semaphore = asyncio.Semaphore(HISTORY_CONCURRENCY)

    async def load(entry: StockEntry) -> DailyData | AppError:
        async with semaphore:
            try:
                return await history_service.get_daily_data(entry)
            except AppError as exc:
                return exc

    return await asyncio.gather(*(load(entry) for entry in entries))


def _item(
    entry: StockEntry,
    result: quote_service.QuoteResult,
    daily: DailyData | AppError,
    months: int,
    rank: int | None = None,
    market_cap: Decimal | None = None,
) -> OverviewItemOut:
    quote = result.quote
    if quote is not None and entry.is_index:
        quote = quote.model_copy(update={"volume": None, "volume_note": None})  # 指數的成交量單位和個股不同，不顯示
    quote_error = None
    if quote is None and result.error is not None:
        quote_error = QuoteErrorOut(symbol=entry.symbol, market=entry.market, code=result.error.code, message=result.error.message)

    points: list[SparkPoint] = []
    period_return = history_end = history_error = None
    if isinstance(daily, AppError):
        history_error = daily.message
    elif daily.frame.empty:
        history_error = "沒有可用的歷史價格資料"
    else:
        window = analytics.slice_period(daily.frame, months)
        points = [SparkPoint(date=row.date.date(), close=float(row.close)) for row in window.itertuples()]
        stats = analytics.summarize(window)
        period_return, history_end = stats["period_return_pct"], stats["end_date"]

    return OverviewItemOut(
        rank=rank,
        symbol=entry.symbol,
        name=entry.name,
        exchange=entry.exchange,
        currency=entry.currency,
        is_index=entry.is_index,
        market_cap=market_cap,
        quote=quote,
        quote_error=quote_error,
        points=points,
        period_return_pct=period_return,
        history_end=history_end,
        history_error=history_error,
    )


async def _build(db: Session, market: str, period: str, limit: int) -> OverviewOut:
    warnings: list[str] = []
    try:
        universe = await universe_service.top_stocks(db, market, limit)
    except AppError as exc:
        universe = None
        warnings.append(f"大型股排行暫時無法取得：{exc.message}")
    ranked = universe.stocks if universe else []
    indices = INDICES[market]
    entries = indices + [item.entry for item in ranked]

    # 先取日資料（限制同時請求數），報價的收盤備援就能直接使用快取
    histories = dict(zip((entry.key for entry in entries), await _load_histories(entries)))
    quotes = {result.entry.key: result for result in await quote_service.get_quotes(entries)}
    months = history_service.PERIOD_MONTHS[period]

    index_items = [_item(entry, quotes[entry.key], histories[entry.key], months) for entry in indices]
    stock_items = [
        _item(item.entry, quotes[item.entry.key], histories[item.entry.key], months, rank=rank, market_cap=item.market_cap)
        for rank, item in enumerate(ranked, start=1)
    ]
    return OverviewOut(
        market=market,
        period=period,
        market_open=session_for(market).is_open(clock.now()),
        indices=index_items,
        stocks=stock_items,
        ranking=RankingOut(method=universe.method, source=universe.source, as_of=universe.as_of, note=universe.note)
        if universe
        else None,
        history_source=history_service.SOURCE_NAMES[market],
        data_note="走勢為每日收盤價（非盤中），最後一點是最近已收盤的交易日；卡片上的價格是最新報價",
        warnings=warnings,
        fetched_at=clock.now(),
    )


async def get_overview(db: Session, market: str, period: str, limit: int, user: User | None) -> OverviewOut:
    overview = await cache.get_or_set(
        f"overview:{market}:{period}:{limit}", OVERVIEW_TTL_SECONDS, lambda: _build(db, market, period, limit)
    )
    # 取得新行情時同步檢查價格提醒（檢查所有人的提醒，只回傳自己的通知）
    quotes = [item.quote for item in overview.stocks if item.quote is not None]
    triggered = await alert_service.process_quotes(db, quotes, user)
    return overview.model_copy(update={"triggered_alerts": triggered})
