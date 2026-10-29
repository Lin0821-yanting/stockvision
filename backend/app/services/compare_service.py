"""多股比較：抓取各股歷史日資料（快取）與最新報價，交給 Pandas 對齊日期並標準化。"""

from __future__ import annotations

import asyncio

from sqlalchemy.orm import Session

from app.core import clock
from app.core.errors import InvalidRequestError
from app.schemas.compare import CompareOut, ComparePoint, CompareStockOut
from app.schemas.stock import QuoteErrorOut
from app.services import alert_service, analytics, history_service, quote_service
from app.services.entities import StockEntry

MIN_SYMBOLS = 2
MAX_SYMBOLS = 4
METHOD = "以所有股票都有交易的日期對齊（inner join），共同起始交易日的收盤價設為 100，標準化指數 = 當日收盤 ÷ 共同起始日收盤 × 100"


async def compare(db: Session, entries: list[StockEntry], period: str) -> CompareOut:
    if not MIN_SYMBOLS <= len(entries) <= MAX_SYMBOLS:
        raise InvalidRequestError(
            f"請選擇 {MIN_SYMBOLS} 到 {MAX_SYMBOLS} 檔不同的股票進行比較",
            details={"count": len(entries)},
        )

    dailies, quote_results = await asyncio.gather(
        asyncio.gather(*(history_service.get_daily_data(entry) for entry in entries)),
        quote_service.get_quotes(entries),
    )
    frames = {entry.symbol: daily.frame for entry, daily in zip(entries, dailies)}
    try:
        result = analytics.normalize_prices(frames, history_service.PERIOD_MONTHS[period])
    except ValueError as exc:
        raise InvalidRequestError(str(exc), details={"symbols": [entry.symbol for entry in entries]}) from exc

    quotes = {r.entry.symbol: r.quote for r in quote_results if r.quote is not None}
    errors = [
        QuoteErrorOut(symbol=r.entry.symbol, market=r.entry.market, code=r.error.code, message=r.error.message)
        for r in quote_results
        if r.quote is None and r.error is not None
    ]

    stocks = []
    for entry in entries:
        quote = quotes.get(entry.symbol)
        stocks.append(
            CompareStockOut(
                symbol=entry.symbol,
                market=entry.market,
                name=entry.name,
                exchange=entry.exchange,
                currency=entry.currency,
                latest_price=quote.price if quote else None,
                day_change_pct=quote.change_pct if quote else None,
                volume=quote.volume if quote else None,
                quote_kind=quote.kind if quote else None,
                quote_source=quote.source if quote else None,
                quote_as_of=quote.as_of if quote else None,
                start_close=round(float(result.closes[entry.symbol].iloc[0]), 4),
                end_close=round(float(result.closes[entry.symbol].iloc[-1]), 4),
                cumulative_return_pct=result.cumulative_return_pct[entry.symbol],
                max_drawdown_pct=result.max_drawdown_pct[entry.symbol],
                data_points=result.data_points[entry.symbol],
                excluded_dates=result.excluded_dates[entry.symbol],
            )
        )

    series = [
        ComparePoint(
            date=timestamp.date(),
            values={symbol: round(float(value), 4) for symbol, value in result.normalized.loc[timestamp].items()},
            closes={symbol: round(float(value), 4) for symbol, value in result.closes.loc[timestamp].items()},
        )
        for timestamp in result.closes.index
    ]

    triggered = await alert_service.process_quotes(db, list(quotes.values()))
    return CompareOut(
        period=period,
        symbols=[entry.symbol for entry in entries],
        common_start=result.common_start,
        common_end=result.common_end,
        aligned_points=len(series),
        method=METHOD,
        stocks=stocks,
        series=series,
        errors=errors,
        triggered_alerts=triggered,
        fetched_at=clock.now(),
    )
