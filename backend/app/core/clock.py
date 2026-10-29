"""目前時間的單一來源；測試可以替換 now() 來模擬盤中或收盤時段。"""

from __future__ import annotations

from datetime import UTC, datetime


def now() -> datetime:
    return datetime.now(UTC)
