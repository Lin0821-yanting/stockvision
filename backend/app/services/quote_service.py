"""報價合併：盤中報價優先，拿不到時退回最近交易日收盤，並標示資料種類、時間與來源。

台股：TWSE MIS（盤中，約 5 秒更新）→ FinMind 日資料 → TWSE / TPEx OpenAPI
美股：Finnhub（需要 API Key）→ FinMind 日資料
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal

import pandas as pd

from app.core import clock
from app.core.config import get_settings
from app.core.errors import AppError, PriceUnavailableError, SymbolNotFoundError, UpstreamError
from app.core.market_hours import session_for
from app.core.money import quantize_price, to_decimal
from app.schemas.stock import QuoteOut
from app.services import history_service, snapshot_service
from app.services.cache import cache
from app.services.entities import StockEntry
from app.services.providers import finnhub, twse_mis
from app.services.providers.finnhub import FinnhubQuote
from app.services.providers.twse_mis import MisQuote

MIS_TTL_SECONDS = 5
MIS_MIN_INTERVAL_SECONDS = 2.0
MIS_RECENT_WINDOW_SECONDS = 120
MIS_BATCH_LIMIT = 40
FINNHUB_TTL_SECONDS = 15
REALTIME_MAX_AGE = timedelta(minutes=30)

# 最近被查詢過的台股；抓 MIS 時一併更新，其他頁面的請求就能直接使用快取
_recent_tw: dict[str, tuple[tuple[str, str], float]] = {}
_last_mis_call = 0.0


@dataclass
class QuoteResult:
    entry: StockEntry
    quote: QuoteOut | None = None
    error: AppError | None = None


def reset_state() -> None:
    """清除 MIS 批次狀態（測試用）。"""
    global _last_mis_call
    _recent_tw.clear()
    _last_mis_call = 0.0


def _change_pct(change: Decimal | None, base: Decimal | None) -> Decimal | None:
    if change is None or base is None or base == 0:
        return None
    return quantize_price(change / base * 100)


async def get_quotes(entries: list[StockEntry]) -> list[QuoteResult]:
    unique = list({entry.key: entry for entry in entries}.values())
    tw_results, us_results = await asyncio.gather(
        _tw_quotes([entry for entry in unique if entry.market == "TW"]),
        _us_quotes([entry for entry in unique if entry.market == "US"]),
    )
    results = {**tw_results, **us_results}
    return [results[entry.key] for entry in unique]


async def get_quote(entry: StockEntry) -> QuoteOut:
    [result] = await get_quotes([entry])
    if result.quote is None:
        raise result.error or PriceUnavailableError(f"目前無法取得 {entry.symbol} 的價格")
    return result.quote


# ---------------------------------------------------------------- 台股


async def _fetch_mis(entries: list[StockEntry]) -> dict[str, tuple[MisQuote, datetime]]:
    global _last_mis_call
    now_mono = time.monotonic()
    for stale in [s for s, (_, ts) in _recent_tw.items() if now_mono - ts > MIS_RECENT_WINDOW_SECONDS]:
        _recent_tw.pop(stale, None)
    for entry in entries:
        _recent_tw[entry.symbol] = (entry.mis_channel, now_mono)

    def cached(symbol: str):
        return cache.get(f"mis:{symbol}")

    missing = [entry.symbol for entry in entries if cached(entry.symbol) is None]
    if missing:
        async with cache.lock("mis"):
            still_missing = [symbol for symbol in missing if cached(symbol) is None]
            if still_missing:
                extra = [channel for symbol, (channel, _) in _recent_tw.items() if symbol not in still_missing]
                channels = ([_recent_tw[symbol][0] for symbol in still_missing] + extra)[:MIS_BATCH_LIMIT]
                wait = MIS_MIN_INTERVAL_SECONDS - (time.monotonic() - _last_mis_call)
                if wait > 0:
                    await asyncio.sleep(wait)
                try:
                    quotes = await twse_mis.fetch_quotes(channels)
                finally:
                    _last_mis_call = time.monotonic()
                fetched_at = clock.now()
                for symbol, quote in quotes.items():
                    cache.set(f"mis:{symbol}", (quote, fetched_at), MIS_TTL_SECONDS)

    return {entry.symbol: cached(entry.symbol) for entry in entries if cached(entry.symbol) is not None}


def _from_mis(entry: StockEntry, mis: MisQuote, fetched_at: datetime, now: datetime) -> QuoteOut:
    session = session_for("TW")
    market_open = session.is_open(now)
    is_today = mis.trade_date == session.today(now)
    realtime = market_open and is_today
    change = mis.price - mis.prev_close if mis.price is not None and mis.prev_close else None
    if realtime:
        note = None
    elif is_today:
        note = "今日收盤（TWSE MIS）"
    else:
        note = "最近交易日收盤（TWSE MIS）"
    return QuoteOut(
        symbol=entry.symbol,
        market="TW",
        name=entry.name,
        exchange=entry.exchange,
        currency="TWD",
        price=mis.price,
        change=change,
        change_pct=_change_pct(change, mis.prev_close),
        open=mis.open,
        high=mis.high,
        low=mis.low,
        prev_close=mis.prev_close,
        volume=mis.volume,
        trade_date=mis.trade_date,
        as_of=mis.trade_time,
        kind="realtime" if realtime else "close",
        source=twse_mis.SOURCE,
        note=note,
        market_open=market_open,
        fetched_at=fetched_at,
    )


async def _tw_quotes(entries: list[StockEntry]) -> dict[str, QuoteResult]:
    if not entries:
        return {}
    now = clock.now()
    session = session_for("TW")
    try:
        mis_quotes = await _fetch_mis(entries)
        mis_failed = False
    except UpstreamError:
        mis_quotes, mis_failed = {}, True

    results: dict[str, QuoteResult] = {}
    fallbacks: list[tuple[StockEntry, str]] = []
    for entry in entries:
        item = mis_quotes.get(entry.symbol)
        mis = item[0] if item else None
        if mis is not None and mis.price is not None and mis.trade_date is not None:
            results[entry.key] = QuoteResult(entry, _from_mis(entry, mis, item[1], now))
            continue
        if mis_failed:
            note = "盤中報價（TWSE MIS）暫時無法取得，顯示最近交易日收盤"
        elif mis is not None and mis.trade_date == session.today(now) and session.is_open(now):
            note = "今日尚無成交，顯示前一交易日收盤"
        else:
            note = "沒有盤中報價，顯示最近交易日收盤"
        fallbacks.append((entry, note))

    if fallbacks:
        done = await asyncio.gather(*(_daily_quote(entry, note, now) for entry, note in fallbacks))
        for (entry, _), result in zip(fallbacks, done):
            results[entry.key] = result
    return results


# ---------------------------------------------------------------- 美股


async def _finnhub_cached(symbol: str) -> tuple[FinnhubQuote | None, datetime]:
    async def load() -> tuple[FinnhubQuote | None, datetime]:
        return await finnhub.fetch_quote(symbol), clock.now()

    return await cache.get_or_set(f"finnhub:{symbol}", FINNHUB_TTL_SECONDS, load)


async def _from_finnhub(entry: StockEntry, quote: FinnhubQuote, fetched_at: datetime, now: datetime) -> QuoteOut:
    session = session_for("US")
    market_open = session.is_open(now)
    realtime = market_open and now - quote.as_of <= REALTIME_MAX_AGE
    as_of = quote.as_of.astimezone(session.timezone)
    change = quote.change
    if change is None and quote.prev_close:
        change = quote.price - quote.prev_close

    volume = volume_note = None
    try:
        daily = await history_service.get_daily_data(entry)
        if not daily.frame.empty:
            last = daily.frame.iloc[-1]
            volume = int(last.volume)
            volume_note = f"Finnhub 報價不含成交量，此為 {last.date.date()} 的日成交量（FinMind）"
    except AppError:
        volume_note = "Finnhub 報價不含成交量"

    return QuoteOut(
        symbol=entry.symbol,
        market="US",
        name=entry.name,
        exchange=entry.exchange,
        currency="USD",
        price=quote.price,
        change=change,
        change_pct=quote.change_pct if quote.change_pct is not None else _change_pct(change, quote.prev_close),
        open=quote.open,
        high=quote.high,
        low=quote.low,
        prev_close=quote.prev_close,
        volume=volume,
        volume_note=volume_note,
        trade_date=as_of.date(),
        as_of=as_of,
        kind="realtime" if realtime else "close",
        source=finnhub.SOURCE,
        note=None if realtime else "美股目前非交易時段，顯示最近成交價（Finnhub）",
        market_open=market_open,
        fetched_at=fetched_at,
    )


async def _us_quotes(entries: list[StockEntry]) -> dict[str, QuoteResult]:
    if not entries:
        return {}
    now = clock.now()
    results: dict[str, QuoteResult] = {}
    fallbacks: list[tuple[StockEntry, str]] = []

    if get_settings().finnhub_configured:
        fetched = await asyncio.gather(*(_finnhub_cached(entry.symbol) for entry in entries), return_exceptions=True)
        for entry, item in zip(entries, fetched):
            if isinstance(item, BaseException):
                fallbacks.append((entry, "Finnhub 暫時無法取得報價，顯示最近交易日收盤"))
            elif item[0] is None:
                fallbacks.append((entry, "Finnhub 查無此代號的報價，顯示最近交易日收盤"))
            else:
                results[entry.key] = QuoteResult(entry, await _from_finnhub(entry, item[0], item[1], now))
    else:
        fallbacks = [(entry, "未設定 Finnhub API Key，美股顯示最近交易日收盤（非即時）") for entry in entries]

    if fallbacks:
        done = await asyncio.gather(*(_daily_quote(entry, note, now) for entry, note in fallbacks))
        for (entry, _), result in zip(fallbacks, done):
            results[entry.key] = result
    return results


# ---------------------------------------------------------------- 日資料備援


def _decimal(value: float) -> Decimal | None:
    return None if pd.isna(value) else to_decimal(float(value))


async def _daily_quote(entry: StockEntry, note: str, now: datetime) -> QuoteResult:
    session = session_for(entry.market)
    market_open = session.is_open(now)
    try:
        daily = await history_service.get_daily_data(entry)
        if daily.frame.empty:
            raise SymbolNotFoundError(f"{entry.symbol} 沒有可用的價格資料", details={"symbol": entry.symbol})
    except AppError as exc:
        if entry.market == "TW":
            snapshot_result = await _snapshot_quote(entry, note, now)
            if snapshot_result is not None:
                return snapshot_result
        return QuoteResult(entry, error=exc)

    frame = daily.frame
    last = frame.iloc[-1]
    price = _decimal(last.close)
    prev_close = _decimal(frame.iloc[-2].close) if len(frame) > 1 else None
    change = price - prev_close if price is not None and prev_close is not None else None
    trade_date = last.date.date()
    return QuoteResult(
        entry,
        QuoteOut(
            symbol=entry.symbol,
            market=entry.market,
            name=entry.name,
            exchange=entry.exchange,
            currency=entry.currency,
            price=price,
            change=change,
            change_pct=_change_pct(change, prev_close),
            open=_decimal(last.open),
            high=_decimal(last.high),
            low=_decimal(last.low),
            prev_close=prev_close,
            volume=int(last.volume),
            trade_date=trade_date,
            as_of=session.close_datetime(trade_date),
            kind="close",
            source=history_service.SOURCE_NAMES[entry.market],
            note=note,
            market_open=market_open,
            fetched_at=daily.fetched_at,
        ),
    )


async def _snapshot_quote(entry: StockEntry, note: str, now: datetime) -> QuoteResult | None:
    try:
        snapshot = await snapshot_service.find_snapshot(entry)
    except AppError:
        return None
    if snapshot is None or snapshot.close is None:
        return None
    session = session_for("TW")
    prev_close = snapshot.close - snapshot.change if snapshot.change is not None else None
    return QuoteResult(
        entry,
        QuoteOut(
            symbol=entry.symbol,
            market="TW",
            name=entry.name,
            exchange=entry.exchange,
            currency="TWD",
            price=snapshot.close,
            change=snapshot.change,
            change_pct=_change_pct(snapshot.change, prev_close),
            open=snapshot.open,
            high=snapshot.high,
            low=snapshot.low,
            prev_close=prev_close,
            volume=snapshot.volume,
            trade_date=snapshot.trade_date,
            as_of=session.close_datetime(snapshot.trade_date),
            kind="close",
            source=snapshot.source,
            note=note,
            market_open=session.is_open(now),
            fetched_at=now,
        ),
    )
