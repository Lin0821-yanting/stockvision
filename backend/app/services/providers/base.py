"""各資料來源共用的資料結構與解析工具。"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(frozen=True)
class DailySnapshot:
    """官方 OpenAPI 的最新一日行情（成交量單位：股）。"""

    symbol: str
    name: str
    trade_date: date
    open: Decimal | None
    high: Decimal | None
    low: Decimal | None
    close: Decimal | None
    change: Decimal | None
    volume: int | None
    source: str


def parse_roc_date(text: str) -> date | None:
    """民國日期 '1151028' 或 '115/10/28' → date(2026, 10, 28)。"""
    digits = str(text).strip().replace("/", "")
    if not digits.isdigit() or len(digits) not in (6, 7):
        return None
    year, month, day = int(digits[:-4]), int(digits[-4:-2]), int(digits[-2:])
    try:
        return date(year + 1911, month, day)
    except ValueError:
        return None
