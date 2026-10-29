"""股票代號解析：判斷台股或美股並正規化。"""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.core.errors import InvalidRequestError, SymbolNotFoundError

# 台股：數字開頭，例如 2330、0050、00400A
TW_PATTERN = re.compile(r"^\d[0-9A-Z]{1,6}$")
# 美股：英文字母開頭，例如 AAPL、BRK.B、BF-B
US_PATTERN = re.compile(r"^[A-Z][A-Z0-9]{0,5}([.\-][A-Z]{1,2})?$")

_SUFFIXES = ((".TWO", "TW"), (".TW", "TW"), (".US", "US"))


@dataclass(frozen=True)
class SymbolRef:
    market: str
    symbol: str

    @property
    def key(self) -> str:
        return f"{self.market}:{self.symbol}"


def parse_symbol(raw: str, market: str | None = None) -> SymbolRef:
    """'2330'、'2330.TW' → 台股；'aapl'、'AAPL.US' → 美股。"""
    text = raw.strip().upper()
    for suffix, suffix_market in _SUFFIXES:
        if text.endswith(suffix):
            text = text[: -len(suffix)]
            market = market or suffix_market
            break
    if not text:
        raise InvalidRequestError("請輸入股票代號")

    resolved_market = (market or ("TW" if text[0].isdigit() else "US")).upper()
    if resolved_market not in ("TW", "US"):
        raise InvalidRequestError("market 只能是 TW 或 US", details={"market": market})

    pattern = TW_PATTERN if resolved_market == "TW" else US_PATTERN
    if not pattern.match(text):
        raise SymbolNotFoundError(
            f"股票代號格式不正確：{raw}",
            details={"symbol": raw, "market": resolved_market},
        )
    return SymbolRef(resolved_market, text)
