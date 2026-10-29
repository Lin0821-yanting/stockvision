"""市況與匯率 API。"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_optional_user
from app.core import clock
from app.core.config import get_settings
from app.core.market_hours import SESSIONS
from app.database.session import get_db
from app.models.user import User
from app.schemas.common import ERROR_RESPONSES
from app.schemas.market import FxRateOut, MarketSessionOut, MarketStatusOut
from app.schemas.overview import OverviewOut
from app.schemas.stock import Market, Period
from app.services import fx_service, overview_service

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


@router.get(
    "/market/overview",
    response_model=OverviewOut,
    summary="大盤總覽：指數與市值前幾大公司的報價、走勢與期間報酬",
    responses=ERROR_RESPONSES,
)
async def market_overview(
    market: Annotated[Market, Query(description="TW 台股或 US 美股")] = "TW",
    period: Annotated[Period, Query(description="走勢期間：1M、3M、6M 或 1Y")] = "1M",
    limit: Annotated[int | None, Query(ge=4, le=30, description="列出的公司數量，預設為 OVERVIEW_SIZE（12）")] = None,
    user: User | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> OverviewOut:
    return await overview_service.get_overview(db, market, period, limit or get_settings().overview_size, user)
