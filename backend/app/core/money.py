"""金額與價格的 Decimal 工具。

外部 API 回傳的浮點數一律先轉成字串再轉 Decimal，避免 0.1 + 0.2 這類浮點誤差。
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from typing import Any

CENT = Decimal("0.01")
PRICE_PLACES = Decimal("0.0001")
_EMPTY_MARKERS = {"", "-", "--", "---", "X", "N/A", "NULL", "NONE"}


def to_decimal(value: Any) -> Decimal | None:
    """把 API 的數字或字串轉成 Decimal；無法解析（例如 "-"、"" 或 NaN）時回傳 None。"""
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, Decimal):
        return value if value.is_finite() else None
    if isinstance(value, int):
        return Decimal(value)
    if isinstance(value, float):
        if value != value or value in (float("inf"), float("-inf")):
            return None
        return Decimal(repr(value))
    text = str(value).strip().replace(",", "")
    if text.upper() in _EMPTY_MARKERS:
        return None
    try:
        result = Decimal(text)
    except InvalidOperation:
        return None
    return result if result.is_finite() else None


def quantize_money(value: Decimal) -> Decimal:
    """金額四捨五入到小數第二位。"""
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def quantize_price(value: Decimal) -> Decimal:
    """價格、匯率保留到小數第四位。"""
    return value.quantize(PRICE_PLACES, rounding=ROUND_HALF_UP)
