"""StockVision FastAPI 進入點。

啟動：uvicorn app.main:app --reload --port 8000（在 backend/ 目錄執行）
Swagger UI：http://localhost:8000/docs
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app import __version__
from app.api.routes import market, stocks, system, watchlist
from app.core.config import get_settings
from app.core.errors import AppError
from app.database.session import init_db
from app.services.providers.http import close_client

logger = logging.getLogger("stockvision")

DESCRIPTION = """
StockVision 台美股智慧看盤與模擬投資平台的 Python 後端。

* 股票資料：FinMind、TWSE OpenAPI、TPEx OpenAPI、TWSE MIS（盤中）、Finnhub（美股盤中，選用）
* 所有價格都附帶資料來源、資料日期與更新時間；日資料不會被標示成即時報價
* 模擬交易只是練習用途：**模擬成交，不代表真實市場價格或成交**
"""


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield
    await close_client()


def _error(status_code: int, code: str, message: str, details: dict | None = None) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"error": {"code": code, "message": message, "details": details or {}}},
    )


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def handle_app_error(_: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content=exc.to_dict())

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
        errors = [
            {
                "loc": [str(part) for part in err.get("loc", ())],
                "msg": str(err.get("msg", "")),
                "type": str(err.get("type", "")),
            }
            for err in exc.errors()
        ]
        message = "輸入資料格式不正確"
        if errors:
            field = ".".join(part for part in errors[0]["loc"] if part not in ("body", "query", "path"))
            message = f"{message}：{field} {errors[0]['msg']}".rstrip()
        return _error(422, "VALIDATION_ERROR", message, {"errors": errors})

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_error(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        message = exc.detail if isinstance(exc.detail, str) else "請求失敗"
        if exc.status_code == 404 and message == "Not Found":
            message = "找不到這個 API 路徑"
        return _error(exc.status_code, f"HTTP_{exc.status_code}", message)

    @app.exception_handler(Exception)
    async def handle_unexpected_error(_: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled error", exc_info=exc)
        return _error(500, "INTERNAL_ERROR", "伺服器發生未預期的錯誤")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version=__version__,
        description=DESCRIPTION,
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    register_exception_handlers(app)
    app.include_router(system.router)
    app.include_router(market.router)
    app.include_router(stocks.router)
    app.include_router(watchlist.router)
    return app


app = create_app()
