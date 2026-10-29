"""市況與匯率的回應結構。"""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel

from app.schemas.common import JsonDecimal


class MarketSessionOut(BaseModel):
    market: Literal["TW", "US"]
    name: str
    state: Literal["open", "pre_open", "closed"]
    label: str
    is_open: bool
    local_time: datetime
    timezone: str
    session: str
    session_taipei: str
    note: str


class MarketStatusOut(BaseModel):
    markets: list[MarketSessionOut]
    server_time: datetime


class FxRateOut(BaseModel):
    pair: str = "USD/TWD"
    rate: JsonDecimal
    spot_buy: JsonDecimal
    spot_sell: JsonDecimal
    rate_date: date
    source: str
    note: str
    fetched_at: datetime
