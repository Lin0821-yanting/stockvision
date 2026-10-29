"""共用的回應結構。"""

from __future__ import annotations

from decimal import Decimal
from typing import Annotated, Any

from pydantic import BaseModel, PlainSerializer

# 內部計算一律用 Decimal；輸出 JSON 時轉成數字，前端不必再解析字串。
JsonDecimal = Annotated[Decimal, PlainSerializer(float, return_type=float, when_used="json")]


class ErrorBody(BaseModel):
    code: str
    message: str
    details: dict[str, Any] = {}


class ErrorResponse(BaseModel):
    error: ErrorBody


ERROR_RESPONSES: dict[int | str, dict[str, Any]] = {
    400: {"model": ErrorResponse, "description": "違反業務規則（例如資金不足）"},
    404: {"model": ErrorResponse, "description": "找不到資料"},
    422: {"model": ErrorResponse, "description": "輸入資料格式不正確"},
    503: {"model": ErrorResponse, "description": "外部股票 API 暫時無法取得資料"},
}
