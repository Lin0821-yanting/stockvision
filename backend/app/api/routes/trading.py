"""模擬交易 API：帳戶、投資組合、下單與交易紀錄（需要登入，每位使用者各自獨立）。"""

from __future__ import annotations

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.schemas.common import AUTH_REQUIRED_RESPONSES, ERROR_RESPONSES
from app.schemas.trading import (
    AccountOut,
    PortfolioOut,
    ResetOut,
    TradeListOut,
    TradePreviewOut,
    TradeRequest,
    TradeResultOut,
)
from app.services import portfolio_service, trading_service

router = APIRouter(prefix="/api", tags=["模擬交易"], responses=AUTH_REQUIRED_RESPONSES)


@router.get("/account", response_model=AccountOut, summary="模擬帳戶（現金餘額與回合）")
def get_account(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> AccountOut:
    return trading_service.account_out(trading_service.get_account(db, user))


@router.post("/account/reset", response_model=ResetOut, summary="重置模擬帳戶（清空持股、現金回到 NT$1,000,000）")
def reset_account(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> ResetOut:
    account = trading_service.reset_account(db, user)
    return ResetOut(
        message=f"帳戶已重置為 NT$ {account.initial_cash:,.0f}，目前為第 {account.cycle} 輪；先前的交易紀錄仍保留",
        account=trading_service.account_out(account),
    )


@router.get("/portfolio", response_model=PortfolioOut, summary="投資組合：持股市值、損益、總資產與報酬率")
async def get_portfolio(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> PortfolioOut:
    return await portfolio_service.get_portfolio(db, user)


@router.post("/trades/preview", response_model=TradePreviewOut, summary="下單試算（不會成交）")
async def preview_trade(
    payload: TradeRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> TradePreviewOut:
    return await trading_service.preview_trade(db, user, payload)


@router.post(
    "/trades",
    response_model=TradeResultOut,
    status_code=status.HTTP_201_CREATED,
    summary="模擬買進或賣出（以後端取得的最新價格成交）",
)
async def create_trade(
    payload: TradeRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> TradeResultOut:
    trade = await trading_service.execute_trade(db, user, payload)
    action = "買進" if trade.side == "BUY" else "賣出"
    return TradeResultOut(
        message=f"模擬{action} {trade.symbol} {trade.name} {trade.shares:,} 股，成交價 {trade.price:,.2f} {trade.currency}",
        trade=trading_service.trade_out(trade),
        account=trading_service.account_out(trading_service.get_account(db, user)),
    )


@router.get("/trades", response_model=TradeListOut, summary="交易紀錄")
def list_trades(
    scope: Annotated[Literal["current", "all"], Query(description="current＝本輪；all＝包含重置前的紀錄")] = "current",
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TradeListOut:
    account, trades = trading_service.list_trades(db, user, scope, limit)
    return TradeListOut(scope=scope, current_cycle=account.cycle, trades=[trading_service.trade_out(t) for t in trades])
