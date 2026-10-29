"""服務層共用的資料結構。"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StockEntry:
    """一檔可以查詢的股票（來自本機股票清單）。"""

    market: str  # TW / US
    symbol: str
    name: str
    exchange: str  # TWSE / TPEx / US
    industry: str | None = None

    @property
    def key(self) -> str:
        return f"{self.market}:{self.symbol}"

    @property
    def currency(self) -> str:
        return "TWD" if self.market == "TW" else "USD"

    @property
    def mis_channel(self) -> tuple[str, str]:
        """TWSE MIS 的市場代碼：上市 tse、上櫃 otc。"""
        return ("otc" if self.exchange == "TPEx" else "tse", self.symbol)
