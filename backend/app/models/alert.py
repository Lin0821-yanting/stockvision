from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.session import Base
from app.database.types import DecimalText, UTCDateTime, utcnow


class Alert(Base):
    """價格提醒條件。"""

    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    market: Mapped[str] = mapped_column(String(4))
    symbol: Mapped[str] = mapped_column(String(16))
    name: Mapped[str] = mapped_column(String(200))
    exchange: Mapped[str] = mapped_column(String(16))
    condition: Mapped[str] = mapped_column(String(16))  # PRICE_LTE / PRICE_GTE / NEW_20D_LOW
    target_price: Mapped[Decimal | None] = mapped_column(DecimalText(), nullable=True)
    trigger_mode: Mapped[str] = mapped_column(String(12), default="ONCE")  # ONCE / EVERY_CROSS
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    note: Mapped[str | None] = mapped_column(String(200), nullable=True)
    # 上一次檢查時條件是否成立：只有「不成立 → 成立」才會觸發，避免每次輪詢重複通知
    last_condition_met: Mapped[bool] = mapped_column(Boolean, default=False)
    last_checked_at: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)
    last_checked_price: Mapped[Decimal | None] = mapped_column(DecimalText(), nullable=True)
    last_price_kind: Mapped[str | None] = mapped_column(String(10), nullable=True)
    last_triggered_at: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)
    trigger_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utcnow)


class AlertEvent(Base):
    """提醒觸發紀錄，同時作為站內通知（read_at 為已讀時間）。提醒被刪除後紀錄仍保留。"""

    __tablename__ = "alert_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    alert_id: Mapped[int | None] = mapped_column(ForeignKey("alerts.id", ondelete="SET NULL"), nullable=True)
    market: Mapped[str] = mapped_column(String(4))
    symbol: Mapped[str] = mapped_column(String(16))
    name: Mapped[str] = mapped_column(String(200))
    condition: Mapped[str] = mapped_column(String(16))
    target_price: Mapped[Decimal | None] = mapped_column(DecimalText(), nullable=True)
    triggered_price: Mapped[Decimal] = mapped_column(DecimalText())
    reference_low: Mapped[Decimal | None] = mapped_column(DecimalText(), nullable=True)
    price_kind: Mapped[str] = mapped_column(String(10))
    price_source: Mapped[str] = mapped_column(String(80))
    price_as_of: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)
    message: Mapped[str] = mapped_column(String(400))
    triggered_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utcnow)
    read_at: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)
