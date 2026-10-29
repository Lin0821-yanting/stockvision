"""預設資料。"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.account import Account

ACCOUNT_ID = 1


def seed_defaults(db: Session) -> None:
    """第一次啟動時建立 NT$1,000,000 的模擬帳戶。"""
    if db.get(Account, ACCOUNT_ID) is None:
        initial = get_settings().initial_cash
        db.add(Account(id=ACCOUNT_ID, base_currency="TWD", initial_cash=initial, cash=initial, cycle=1))
        db.commit()
