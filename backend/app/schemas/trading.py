"""模擬交易、帳戶與投資組合的請求與回應結構。"""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.common import JsonDecimal
from app.schemas.market import FxRateOut
from app.schemas.stock import Market

DISCLAIMER = "模擬成交，不代表真實市場價格或成交"

Side = Literal["BUY", "SELL"]


class TradeRequest(BaseModel):
    symbol: str = Field(min_length=1, max_length=20, examples=["2330"])
    side: Side = Field(examples=["BUY"])
    shares: int = Field(gt=0, le=10_000_000, description="股數（台股 1 張 = 1,000 股，可下零股）", examples=[1000])


class AccountOut(BaseModel):
    id: int
    base_currency: str
    initial_cash: JsonDecimal
    cash: JsonDecimal
    cycle: int
    created_at: datetime
    reset_at: datetime | None


class TradeOut(BaseModel):
    id: int
    cycle: int
    symbol: str
    market: Market
    name: str
    side: Side
    shares: int
    price: JsonDecimal
    currency: str
    fx_rate: JsonDecimal
    fx_date: date | None
    gross_amount: JsonDecimal
    amount_twd: JsonDecimal
    fee_twd: JsonDecimal
    tax_twd: JsonDecimal
    realized_pnl_twd: JsonDecimal | None
    cash_after_twd: JsonDecimal
    price_kind: Literal["realtime", "close"]
    price_source: str
    price_as_of: datetime | None
    created_at: datetime


class TradePreviewOut(BaseModel):
    symbol: str
    market: Market
    name: str
    side: Side
    shares: int
    price: JsonDecimal
    currency: str
    price_kind: Literal["realtime", "close"]
    price_source: str
    price_as_of: datetime | None
    fx_rate: JsonDecimal
    fx_date: date | None
    gross_amount: JsonDecimal
    amount_twd: JsonDecimal
    fee_twd: JsonDecimal
    tax_twd: JsonDecimal
    cash_before: JsonDecimal
    cash_after: JsonDecimal | None
    shares_held: int
    shares_after: int | None
    estimated_realized_pnl_twd: JsonDecimal | None = None
    can_execute: bool
    reason: str | None = None
    reason_code: str | None = None
    disclaimer: str = DISCLAIMER


class TradeResultOut(BaseModel):
    message: str
    trade: TradeOut
    account: AccountOut
    disclaimer: str = DISCLAIMER


class TradeListOut(BaseModel):
    scope: Literal["current", "all"]
    current_cycle: int
    trades: list[TradeOut]


class PositionOut(BaseModel):
    symbol: str
    market: Market
    name: str
    exchange: str
    currency: str
    shares: int
    avg_cost: JsonDecimal
    cost_basis_twd: JsonDecimal
    current_price: JsonDecimal | None
    day_change_pct: JsonDecimal | None
    price_kind: Literal["realtime", "close"] | None
    price_source: str | None
    price_as_of: datetime | None
    fx_rate: JsonDecimal | None
    market_value: JsonDecimal | None = Field(description="原幣市值")
    market_value_twd: JsonDecimal | None
    unrealized_pnl_twd: JsonDecimal | None
    unrealized_pnl_pct: JsonDecimal | None
    realized_pnl_twd: JsonDecimal = Field(description="本輪已實現損益（台幣）")
    weight_pct: JsonDecimal | None = Field(description="占持股總市值比例")
    quote_error: str | None = None


class PortfolioOut(BaseModel):
    account: AccountOut
    positions: list[PositionOut]
    cash_twd: JsonDecimal
    market_value_twd: JsonDecimal
    cost_basis_twd: JsonDecimal
    unrealized_pnl_twd: JsonDecimal
    realized_pnl_twd: JsonDecimal
    total_assets_twd: JsonDecimal
    total_pnl_twd: JsonDecimal
    roi_pct: JsonDecimal | None
    fx: FxRateOut | None
    incomplete: bool = Field(description="有持股暫時取不到價格時為 true，總市值可能低估")
    warnings: list[str]
    as_of: datetime
    disclaimer: str = DISCLAIMER


class ResetOut(BaseModel):
    message: str
    account: AccountOut
