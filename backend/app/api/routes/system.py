"""系統狀態 API。"""

from __future__ import annotations

from fastapi import APIRouter

from app import __version__
from app.core.config import get_settings
from app.database.types import utcnow
from app.schemas.system import DataSourceStatus, HealthOut

router = APIRouter(prefix="/api", tags=["系統"])


@router.get("/health", response_model=HealthOut, summary="健康檢查與資料來源設定狀態")
def health() -> HealthOut:
    settings = get_settings()
    return HealthOut(
        status="ok",
        app=settings.app_name,
        version=__version__,
        server_time=utcnow(),
        data_sources=[
            DataSourceStatus(
                name="FinMind",
                purpose="台股與美股清單、歷史日資料、USD/TWD 匯率",
                configured=True,
                note="已設定 token（600 次/小時）"
                if settings.finmind_configured
                else "未設定 token，使用免費額度（300 次/小時）",
            ),
            DataSourceStatus(
                name="TWSE MIS",
                purpose="台股盤中報價（約 5 秒更新）",
                configured=True,
                note="不需金鑰；證交所網頁使用的公開端點，非官方 OpenAPI",
            ),
            DataSourceStatus(
                name="TWSE / TPEx OpenAPI",
                purpose="上市、上櫃最新日收盤備援資料",
                configured=True,
                note="不需金鑰",
            ),
            DataSourceStatus(
                name="Finnhub",
                purpose="美股盤中報價",
                configured=settings.finnhub_configured,
                note="已設定 API Key"
                if settings.finnhub_configured
                else "未設定 FINNHUB_API_KEY，美股改用 FinMind 每日收盤資料",
            ),
        ],
    )
