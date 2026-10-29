"""自訂 SQLAlchemy 欄位型別。"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import DateTime, String
from sqlalchemy.types import TypeDecorator


def utcnow() -> datetime:
    return datetime.now(UTC)


class DecimalText(TypeDecorator[Decimal]):
    """以文字儲存 Decimal。

    SQLite 沒有真正的十進位型別，用 Numeric 會被轉成浮點數而產生誤差，
    所以金額一律存成字串，讀出時再轉回 Decimal。
    """

    impl = String(64)
    cache_ok = True

    def process_bind_param(self, value: Decimal | None, dialect) -> str | None:
        if value is None:
            return None
        if not isinstance(value, Decimal):
            value = Decimal(str(value))
        return format(value, "f")

    def process_result_value(self, value: str | None, dialect) -> Decimal | None:
        if value is None:
            return None
        return Decimal(value)


class UTCDateTime(TypeDecorator[datetime]):
    """資料庫內存無時區的 UTC 時間，讀出時補回 UTC 時區。"""

    impl = DateTime
    cache_ok = True

    def process_bind_param(self, value: datetime | None, dialect) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            raise ValueError("UTCDateTime 欄位只接受帶時區的 datetime")
        return value.astimezone(UTC).replace(tzinfo=None)

    def process_result_value(self, value: datetime | None, dialect) -> datetime | None:
        if value is None:
            return None
        return value.replace(tzinfo=UTC)
