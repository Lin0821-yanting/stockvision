"""價格提醒的判斷邏輯（純函式）。"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

PRICE_LTE = "PRICE_LTE"
PRICE_GTE = "PRICE_GTE"
NEW_20D_LOW = "NEW_20D_LOW"
CONDITIONS = (PRICE_LTE, PRICE_GTE, NEW_20D_LOW)

ONCE = "ONCE"
EVERY_CROSS = "EVERY_CROSS"


@dataclass(frozen=True)
class Evaluation:
    condition_met: bool
    triggered: bool
    deactivate: bool


def condition_met(condition: str, price: Decimal, target: Decimal | None, low_20d: Decimal | None) -> bool:
    if condition == PRICE_LTE:
        return target is not None and price <= target
    if condition == PRICE_GTE:
        return target is not None and price >= target
    if condition == NEW_20D_LOW:
        # 最新價格低於前 20 個交易日的最低收盤價
        return low_20d is not None and price < low_20d
    raise ValueError(f"未知的提醒條件：{condition}")


def evaluate(
    *,
    condition: str,
    target: Decimal | None,
    trigger_mode: str,
    previously_met: bool,
    price: Decimal,
    low_20d: Decimal | None = None,
) -> Evaluation:
    """條件由「不成立」變成「成立」才觸發；ONCE 模式觸發後自動停用。"""
    met = condition_met(condition, price, target, low_20d)
    triggered = met and not previously_met
    return Evaluation(condition_met=met, triggered=triggered, deactivate=triggered and trigger_mode == ONCE)


def describe(condition: str, target: Decimal | None, currency: str = "TWD") -> str:
    if condition == PRICE_LTE:
        return f"價格 ≤ {target:,.2f} {currency}"
    if condition == PRICE_GTE:
        return f"價格 ≥ {target:,.2f} {currency}"
    return "創 20 日新低（低於前 20 個交易日最低收盤價）"
