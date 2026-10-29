"""股票清單：從 FinMind 下載台股與美股清單後存進 SQLite，搜尋與代號解析都查本機資料。"""

from __future__ import annotations

import logging
import re
from collections.abc import Callable, Iterable
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import delete, insert, select
from sqlalchemy.orm import Session

from app.core import clock
from app.core.errors import AppError, SymbolNotFoundError, UpstreamError
from app.core.symbols import US_PATTERN, parse_symbol
from app.models.catalog import StockCatalog
from app.services import history_service, snapshot_service
from app.services.cache import cache
from app.services.entities import StockEntry
from app.services.providers import finmind

logger = logging.getLogger("stockvision.catalog")

CATALOG_TTL = timedelta(hours=24)
RETRY_AFTER_FAILURE_SECONDS = 10 * 60
_US_NAME_SUFFIX = re.compile(r"\s+(Common Stock|Ordinary Shares|Common Shares)\s*$", re.IGNORECASE)


def _latest_rows(rows: Iterable[dict[str, Any]], accept: Callable[[str, dict[str, Any]], bool]) -> dict[str, dict[str, Any]]:
    """同一個代號可能出現多次（不同日期或產業分類），保留日期最新的一筆。"""
    latest: dict[str, dict[str, Any]] = {}
    for row in rows:
        symbol = str(row.get("stock_id", "")).strip().upper()
        if not symbol or not accept(symbol, row):
            continue
        current = latest.get(symbol)
        if current is None or str(row.get("date", "")) >= str(current.get("date", "")):
            latest[symbol] = row
    return latest


def parse_taiwan_info(rows: Iterable[dict[str, Any]]) -> list[StockEntry]:
    latest = _latest_rows(
        rows,
        lambda symbol, row: symbol[0].isdigit() and str(row.get("type", "")).lower() in ("twse", "tpex"),
    )
    return [
        StockEntry(
            market="TW",
            symbol=symbol,
            name=str(row.get("stock_name") or "").strip() or symbol,
            exchange="TPEx" if str(row.get("type")).lower() == "tpex" else "TWSE",
            industry=str(row.get("industry_category") or "").strip() or None,
        )
        for symbol, row in latest.items()
    ]


def parse_us_info(rows: Iterable[dict[str, Any]]) -> list[StockEntry]:
    latest = _latest_rows(rows, lambda symbol, _row: bool(US_PATTERN.match(symbol)))
    return [
        StockEntry(
            market="US",
            symbol=symbol,
            name=_US_NAME_SUFFIX.sub("", str(row.get("stock_name") or "").strip()) or symbol,
            exchange="US",
            industry=str(row.get("Subsector") or "").strip() or None,
        )
        for symbol, row in latest.items()
    ]


def _last_refresh(db: Session, market: str) -> datetime | None:
    return db.scalar(
        select(StockCatalog.updated_at)
        .where(StockCatalog.market == market)
        .order_by(StockCatalog.updated_at.desc())
        .limit(1)
    )


def _is_fresh(last: datetime | None) -> bool:
    return last is not None and clock.now() - last < CATALOG_TTL


async def ensure_catalog(db: Session, market: str) -> None:
    """清單不存在或超過 24 小時才向 FinMind 重新下載；下載失敗但已有舊清單時沿用舊清單。"""
    if _is_fresh(_last_refresh(db, market)):
        return
    async with cache.lock(f"catalog:{market}"):
        last = _last_refresh(db, market)
        if _is_fresh(last) or (last is not None and cache.get(f"catalog-retry:{market}")):
            return
        try:
            rows = await (finmind.taiwan_stock_info() if market == "TW" else finmind.us_stock_info())
            entries = parse_taiwan_info(rows) if market == "TW" else parse_us_info(rows)
            if not entries:
                raise UpstreamError("FinMind 回傳的股票清單是空的", details={"source": "FinMind"})
        except UpstreamError:
            if last is None:
                raise
            logger.warning("Refreshing %s stock list failed; keep using the cached list", market)
            cache.set(f"catalog-retry:{market}", True, RETRY_AFTER_FAILURE_SECONDS)
            return

        now = clock.now()
        db.execute(delete(StockCatalog).where(StockCatalog.market == market))
        db.execute(
            insert(StockCatalog),
            [
                {
                    "market": entry.market,
                    "symbol": entry.symbol,
                    "name": entry.name,
                    "exchange": entry.exchange,
                    "industry": entry.industry,
                    "updated_at": now,
                }
                for entry in entries
            ],
        )
        db.commit()


def _to_entry(row: StockCatalog) -> StockEntry:
    return StockEntry(
        market=row.market,
        symbol=row.symbol,
        name=row.name,
        exchange=row.exchange,
        industry=row.industry,
    )


def _escape_like(text: str) -> str:
    return text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def search(db: Session, query: str, markets: list[str], limit: int = 20) -> list[StockEntry]:
    """代號完全相符 > 代號開頭相符 > 名稱開頭相符 > 名稱包含；同分時台股優先。"""
    text = query.strip()
    if not text or not markets:
        return []
    upper = text.upper()
    base = select(StockCatalog).where(StockCatalog.market.in_(markets))
    statements = (
        base.where(StockCatalog.symbol == upper),
        base.where(StockCatalog.symbol.like(f"{_escape_like(upper)}%", escape="\\")).limit(60),
        base.where(StockCatalog.name.like(f"%{_escape_like(text)}%", escape="\\")).limit(120),
    )
    found: dict[tuple[str, str], StockCatalog] = {}
    for statement in statements:
        for row in db.scalars(statement):
            found.setdefault((row.market, row.symbol), row)

    def rank(row: StockCatalog) -> tuple:
        name = row.name.upper()
        if row.symbol == upper:
            score = 0
        elif row.symbol.startswith(upper):
            score = 1
        elif name.startswith(upper):
            score = 2
        else:
            score = 3
        return score, 0 if row.market == "TW" else 1, len(row.symbol), row.symbol

    return [_to_entry(row) for row in sorted(found.values(), key=rank)[:limit]]


async def resolve(db: Session, raw_symbol: str, market: str | None = None) -> StockEntry:
    """把使用者輸入的代號轉成清單中的股票；找不到時丟出 SymbolNotFoundError。"""
    ref = parse_symbol(raw_symbol, market)
    try:
        await ensure_catalog(db, ref.market)
    except UpstreamError:
        # FinMind 無法使用時，台股改用官方 OpenAPI 快照辨識代號，盤中報價仍可運作
        if ref.market == "TW":
            try:
                found = await snapshot_service.find_by_symbol(ref.symbol)
            except AppError:
                found = None
            if found is not None:
                exchange, snapshot = found
                return StockEntry("TW", ref.symbol, snapshot.name or ref.symbol, exchange)
        raise

    row = db.get(StockCatalog, (ref.market, ref.symbol))
    if row is not None:
        return _to_entry(row)

    if ref.market == "US":
        # ETF 等不在 USStockInfo 清單中的代號：FinMind 有價格資料才接受
        candidate = StockEntry("US", ref.symbol, ref.symbol, "US")
        try:
            daily = await history_service.get_daily_data(candidate)
        except AppError:
            daily = None
        if daily is not None and not daily.frame.empty:
            return candidate

    raise SymbolNotFoundError(
        f"找不到股票代號 {ref.symbol}",
        details={"symbol": ref.symbol, "market": ref.market},
    )
