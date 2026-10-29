"""官方 OpenAPI 全市場日行情快照（快取 10 分鐘），在 FinMind 無法使用時當作台股收盤備援。"""

from __future__ import annotations

from app.services.cache import cache
from app.services.entities import StockEntry
from app.services.providers import tpex_openapi, twse_openapi
from app.services.providers.base import DailySnapshot

SNAPSHOT_TTL_SECONDS = 10 * 60


async def twse_snapshots() -> dict[str, DailySnapshot]:
    return await cache.get_or_set("snapshot:twse", SNAPSHOT_TTL_SECONDS, twse_openapi.fetch_stock_day_all)


async def tpex_snapshots() -> dict[str, DailySnapshot]:
    return await cache.get_or_set("snapshot:tpex", SNAPSHOT_TTL_SECONDS, tpex_openapi.fetch_daily_close)


async def find_snapshot(entry: StockEntry) -> DailySnapshot | None:
    snapshots = await (tpex_snapshots() if entry.exchange == "TPEx" else twse_snapshots())
    return snapshots.get(entry.symbol)


async def find_by_symbol(symbol: str) -> tuple[str, DailySnapshot] | None:
    """在上市、上櫃快照中尋找代號，回傳（交易所, 快照）。"""
    for exchange, loader in (("TWSE", twse_snapshots), ("TPEx", tpex_snapshots)):
        snapshot = (await loader()).get(symbol)
        if snapshot is not None:
            return exchange, snapshot
    return None
