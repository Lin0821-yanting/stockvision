"""應用程式設定：從環境變數與 .env 讀取（pydantic-settings）。"""

from __future__ import annotations

from decimal import Decimal
from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]
PROJECT_DIR = BACKEND_DIR.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        # 以專案根目錄的 .env 為主；backend/.env 若存在會覆寫同名設定。
        # 真正的環境變數優先於兩者（測試與 E2E 會用這個方式覆寫）。
        env_file=(PROJECT_DIR / ".env", BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "StockVision API"
    database_url: str = "sqlite:///./data/stockvision.db"
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    finmind_token: str = ""
    finnhub_api_key: str = ""

    initial_cash: Decimal = Decimal("1000000")
    alert_scheduler_enabled: bool = True
    alert_check_interval_seconds: int = Field(default=60, ge=15, le=3600)
    http_timeout_seconds: float = Field(default=10.0, gt=0)

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def resolved_database_url(self) -> str:
        """把 SQLite 相對路徑換成以 backend/ 為基準的絕對路徑，避免受啟動目錄影響。"""
        prefix = "sqlite:///"
        url = self.database_url.strip()
        if url.startswith(prefix):
            raw_path = url[len(prefix):]
            if raw_path and raw_path != ":memory:" and not Path(raw_path).is_absolute():
                return prefix + (BACKEND_DIR / raw_path).resolve().as_posix()
        return url

    @property
    def finmind_configured(self) -> bool:
        return bool(self.finmind_token.strip())

    @property
    def finnhub_configured(self) -> bool:
        return bool(self.finnhub_api_key.strip())


@lru_cache
def get_settings() -> Settings:
    return Settings()
