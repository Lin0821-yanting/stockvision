"""股票查詢 API：搜尋、批次報價、個股資訊與歷史資料。"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_optional_user
from app.core.errors import AppError, InvalidRequestError, UpstreamError
from app.database.session import get_db
from app.models.user import User
from app.schemas.common import ERROR_RESPONSES
from app.schemas.stock import (
    HistoryOut,
    Market,
    Period,
    QuoteErrorOut,
    QuotesOut,
    StockDetailOut,
    StockInfoOut,
    StockSearchOut,
)
from app.schemas.compare import CompareOut
from app.services import alert_service, catalog_service, compare_service, history_service, quote_service
from app.services.entities import StockEntry

router = APIRouter(prefix="/api/stocks", tags=["股票資料"])

MAX_BATCH_SYMBOLS = 30
MARKET_NAMES = {"TW": "台股", "US": "美股"}


def stock_info(entry: StockEntry) -> StockInfoOut:
    return StockInfoOut(
        symbol=entry.symbol,
        market=entry.market,
        name=entry.name,
        exchange=entry.exchange,
        industry=entry.industry,
        currency=entry.currency,
    )


def split_symbols(symbols: str, *, limit: int = MAX_BATCH_SYMBOLS) -> list[str]:
    raw = list(dict.fromkeys(part.strip().upper() for part in symbols.split(",") if part.strip()))
    if not raw:
        raise InvalidRequestError("請至少提供一個股票代號")
    if len(raw) > limit:
        raise InvalidRequestError(f"一次最多 {limit} 檔股票", details={"count": len(raw), "limit": limit})
    return raw


async def resolve_many(db: Session, symbols: list[str]) -> tuple[list[StockEntry], list[QuoteErrorOut]]:
    entries: list[StockEntry] = []
    errors: list[QuoteErrorOut] = []
    for symbol in symbols:
        try:
            entries.append(await catalog_service.resolve(db, symbol))
        except AppError as exc:
            errors.append(QuoteErrorOut(symbol=symbol, code=exc.code, message=exc.message))
    return entries, errors


@router.get("/search", response_model=StockSearchOut, summary="搜尋股票名稱或代號", responses=ERROR_RESPONSES)
async def search_stocks(
    q: Annotated[str, Query(min_length=1, max_length=40, description="代號或名稱，例如 2330、台積電、AAPL")],
    market: Annotated[Market | None, Query(description="只搜尋台股（TW）或美股（US）")] = None,
    limit: Annotated[int, Query(ge=1, le=50)] = 20,
    db: Session = Depends(get_db),
) -> StockSearchOut:
    warnings: list[str] = []
    loaded: list[str] = []
    for item in [market] if market else ["TW", "US"]:
        try:
            await catalog_service.ensure_catalog(db, item)
            loaded.append(item)
        except UpstreamError as exc:
            warnings.append(f"{MARKET_NAMES[item]}清單暫時無法取得：{exc.message}")
    if not loaded:
        raise UpstreamError("股票清單暫時無法取得，請稍後再試", details={"warnings": warnings})
    results = catalog_service.search(db, q, markets=loaded, limit=limit)
    return StockSearchOut(query=q, results=[stock_info(entry) for entry in results], warnings=warnings)


@router.get("/quotes", response_model=QuotesOut, summary="批次取得最新報價（盤中或收盤）", responses=ERROR_RESPONSES)
async def get_quotes(
    symbols: Annotated[str, Query(description="以逗號分隔，例如 2330,2317,AAPL", examples=["2330,2317,AAPL"])],
    user: User | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> QuotesOut:
    entries, errors = await resolve_many(db, split_symbols(symbols))
    results = await quote_service.get_quotes(entries)
    quotes = [result.quote for result in results if result.quote is not None]
    errors += [
        QuoteErrorOut(symbol=r.entry.symbol, market=r.entry.market, code=r.error.code, message=r.error.message)
        for r in results
        if r.quote is None and r.error is not None
    ]
    # 取得新行情時同步檢查價格提醒（檢查所有人的提醒，只回傳自己的通知）
    triggered = await alert_service.process_quotes(db, quotes, user)
    return QuotesOut(quotes=quotes, errors=errors, triggered_alerts=triggered)


# 注意：/compare 必須宣告在 /{symbol} 之前，否則 "compare" 會被當成股票代號
@router.get(
    "/compare",
    response_model=CompareOut,
    summary="多股比較：標準化走勢與區間報酬（Pandas 計算）",
    responses=ERROR_RESPONSES,
)
async def compare_stocks(
    symbols: Annotated[str, Query(description="2 到 4 檔，以逗號分隔，例如 2330,2317,AAPL", examples=["2330,2317"])],
    period: Annotated[Period, Query(description="1M、3M、6M 或 1Y")] = "3M",
    user: User | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> CompareOut:
    raw = split_symbols(symbols, limit=compare_service.MAX_SYMBOLS)
    entries = [await catalog_service.resolve(db, symbol) for symbol in raw]
    unique = list({entry.key: entry for entry in entries}.values())  # 2330 與 2330.TW 視為同一檔
    return await compare_service.compare(db, unique, period, user)


@router.get("/{symbol}", response_model=StockDetailOut, summary="個股資訊與最新報價", responses=ERROR_RESPONSES)
async def get_stock(
    symbol: str, user: User | None = Depends(get_optional_user), db: Session = Depends(get_db)
) -> StockDetailOut:
    entry = await catalog_service.resolve(db, symbol)
    quote = await quote_service.get_quote(entry)
    low_20d, is_20d_low = await history_service.twenty_day_low(entry, quote)
    triggered = await alert_service.process_quotes(db, [quote], user)
    return StockDetailOut(
        stock=stock_info(entry),
        quote=quote,
        low_20d=low_20d,
        is_20d_low=is_20d_low,
        triggered_alerts=triggered,
    )


@router.get(
    "/{symbol}/history",
    response_model=HistoryOut,
    summary="歷史日資料與區間報酬（Pandas 計算）",
    responses=ERROR_RESPONSES,
)
async def get_history(
    symbol: str,
    period: Annotated[Period, Query(description="1M、3M、6M 或 1Y")] = "3M",
    db: Session = Depends(get_db),
) -> HistoryOut:
    entry = await catalog_service.resolve(db, symbol)
    return await history_service.get_history(entry, period)
