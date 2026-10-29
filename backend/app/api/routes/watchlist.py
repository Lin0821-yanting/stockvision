"""自選股 API：資料保存在 SQLite，查詢時附上最新報價。"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import ConflictError, NotFoundError
from app.core.symbols import parse_symbol
from app.database.session import get_db
from app.models.watchlist import WatchlistItem
from app.schemas.common import ERROR_RESPONSES
from app.schemas.stock import QuoteErrorOut
from app.schemas.watchlist import WatchlistCreate, WatchlistItemOut, WatchlistOut
from app.services import catalog_service, quote_service
from app.services.entities import StockEntry

router = APIRouter(prefix="/api/watchlist", tags=["自選股"])


def _entry(item: WatchlistItem) -> StockEntry:
    return StockEntry(market=item.market, symbol=item.symbol, name=item.name, exchange=item.exchange)


def _item_out(item: WatchlistItem, **extra) -> WatchlistItemOut:
    return WatchlistItemOut(
        id=item.id,
        symbol=item.symbol,
        market=item.market,
        name=item.name,
        exchange=item.exchange,
        currency=_entry(item).currency,
        added_at=item.created_at,
        **extra,
    )


@router.get("", response_model=WatchlistOut, summary="自選股清單（附最新報價）")
async def list_watchlist(
    with_quotes: Annotated[bool, Query(description="是否附上最新報價")] = True,
    db: Session = Depends(get_db),
) -> WatchlistOut:
    items = list(db.scalars(select(WatchlistItem).order_by(WatchlistItem.created_at, WatchlistItem.id)))
    if not with_quotes or not items:
        return WatchlistOut(items=[_item_out(item) for item in items])

    results = await quote_service.get_quotes([_entry(item) for item in items])
    by_key = {result.entry.key: result for result in results}
    out = []
    for item in items:
        result = by_key[_entry(item).key]
        error = None
        if result.quote is None and result.error is not None:
            error = QuoteErrorOut(symbol=item.symbol, market=item.market, code=result.error.code, message=result.error.message)
        out.append(_item_out(item, quote=result.quote, quote_error=error))
    return WatchlistOut(items=out)


@router.post(
    "",
    response_model=WatchlistItemOut,
    status_code=status.HTTP_201_CREATED,
    summary="加入自選股",
    responses=ERROR_RESPONSES,
)
async def add_watchlist(payload: WatchlistCreate, db: Session = Depends(get_db)) -> WatchlistItemOut:
    entry = await catalog_service.resolve(db, payload.symbol)
    exists = db.scalar(
        select(WatchlistItem).where(WatchlistItem.market == entry.market, WatchlistItem.symbol == entry.symbol)
    )
    if exists is not None:
        raise ConflictError(f"{entry.symbol} {entry.name} 已在自選股清單中", details={"symbol": entry.symbol})
    item = WatchlistItem(market=entry.market, symbol=entry.symbol, name=entry.name, exchange=entry.exchange)
    db.add(item)
    db.commit()
    db.refresh(item)
    return _item_out(item)


@router.delete(
    "/{symbol}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="移除自選股",
    responses=ERROR_RESPONSES,
)
def remove_watchlist(symbol: str, db: Session = Depends(get_db)) -> Response:
    ref = parse_symbol(symbol)
    item = db.scalar(select(WatchlistItem).where(WatchlistItem.market == ref.market, WatchlistItem.symbol == ref.symbol))
    if item is None:
        raise NotFoundError(f"{ref.symbol} 不在自選股清單中", details={"symbol": ref.symbol})
    db.delete(item)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
