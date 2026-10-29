from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database.session import Base
from app.database.types import DecimalText, UTCDateTime, utcnow


class Account(Base):
    """模擬投資帳戶（本機單一使用者，id 固定為 1）。金額單位：新台幣。"""

    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(primary_key=True)
    base_currency: Mapped[str] = mapped_column(String(3), default="TWD")
    initial_cash: Mapped[Decimal] = mapped_column(DecimalText())
    cash: Mapped[Decimal] = mapped_column(DecimalText())
    # 每次重置帳戶 cycle + 1；舊的交易紀錄保留並標示所屬回合
    cycle: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utcnow)
    reset_at: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)


class Position(Base):
    """目前持股。avg_cost 為原幣每股平均成本，cost_basis_twd 為台幣總成本（含當時匯率）。"""

    __tablename__ = "positions"
    __table_args__ = (UniqueConstraint("account_id", "market", "symbol", name="uq_position_account_symbol"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"))
    market: Mapped[str] = mapped_column(String(4))
    symbol: Mapped[str] = mapped_column(String(16))
    name: Mapped[str] = mapped_column(String(200))
    exchange: Mapped[str] = mapped_column(String(16))
    currency: Mapped[str] = mapped_column(String(3))
    shares: Mapped[int] = mapped_column(Integer)
    avg_cost: Mapped[Decimal] = mapped_column(DecimalText())
    cost_basis_twd: Mapped[Decimal] = mapped_column(DecimalText())
    opened_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utcnow)


class Trade(Base):
    """每一筆模擬成交。手續費與證交稅欄位先固定為 0，保留日後擴充。"""

    __tablename__ = "trades"

    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"))
    cycle: Mapped[int] = mapped_column(Integer)
    market: Mapped[str] = mapped_column(String(4))
    symbol: Mapped[str] = mapped_column(String(16))
    name: Mapped[str] = mapped_column(String(200))
    side: Mapped[str] = mapped_column(String(4))  # BUY / SELL
    shares: Mapped[int] = mapped_column(Integer)
    price: Mapped[Decimal] = mapped_column(DecimalText())  # 原幣成交價
    currency: Mapped[str] = mapped_column(String(3))
    fx_rate: Mapped[Decimal] = mapped_column(DecimalText())  # 原幣 → 台幣（台股為 1）
    fx_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    gross_amount: Mapped[Decimal] = mapped_column(DecimalText())  # 原幣成交金額
    amount_twd: Mapped[Decimal] = mapped_column(DecimalText())
    fee_twd: Mapped[Decimal] = mapped_column(DecimalText(), default=Decimal("0"))
    tax_twd: Mapped[Decimal] = mapped_column(DecimalText(), default=Decimal("0"))
    realized_pnl_twd: Mapped[Decimal | None] = mapped_column(DecimalText(), nullable=True)
    cash_after_twd: Mapped[Decimal] = mapped_column(DecimalText())
    price_kind: Mapped[str] = mapped_column(String(10))  # realtime / close
    price_source: Mapped[str] = mapped_column(String(80))
    price_as_of: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utcnow)
