"""FinMind API v4（https://finmind.github.io/）。

免費額度：未設定 token 每小時 300 次，設定 token 後 600 次。
分 K、Tick 等盤中資料需要付費等級，因此本專案只使用日資料。
"""

from __future__ import annotations

from datetime import date
from typing import Any

from app.core.config import get_settings
from app.core.errors import UpstreamError, UpstreamRateLimitedError
from app.services.providers.http import request_json

BASE_URL = "https://api.finmindtrade.com/api/v4/data"
SOURCE = "FinMind"


async def fetch_dataset(
    dataset: str,
    *,
    data_id: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
) -> list[dict[str, Any]]:
    params = {"dataset": dataset}
    if data_id:
        params["data_id"] = data_id
    if start_date:
        params["start_date"] = start_date.isoformat()
    if end_date:
        params["end_date"] = end_date.isoformat()

    settings = get_settings()
    # token 放在 header，不會出現在網址或 log
    headers = {"Authorization": f"Bearer {settings.finmind_token.strip()}"} if settings.finmind_configured else None
    status, payload = await request_json(BASE_URL, source=SOURCE, params=params, headers=headers)

    details = {"source": SOURCE, "dataset": dataset}
    if not isinstance(payload, dict):
        raise UpstreamError("FinMind 回傳的資料格式不正確", details=details)

    api_status = payload.get("status", status)
    message = str(payload.get("msg", ""))
    if api_status == 402 or "upper limit" in message.lower():
        raise UpstreamRateLimitedError(
            "FinMind API 已達使用上限（未設定 token 為每小時 300 次），請稍後再試或在 .env 設定 FINMIND_TOKEN",
            details=details,
        )
    if api_status != 200:
        raise UpstreamError(f"FinMind 回應錯誤：{message or api_status}", details={**details, "status": api_status})

    data = payload.get("data")
    if not isinstance(data, list):
        raise UpstreamError("FinMind 回傳的資料格式不正確", details=details)
    return data


async def taiwan_stock_info() -> list[dict[str, Any]]:
    return await fetch_dataset("TaiwanStockInfo")


async def us_stock_info() -> list[dict[str, Any]]:
    return await fetch_dataset("USStockInfo")


async def taiwan_stock_price(stock_id: str, start: date, end: date) -> list[dict[str, Any]]:
    return await fetch_dataset("TaiwanStockPrice", data_id=stock_id, start_date=start, end_date=end)


async def us_stock_price(stock_id: str, start: date, end: date) -> list[dict[str, Any]]:
    return await fetch_dataset("USStockPrice", data_id=stock_id, start_date=start, end_date=end)


async def exchange_rate(currency: str, start: date) -> list[dict[str, Any]]:
    return await fetch_dataset("TaiwanExchangeRate", data_id=currency, start_date=start)
