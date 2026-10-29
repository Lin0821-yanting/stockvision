"""預設資料。"""

from __future__ import annotations

from sqlalchemy.orm import Session


def seed_defaults(db: Session) -> None:
    """目前尚無需要預先建立的資料（模擬帳戶會在交易功能加入）。"""
