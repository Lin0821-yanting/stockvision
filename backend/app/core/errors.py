"""統一的錯誤類型。main.py 會把它們轉成 {"error": {"code", "message", "details"}} 格式的 JSON。"""

from __future__ import annotations

from typing import Any


class AppError(Exception):
    status_code: int = 400
    code: str = "BAD_REQUEST"

    def __init__(
        self,
        message: str,
        *,
        code: str | None = None,
        status_code: int | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        if code is not None:
            self.code = code
        if status_code is not None:
            self.status_code = status_code
        self.details = details or {}

    def to_dict(self) -> dict[str, Any]:
        return {"error": {"code": self.code, "message": self.message, "details": self.details}}


class NotFoundError(AppError):
    status_code = 404
    code = "NOT_FOUND"


class SymbolNotFoundError(NotFoundError):
    code = "SYMBOL_NOT_FOUND"


class ConflictError(AppError):
    status_code = 409
    code = "CONFLICT"


class AuthenticationError(AppError):
    """未登入、session 過期或帳號密碼錯誤。"""

    status_code = 401
    code = "AUTH_REQUIRED"


class ForbiddenError(AppError):
    status_code = 403
    code = "FORBIDDEN"


class TooManyAttemptsError(AppError):
    status_code = 429
    code = "TOO_MANY_ATTEMPTS"


class InvalidRequestError(AppError):
    status_code = 400
    code = "INVALID_REQUEST"


class BusinessRuleError(AppError):
    status_code = 400
    code = "BUSINESS_RULE_VIOLATION"


class InsufficientFundsError(BusinessRuleError):
    code = "INSUFFICIENT_FUNDS"


class InsufficientSharesError(BusinessRuleError):
    code = "INSUFFICIENT_SHARES"


class UpstreamError(AppError):
    """外部股票 API 無法取得資料（逾時、連線失敗、5xx、格式錯誤）。"""

    status_code = 503
    code = "UPSTREAM_UNAVAILABLE"


class UpstreamRateLimitedError(UpstreamError):
    code = "UPSTREAM_RATE_LIMITED"


class PriceUnavailableError(UpstreamError):
    code = "MARKET_PRICE_UNAVAILABLE"
