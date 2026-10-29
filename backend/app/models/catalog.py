from __future__ import annotations

from datetime import datetime

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.session import Base
from app.database.types import UTCDateTime


class StockCatalog(Base):
    """股票清單快取（來自 FinMind TaiwanStockInfo / USStockInfo），搜尋時只查這張表。"""

    __tablename__ = "stock_catalog"

    market: Mapped[str] = mapped_column(String(4), primary_key=True)
    symbol: Mapped[str] = mapped_column(String(16), primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    exchange: Mapped[str] = mapped_column(String(16))
    industry: Mapped[str | None] = mapped_column(String(120), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime())
