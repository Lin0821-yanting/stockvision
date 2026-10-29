from __future__ import annotations

from datetime import datetime

from sqlalchemy import String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database.session import Base
from app.database.types import UTCDateTime, utcnow


class WatchlistItem(Base):
    """自選股（本機單一使用者）。"""

    __tablename__ = "watchlist_items"
    __table_args__ = (UniqueConstraint("market", "symbol", name="uq_watchlist_market_symbol"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    market: Mapped[str] = mapped_column(String(4))
    symbol: Mapped[str] = mapped_column(String(16))
    name: Mapped[str] = mapped_column(String(200))
    exchange: Mapped[str] = mapped_column(String(16))
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utcnow)
