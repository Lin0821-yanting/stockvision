"""股票資料相關的回應結構。"""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.common import JsonDecimal

Market = Literal["TW", "US"]
Period = Literal["1M", "3M", "6M", "1Y"]


class StockInfoOut(BaseModel):
    symbol: str = Field(examples=["2330"])
    market: Market
    name: str = Field(examples=["台積電"])
    exchange: str = Field(description="TWSE（上市）、TPEx（上櫃）或 US", examples=["TWSE"])
    industry: str | None = None
    currency: Literal["TWD", "USD"]


class StockSearchOut(BaseModel):
    query: str
    results: list[StockInfoOut]
    source: str = "FinMind TaiwanStockInfo / USStockInfo（本機快取，每日更新）"
    warnings: list[str] = []


class QuoteOut(BaseModel):
    """一檔股票目前可取得的最新價格，並標示是盤中報價還是收盤資料。"""

    symbol: str
    market: Market
    name: str
    exchange: str
    currency: Literal["TWD", "USD"]
    price: JsonDecimal | None = Field(description="最新成交價或收盤價；當日尚無成交且無備援資料時為 null")
    change: JsonDecimal | None = None
    change_pct: JsonDecimal | None = None
    open: JsonDecimal | None = None
    high: JsonDecimal | None = None
    low: JsonDecimal | None = None
    prev_close: JsonDecimal | None = None
    volume: int | None = Field(default=None, description="成交量（股）")
    volume_note: str | None = None
    trade_date: date | None = Field(default=None, description="價格所屬的交易日（交易所當地日期）")
    as_of: datetime | None = Field(default=None, description="報價時間（交易所當地時區）")
    kind: Literal["realtime", "close"] = Field(description="realtime＝盤中報價；close＝收盤／最近交易日資料")
    source: str
    note: str | None = None
    market_open: bool
    fetched_at: datetime


class QuoteErrorOut(BaseModel):
    symbol: str
    market: Market | None = None
    code: str
    message: str


class QuotesOut(BaseModel):
    quotes: list[QuoteOut]
    errors: list[QuoteErrorOut] = []


class StockDetailOut(BaseModel):
    stock: StockInfoOut
    quote: QuoteOut
    low_20d: JsonDecimal | None = Field(default=None, description="前 20 個交易日的最低收盤價")
    is_20d_low: bool = Field(description="最新價格是否低於前 20 個交易日的最低收盤價（創 20 日新低）")


class PriceBar(BaseModel):
    date: date
    open: float
    high: float
    low: float
    close: float
    volume: int
    change: float | None
    change_pct: float | None


class HistoryStats(BaseModel):
    start_date: date | None
    end_date: date | None
    start_close: float | None
    end_close: float | None
    period_return_pct: float | None = Field(description="區間累積報酬率（%）")
    high: float | None
    low: float | None
    avg_volume: int | None
    trading_days: int


class HistoryOut(BaseModel):
    symbol: str
    market: Market
    name: str
    currency: Literal["TWD", "USD"]
    period: Period
    source: str
    data_note: str
    fetched_at: datetime
    bars: list[PriceBar]
    stats: HistoryStats
