from __future__ import annotations

from datetime import datetime

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database.session import Base
from app.database.types import UTCDateTime, utcnow


class WatchlistItem(Base):
    """自選股，每位使用者各自一份。"""

    __tablename__ = "watchlist_items"
    __table_args__ = (UniqueConstraint("user_id", "market", "symbol", name="uq_watchlist_user_symbol"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    market: Mapped[str] = mapped_column(String(4))
    symbol: Mapped[str] = mapped_column(String(16))
    name: Mapped[str] = mapped_column(String(200))
    exchange: Mapped[str] = mapped_column(String(16))
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utcnow)
