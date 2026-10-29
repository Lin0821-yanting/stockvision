"""大盤總覽的回應結構。"""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.alert import AlertEventOut
from app.schemas.common import JsonDecimal
from app.schemas.stock import Market, Period, QuoteErrorOut, QuoteOut


class SparkPoint(BaseModel):
    date: date
    close: float


class OverviewItemOut(BaseModel):
    rank: int | None = Field(description="市值排名；指數為 null")
    symbol: str
    name: str
    exchange: str
    currency: Literal["TWD", "USD"]
    is_index: bool
    market_cap: JsonDecimal | None = Field(default=None, description="市值（當地貨幣），依排行資料日期計算")
    quote: QuoteOut | None = None
    quote_error: QuoteErrorOut | None = None
    points: list[SparkPoint] = Field(default=[], description="期間內每日收盤價（含期初基準日）")
    period_return_pct: float | None = Field(default=None, description="期間報酬率（%），以每日收盤價計算")
    history_end: date | None = Field(default=None, description="走勢最後一個交易日")
    history_error: str | None = None


class RankingOut(BaseModel):
    method: str
    source: str
    as_of: date | None = Field(description="排行使用的資料日期")
    note: str


class OverviewOut(BaseModel):
    market: Market
    period: Period
    market_open: bool
    indices: list[OverviewItemOut]
    stocks: list[OverviewItemOut]
    ranking: RankingOut | None = Field(description="排行暫時無法取得時為 null，原因寫在 warnings")
    history_source: str
    data_note: str
    warnings: list[str] = []
    fetched_at: datetime
    triggered_alerts: list[AlertEventOut] = Field(default=[], description="這次取得行情時新觸發的提醒")
