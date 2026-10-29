"""價格提醒與站內通知的請求與回應結構。"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from app.schemas.common import JsonDecimal

Condition = Literal["PRICE_LTE", "PRICE_GTE", "NEW_20D_LOW"]
TriggerMode = Literal["ONCE", "EVERY_CROSS"]
AlertStatus = Literal["monitoring", "triggered", "disabled"]


def _check_target(condition: str | None, target: Decimal | None) -> None:
    if condition in ("PRICE_LTE", "PRICE_GTE") and target is None:
        raise ValueError("價格條件需要設定目標價格")


class AlertCreate(BaseModel):
    symbol: str = Field(min_length=1, max_length=20, examples=["2330"])
    condition: Condition = Field(description="PRICE_LTE（≤ 目標價）、PRICE_GTE（≥ 目標價）、NEW_20D_LOW（創 20 日新低）")
    target_price: Decimal | None = Field(default=None, gt=0, max_digits=14, decimal_places=4, examples=[900])
    trigger_mode: TriggerMode = Field(default="ONCE", description="ONCE＝觸發後自動停用；EVERY_CROSS＝每次條件由不成立變成立都通知")
    note: str | None = Field(default=None, max_length=200)

    @model_validator(mode="after")
    def target_required(self) -> AlertCreate:
        _check_target(self.condition, self.target_price)
        if self.condition == "NEW_20D_LOW":
            self.target_price = None
        return self


class AlertUpdate(BaseModel):
    condition: Condition | None = None
    target_price: Decimal | None = Field(default=None, gt=0, max_digits=14, decimal_places=4)
    trigger_mode: TriggerMode | None = None
    is_active: bool | None = None
    note: str | None = Field(default=None, max_length=200)


class AlertEventOut(BaseModel):
    id: int
    alert_id: int | None
    symbol: str
    market: str
    name: str
    condition: Condition
    condition_label: str
    target_price: JsonDecimal | None
    triggered_price: JsonDecimal
    reference_low: JsonDecimal | None
    price_kind: Literal["realtime", "close"]
    price_source: str
    price_as_of: datetime | None
    message: str
    triggered_at: datetime
    read_at: datetime | None


class AlertOut(BaseModel):
    id: int
    symbol: str
    market: str
    name: str
    exchange: str
    currency: str
    condition: Condition
    condition_label: str
    target_price: JsonDecimal | None
    trigger_mode: TriggerMode
    is_active: bool
    status: AlertStatus
    status_label: str
    note: str | None
    last_condition_met: bool
    last_checked_at: datetime | None
    last_checked_price: JsonDecimal | None
    last_price_kind: Literal["realtime", "close"] | None
    last_triggered_at: datetime | None
    trigger_count: int
    created_at: datetime
    updated_at: datetime


class MonitorStatusOut(BaseModel):
    enabled: bool
    interval_seconds: int
    running: bool
    last_run_at: datetime | None
    last_result: str
    next_run_at: datetime | None
    markets_open: list[str]
    explanation: str


class AlertListOut(BaseModel):
    alerts: list[AlertOut]
    monitor: MonitorStatusOut


class AlertMutationOut(BaseModel):
    alert: AlertOut
    triggered: list[AlertEventOut] = []


class AlertCheckOut(BaseModel):
    checked_alerts: int
    checked_symbols: int
    triggered: list[AlertEventOut]
    errors: list[str]
    checked_at: datetime


class NotificationsOut(BaseModel):
    items: list[AlertEventOut]
    unread_count: int


class ReadAllOut(BaseModel):
    updated: int
