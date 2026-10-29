"""多股比較的回應結構。"""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.alert import AlertEventOut
from app.schemas.common import JsonDecimal
from app.schemas.stock import Market, Period, QuoteErrorOut


class ComparePoint(BaseModel):
    date: date
    values: dict[str, float] = Field(description="標準化指數（共同起始日 = 100），key 為股票代號")
    closes: dict[str, float] = Field(description="當日收盤價（各自原幣）")


class CompareStockOut(BaseModel):
    symbol: str
    market: Market
    name: str
    exchange: str
    currency: str
    latest_price: JsonDecimal | None
    day_change_pct: JsonDecimal | None
    volume: int | None
    quote_kind: Literal["realtime", "close"] | None
    quote_source: str | None
    quote_as_of: datetime | None
    start_close: float
    end_close: float
    cumulative_return_pct: float = Field(description="區間累積報酬率（%）＝ 期末指數 − 100")
    max_drawdown_pct: float = Field(description="區間最大回檔（%），由標準化指數計算")
    data_points: int
    excluded_dates: int = Field(description="因其他股票當天沒有交易而排除的日數")


class CompareOut(BaseModel):
    period: Period
    symbols: list[str]
    common_start: date
    common_end: date
    aligned_points: int
    method: str
    computed_by: str = "Python Pandas"
    stocks: list[CompareStockOut]
    series: list[ComparePoint]
    errors: list[QuoteErrorOut] = []
    triggered_alerts: list[AlertEventOut] = []
    fetched_at: datetime
