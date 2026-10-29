"""共用的 HTTPX AsyncClient：逾時、失敗重試與錯誤轉換。"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import httpx

from app.core.config import get_settings
from app.core.errors import UpstreamError, UpstreamRateLimitedError

logger = logging.getLogger("stockvision.http")

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) StockVision/0.1 (educational project)"
RETRY_STATUS = {429, 500, 502, 503, 504}
# 第 n 次重試前等待 RETRY_BACKOFF_SECONDS * 2^n 秒；測試時會設成 0
RETRY_BACKOFF_SECONDS = 0.4

_client: httpx.AsyncClient | None = None
_client_loop: asyncio.AbstractEventLoop | None = None


def get_client() -> httpx.AsyncClient:
    """每個 event loop 共用一個連線池（測試時每個 TestClient 都有自己的 loop）。"""
    global _client, _client_loop
    loop = asyncio.get_running_loop()
    if _client is None or _client.is_closed or _client_loop is not loop:
        _client = httpx.AsyncClient(
            timeout=get_settings().http_timeout_seconds,
            headers={"User-Agent": USER_AGENT},
            follow_redirects=True,
        )
        _client_loop = loop
    return _client


async def close_client() -> None:
    global _client
    if _client is not None and not _client.is_closed:
        await _client.aclose()
    _client = None


async def request_json(
    url: str,
    *,
    source: str,
    params: dict[str, str] | None = None,
    headers: dict[str, str] | None = None,
    retries: int = 2,
) -> tuple[int, Any]:
    """發出 GET 並解析 JSON，回傳 (HTTP 狀態碼, 內容)。

    逾時、連線失敗、429 與 5xx 會重試；全部失敗時丟出 UpstreamError。
    其他 4xx 不重試，交給呼叫端依各 API 的格式判斷。
    """
    client = get_client()
    reason = ""
    for attempt in range(retries + 1):
        try:
            response = await client.get(url, params=params, headers=headers)
        except httpx.TimeoutException:
            reason = "連線逾時"
        except httpx.HTTPError as exc:
            reason = f"連線失敗（{type(exc).__name__}）"
        else:
            if response.status_code not in RETRY_STATUS:
                try:
                    return response.status_code, response.json()
                except ValueError as exc:
                    raise UpstreamError(
                        f"{source} 回傳的資料格式不正確",
                        details={"source": source, "status": response.status_code},
                    ) from exc
            reason = f"HTTP {response.status_code}"
            if response.status_code == 429 and attempt == retries:
                raise UpstreamRateLimitedError(
                    f"{source} 請求次數過多，請稍後再試",
                    details={"source": source},
                )
        if attempt < retries:
            await asyncio.sleep(RETRY_BACKOFF_SECONDS * (2**attempt))

    logger.warning("%s request failed after %d attempts: %s", source, retries + 1, reason)
    raise UpstreamError(
        f"無法從 {source} 取得資料：{reason}",
        details={"source": source, "reason": reason},
    )


async def get_json(
    url: str,
    *,
    source: str,
    params: dict[str, str] | None = None,
    headers: dict[str, str] | None = None,
    retries: int = 2,
) -> Any:
    status, payload = await request_json(url, source=source, params=params, headers=headers, retries=retries)
    if status >= 400:
        raise UpstreamError(
            f"{source} 回應錯誤（HTTP {status}）",
            details={"source": source, "status": status},
        )
    return payload
