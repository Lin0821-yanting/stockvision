"""帳號註冊、登入、session 管理與登入失敗次數限制。"""

from __future__ import annotations

import time
from datetime import datetime, timedelta

from sqlalchemy import delete, func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core import clock
from app.core.config import get_settings
from app.core.errors import AuthenticationError, ConflictError, ForbiddenError, TooManyAttemptsError
from app.core.security import hash_password, hash_token, new_session_token, verify_password
from app.models.account import Account
from app.models.alert import Alert, AlertEvent
from app.models.user import User, UserSession
from app.models.watchlist import WatchlistItem
from app.services import trading_service

MAX_FAILURES = 5
LOCK_SECONDS = 60
SEEN_UPDATE_INTERVAL = timedelta(minutes=5)


class LoginThrottle:
    """同一個帳號＋IP 連續失敗 MAX_FAILURES 次就暫停 LOCK_SECONDS 秒。存在記憶體，後端重啟後歸零。"""

    def __init__(self) -> None:
        self._state: dict[str, tuple[int, float]] = {}  # key → (連續失敗次數, 鎖定到期的 monotonic 時間)

    def check(self, key: str) -> None:
        _, locked_until = self._state.get(key, (0, 0.0))
        remaining = locked_until - time.monotonic()
        if remaining > 0:
            seconds = int(remaining) + 1
            raise TooManyAttemptsError(f"登入失敗次數過多，請 {seconds} 秒後再試", details={"retry_after": seconds})

    def failed(self, key: str) -> None:
        failures = self._state.get(key, (0, 0.0))[0] + 1
        if failures >= MAX_FAILURES:
            self._state[key] = (0, time.monotonic() + LOCK_SECONDS)
        else:
            self._state[key] = (failures, 0.0)

    def succeeded(self, key: str) -> None:
        self._state.pop(key, None)

    def reset(self) -> None:
        self._state.clear()


throttle = LoginThrottle()
_timing_guard_hash: str | None = None


def normalize_username(username: str) -> str:
    return username.strip().lower()


def _guard_hash() -> str:
    """帳號不存在時也做一次雜湊比對，回應時間不會透露帳號是否存在。"""
    global _timing_guard_hash
    if _timing_guard_hash is None:
        _timing_guard_hash = hash_password("stockvision-timing-guard")
    return _timing_guard_hash


def claim_legacy_data(db: Session, user: User) -> None:
    """單人模式留下的資料（user_id 為空）交給第一位註冊的使用者，原本的交易紀錄不會遺失。"""
    legacy_account = db.scalar(select(Account).where(Account.user_id.is_(None)).order_by(Account.id).limit(1))
    if legacy_account is not None:
        legacy_account.user_id = user.id
    for model in (WatchlistItem, Alert, AlertEvent):
        db.execute(update(model).where(model.user_id.is_(None)).values(user_id=user.id))


def register(db: Session, username: str, password: str, display_name: str | None) -> User:
    if not get_settings().registration_enabled:
        raise ForbiddenError("目前不開放註冊新帳號", code="REGISTRATION_DISABLED")
    normalized = normalize_username(username)
    if db.scalar(select(User.id).where(User.username == normalized)) is not None:
        raise ConflictError("這個帳號已經有人使用，請換一個", details={"username": normalized})

    now = clock.now()
    user = User(
        username=normalized,
        display_name=(display_name or "").strip()[:50] or username.strip(),
        password_hash=hash_password(password),
        created_at=now,
        last_login_at=now,
    )
    db.add(user)
    try:
        db.flush()
    except IntegrityError as exc:  # 兩個請求同時註冊同一個帳號
        db.rollback()
        raise ConflictError("這個帳號已經有人使用，請換一個", details={"username": normalized}) from exc
    if db.scalar(select(func.count()).select_from(User)) == 1:
        claim_legacy_data(db, user)
    db.commit()
    trading_service.get_account(db, user)  # 沒有接收舊帳戶時建立新的 NT$1,000,000 帳戶
    db.refresh(user)
    return user


def authenticate(db: Session, username: str, password: str, client_key: str) -> User:
    normalized = normalize_username(username)
    key = f"{normalized}|{client_key}"
    throttle.check(key)
    user = db.scalar(select(User).where(User.username == normalized))
    valid = verify_password(password, user.password_hash if user else _guard_hash())
    if user is None or not valid:
        throttle.failed(key)
        raise AuthenticationError("帳號或密碼錯誤", code="INVALID_CREDENTIALS")
    throttle.succeeded(key)
    user.last_login_at = clock.now()
    db.commit()
    return user


def create_session(db: Session, user: User, user_agent: str | None) -> tuple[str, datetime]:
    now = clock.now()
    db.execute(delete(UserSession).where(UserSession.user_id == user.id, UserSession.expires_at < now))
    token = new_session_token()
    expires_at = now + timedelta(days=get_settings().session_days)
    db.add(
        UserSession(
            user_id=user.id,
            token_hash=hash_token(token),
            created_at=now,
            expires_at=expires_at,
            last_seen_at=now,
            user_agent=(user_agent or "")[:200] or None,
        )
    )
    db.commit()
    return token, expires_at


def user_for_token(db: Session, token: str) -> User | None:
    session = db.scalar(select(UserSession).where(UserSession.token_hash == hash_token(token)))
    if session is None:
        return None
    now = clock.now()
    if session.expires_at <= now:
        db.delete(session)
        db.commit()
        return None
    if now - session.last_seen_at > SEEN_UPDATE_INTERVAL:
        session.last_seen_at = now
        db.commit()
    return db.get(User, session.user_id)


def revoke_session(db: Session, token: str) -> None:
    db.execute(delete(UserSession).where(UserSession.token_hash == hash_token(token)))
    db.commit()
