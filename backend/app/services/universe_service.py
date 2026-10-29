"""大型股排行：台股依「已發行普通股數 × 收盤價」，美股依 FinMind 美股清單的市值。

排行每 12 小時重算一次；名次只用來決定大盤總覽要列哪幾家公司，報價與走勢另外即時取得。
"""

from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass, replace
from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.errors import UpstreamError
from app.core.market_hours import TAIPEI
from app.services import catalog_service, snapshot_service
from app.services.cache import cache
from app.services.entities import StockEntry
from app.services.providers import twse_openapi
from app.services.providers.base import DailySnapshot
from app.services.providers.twse_openapi import CompanyBasics

UNIVERSE_TTL_SECONDS = 12 * 60 * 60
MAX_RANKED = 30
US_CANDIDATES = 200

TW_METHOD = "已發行普通股數 × 收盤價"
TW_SOURCE = "TWSE OpenAPI t187ap03_L（已發行普通股數）、STOCK_DAY_ALL（收盤價）"
TW_NOTE = "只包含上市公司，不含上櫃、ETF 與 TDR；市值以資料日期的收盤價計算，不是即時市值"
US_METHOD = "FinMind 美股清單的市值（MarketCap）"
US_SOURCE = "FinMind USStockInfo"
US_NOTE = (
    "同一家公司的不同股票類別只列一次（例如 GOOGL／GOOG）；含在美國掛牌的 ADR（例如 TSM）；"
    "代號含「/」的股票（例如 BRK/B）目前無法查詢，因此不列入"
)

# 特別股、權證、債券等不是普通股的掛牌，市值欄位通常是整家公司的市值，會和普通股重複
_NOT_COMMON = re.compile(r"preferred|warrant|debenture|\bnotes?\b|\bunits?\b|\brights?\b", re.IGNORECASE)
# 公司名稱後面的股票類別說明，例如 "Alphabet Inc. Class C Capital Stock"
_SHARE_CLASS = re.compile(
    r"\s+(class\s+[a-z]\b|common|capital stock|ordinary|american depositary|depositary|new york registry|series\b).*$",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class RankedStock:
    entry: StockEntry
    market_cap: Decimal  # 當地貨幣：台股新台幣、美股美元


@dataclass(frozen=True)
class Universe:
    market: str
    stocks: list[RankedStock]
    method: str
    source: str
    as_of: date | None
    note: str


def company_key(name: str) -> str:
    """去掉股票類別後的公司名稱，用來合併同一家公司的不同掛牌。"""
    base = _SHARE_CLASS.sub("", name)
    return re.sub(r"[^a-z0-9&]+", " ", base.lower()).strip()


def rank_tw(companies: list[CompanyBasics], snapshots: dict[str, DailySnapshot]) -> list[RankedStock]:
    ranked: list[RankedStock] = []
    for company in companies:
        # 91 開頭是 TDR：原股股數 × TDR 價格不是公司市值
        if company.symbol.startswith("91"):
            continue
        snapshot = snapshots.get(company.symbol)
        if snapshot is None or snapshot.close is None or snapshot.close <= 0:
            continue
        entry = StockEntry("TW", company.symbol, company.short_name, "TWSE")
        ranked.append(RankedStock(entry, snapshot.close * company.shares))
    ranked.sort(key=lambda item: item.market_cap, reverse=True)
    return ranked


def rank_us(candidates: list[tuple[StockEntry, float]]) -> list[RankedStock]:
    """candidates 已依市值由大到小排序；同一家公司只保留市值最大的普通股。"""
    seen: set[str] = set()
    ranked: list[RankedStock] = []
    for entry, market_cap in candidates:
        if _NOT_COMMON.search(entry.name):
            continue
        key = company_key(entry.name)
        if key in seen:
            continue
        seen.add(key)
        ranked.append(RankedStock(entry, Decimal(str(market_cap))))
    return ranked


async def _load_tw() -> Universe:
    companies, snapshots = await asyncio.gather(twse_openapi.fetch_company_basics(), snapshot_service.twse_snapshots())
    ranked = rank_tw(companies, snapshots)[:MAX_RANKED]
    if not ranked:
        raise UpstreamError("證交所資料不完整，暫時無法計算台股市值排行", details={"source": twse_openapi.COMPANY_SOURCE})
    as_of = max(snapshots[item.entry.symbol].trade_date for item in ranked)
    return Universe("TW", ranked, TW_METHOD, TW_SOURCE, as_of, TW_NOTE)


async def _load_us(db: Session) -> Universe:
    await catalog_service.ensure_catalog(db, "US")
    if not catalog_service.has_market_caps(db, "US") and not cache.get("universe:us-refreshed"):
        # 加入大盤總覽前下載的清單沒有市值欄位：重新下載一次（12 小時內不重複）
        cache.set("universe:us-refreshed", True, UNIVERSE_TTL_SECONDS)
        await catalog_service.ensure_catalog(db, "US", force=True)
    ranked = rank_us(catalog_service.market_cap_leaders(db, "US", US_CANDIDATES))[:MAX_RANKED]
    if not ranked:
        raise UpstreamError("美股清單沒有市值資料，暫時無法排行", details={"source": US_SOURCE})
    refreshed = catalog_service.last_refresh(db, "US")
    as_of = refreshed.astimezone(TAIPEI).date() if refreshed else None
    return Universe("US", ranked, US_METHOD, US_SOURCE, as_of, US_NOTE)


async def top_stocks(db: Session, market: str, limit: int) -> Universe:
    if market == "TW":
        universe = await cache.get_or_set("universe:TW", UNIVERSE_TTL_SECONDS, _load_tw)
    else:
        universe = await cache.get_or_set("universe:US", UNIVERSE_TTL_SECONDS, lambda: _load_us(db))
    return replace(universe, stocks=universe.stocks[:limit])
