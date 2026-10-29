"""FastAPI 相依項目：取得目前登入的使用者。"""

from __future__ import annotations

from fastapi import Depends, Security
from fastapi.security import APIKeyCookie, HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import AuthenticationError
from app.database.session import get_db
from app.models.user import User
from app.services import auth_service

# 兩種方式擇一：瀏覽器自動帶上的 HttpOnly cookie，或 API 工具用的 Bearer token
cookie_scheme = APIKeyCookie(
    name=get_settings().session_cookie_name,
    auto_error=False,
    scheme_name="SessionCookie",
    description="登入（POST /api/auth/login）後瀏覽器會自動帶上這個 HttpOnly cookie",
)
bearer_scheme = HTTPBearer(auto_error=False, scheme_name="BearerToken", description="Authorization: Bearer <session token>")


def request_token(
    cookie: str | None = Security(cookie_scheme),
    bearer: HTTPAuthorizationCredentials | None = Security(bearer_scheme),
) -> str | None:
    return cookie or (bearer.credentials if bearer else None)


def get_optional_user(token: str | None = Depends(request_token), db: Session = Depends(get_db)) -> User | None:
    return auth_service.user_for_token(db, token) if token else None


def get_current_user(user: User | None = Depends(get_optional_user)) -> User:
    if user is None:
        raise AuthenticationError("請先登入", code="AUTH_REQUIRED")
    return user
