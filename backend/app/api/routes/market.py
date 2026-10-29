"""市況與匯率 API。"""

from __future__ import annotations

from fastapi import APIRouter

from app.core import clock
from app.core.market_hours import SESSIONS
from app.schemas.common import ERROR_RESPONSES
from app.schemas.market import FxRateOut, MarketSessionOut, MarketStatusOut
from app.services import fx_service

router = APIRouter(prefix="/api", tags=["市況與匯率"])


@router.get("/market/status", response_model=MarketStatusOut, summary="台股與美股目前是否為交易時段")
def market_status() -> MarketStatusOut:
    now = clock.now()
    markets = []
    for session in SESSIONS.values():
        state, label = session.state(now)
        markets.append(
            MarketSessionOut(
                market=session.market,
                name=session.name,
                state=state,
                label=label,
                is_open=state == "open",
                local_time=session.local_now(now),
                timezone=str(session.timezone),
                session=f"{session.open_time:%H:%M}–{session.close_time:%H:%M}（{session.timezone_label}）",
                session_taipei=session.session_in_taipei(now),
                note="依星期與時間判斷，未包含國定假日；假日時報價會停在最後交易日",
            )
        )
    return MarketStatusOut(markets=markets, server_time=now)


@router.get("/fx/usd-twd", response_model=FxRateOut, summary="USD/TWD 匯率（美股模擬交易換算用）", responses=ERROR_RESPONSES)
async def usd_twd() -> FxRateOut:
    return await fx_service.get_usd_twd()
