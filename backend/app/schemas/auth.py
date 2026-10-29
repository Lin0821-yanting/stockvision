"""登入與註冊的請求與回應結構。"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

USERNAME_PATTERN = r"^[A-Za-z0-9_]{3,30}$"


class RegisterIn(BaseModel):
    username: str = Field(pattern=USERNAME_PATTERN, description="3–30 個英文字母、數字或底線，不分大小寫", examples=["alice"])
    password: str = Field(min_length=8, max_length=128, description="至少 8 個字元", examples=["stockvision-demo"])
    display_name: str | None = Field(default=None, max_length=50, examples=["Alice"])


class LoginIn(BaseModel):
    username: str = Field(min_length=1, max_length=30, examples=["alice"])
    password: str = Field(min_length=1, max_length=128, examples=["stockvision-demo"])


class UserOut(BaseModel):
    id: int
    username: str
    display_name: str
    created_at: datetime
    last_login_at: datetime | None


class AuthOut(BaseModel):
    user: UserOut
    expires_at: datetime = Field(description="這次登入的 session 到期時間")
    message: str


class SessionOut(BaseModel):
    authenticated: bool = Field(description="目前是否已登入")
    user: UserOut | None = Field(default=None, description="未登入時為 null")
