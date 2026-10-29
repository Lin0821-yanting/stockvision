"""自選股的請求與回應結構。"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.stock import Market, QuoteErrorOut, QuoteOut


class WatchlistCreate(BaseModel):
    symbol: str = Field(min_length=1, max_length=20, examples=["2330", "AAPL"])


class WatchlistItemOut(BaseModel):
    id: int
    symbol: str
    market: Market
    name: str
    exchange: str
    currency: str
    added_at: datetime
    quote: QuoteOut | None = None
    quote_error: QuoteErrorOut | None = None


class WatchlistOut(BaseModel):
    items: list[WatchlistItemOut]
