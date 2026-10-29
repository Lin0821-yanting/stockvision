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
    is_index: bool = False
    mis_symbol: str | None = None  # TWSE MIS 代碼和代號不同時使用，例如加權指數是 t00

    @property
    def key(self) -> str:
        return f"{self.market}:{self.symbol}"

    @property
    def currency(self) -> str:
        return "TWD" if self.market == "TW" else "USD"

    @property
    def mis_channel(self) -> tuple[str, str]:
        """TWSE MIS 的市場代碼：上市 tse、上櫃 otc。"""
        return ("otc" if self.exchange == "TPEx" else "tse", self.mis_symbol or self.symbol)
