"""登入 API：註冊、登入、登出與目前使用者。"""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_optional_user, request_token
from app.core.config import get_settings
from app.database.session import get_db
from app.models.user import User
from app.schemas.auth import AuthOut, LoginIn, RegisterIn, SessionOut, UserOut
from app.schemas.common import ERROR_RESPONSES, ErrorResponse
from app.services import auth_service

router = APIRouter(prefix="/api/auth", tags=["登入"])

REGISTER_RESPONSES = {
    **ERROR_RESPONSES,
    403: {"model": ErrorResponse, "description": "目前不開放註冊（REGISTRATION_DISABLED）"},
    409: {"model": ErrorResponse, "description": "帳號已經有人使用"},
}
LOGIN_RESPONSES = {
    **ERROR_RESPONSES,
    401: {"model": ErrorResponse, "description": "帳號或密碼錯誤（INVALID_CREDENTIALS）"},
    429: {"model": ErrorResponse, "description": "失敗次數過多，暫時鎖定（TOO_MANY_ATTEMPTS）"},
}
ME_RESPONSES = {401: {"model": ErrorResponse, "description": "尚未登入或登入已過期（AUTH_REQUIRED）"}}


def user_out(user: User) -> UserOut:
    return UserOut(
        id=user.id,
        username=user.username,
        display_name=user.display_name,
        created_at=user.created_at,
        last_login_at=user.last_login_at,
    )


def _set_session_cookie(response: Response, token: str) -> None:
    settings = get_settings()
    response.set_cookie(
        settings.session_cookie_name,
        token,
        max_age=settings.session_days * 24 * 60 * 60,
        httponly=True,
        samesite="lax",
        secure=settings.session_cookie_secure,
        path="/",
    )


def _start_session(db: Session, user: User, request: Request, response: Response) -> datetime:
    token, expires_at = auth_service.create_session(db, user, request.headers.get("user-agent"))
    _set_session_cookie(response, token)
    return expires_at


@router.post(
    "/register",
    response_model=AuthOut,
    status_code=status.HTTP_201_CREATED,
    summary="註冊新帳號（成功後自動登入）",
    responses=REGISTER_RESPONSES,
)
def register(payload: RegisterIn, request: Request, response: Response, db: Session = Depends(get_db)) -> AuthOut:
    user = auth_service.register(db, payload.username, payload.password, payload.display_name)
    expires_at = _start_session(db, user, request, response)
    return AuthOut(user=user_out(user), expires_at=expires_at, message=f"歡迎加入，{user.display_name}！")


@router.post("/login", response_model=AuthOut, summary="登入（設定 HttpOnly session cookie）", responses=LOGIN_RESPONSES)
def login(payload: LoginIn, request: Request, response: Response, db: Session = Depends(get_db)) -> AuthOut:
    client = request.client.host if request.client else "unknown"
    user = auth_service.authenticate(db, payload.username, payload.password, client)
    expires_at = _start_session(db, user, request, response)
    return AuthOut(user=user_out(user), expires_at=expires_at, message=f"歡迎回來，{user.display_name}")


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT, summary="登出（刪除 session）")
def logout(token: str | None = Depends(request_token), db: Session = Depends(get_db)) -> Response:
    if token:
        auth_service.revoke_session(db, token)
    settings = get_settings()
    response = Response(status_code=status.HTTP_204_NO_CONTENT)
    response.delete_cookie(
        settings.session_cookie_name,
        path="/",
        httponly=True,
        samesite="lax",
        secure=settings.session_cookie_secure,
    )
    return response


@router.get("/me", response_model=UserOut, summary="目前登入的使用者（未登入回 401）", responses=ME_RESPONSES)
def me(user: User = Depends(get_current_user)) -> UserOut:
    return user_out(user)


@router.get(
    "/session",
    response_model=SessionOut,
    summary="目前的登入狀態（未登入也回 200，給前端判斷畫面用）",
)
def session(user: User | None = Depends(get_optional_user)) -> SessionOut:
    return SessionOut(authenticated=user is not None, user=user_out(user) if user else None)
