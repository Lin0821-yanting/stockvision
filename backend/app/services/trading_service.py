"""模擬交易流程：由後端取得最新價格與匯率 → 純函式計算 → 在同一個資料庫交易內更新現金、持股與交易紀錄。"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Literal

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core import clock
from app.core.errors import BusinessRuleError, PriceUnavailableError
from app.database.seed import ACCOUNT_ID, seed_defaults
from app.models.account import Account, Position, Trade
from app.schemas.market import FxRateOut
from app.schemas.stock import QuoteOut
from app.schemas.trading import AccountOut, TradeOut, TradePreviewOut, TradeRequest
from app.services import catalog_service, fx_service, quote_service
from app.services.entities import StockEntry
from app.services.trading_logic import ONE, Fill, Holding, apply_buy, apply_sell, trade_amounts


@dataclass(frozen=True)
class PricedOrder:
    entry: StockEntry
    quote: QuoteOut
    price: Decimal
    fx: FxRateOut | None

    @property
    def fx_rate(self) -> Decimal:
        return self.fx.rate if self.fx is not None else ONE


def get_account(db: Session) -> Account:
    account = db.get(Account, ACCOUNT_ID)
    if account is None:
        seed_defaults(db)
        account = db.get(Account, ACCOUNT_ID)
    return account


def account_out(account: Account) -> AccountOut:
    return AccountOut(
        id=account.id,
        base_currency=account.base_currency,
        initial_cash=account.initial_cash,
        cash=account.cash,
        cycle=account.cycle,
        created_at=account.created_at,
        reset_at=account.reset_at,
    )


def trade_out(trade: Trade) -> TradeOut:
    return TradeOut.model_validate(trade, from_attributes=True)


def find_position(db: Session, account: Account, market: str, symbol: str) -> Position | None:
    return db.scalar(
        select(Position).where(Position.account_id == account.id, Position.market == market, Position.symbol == symbol)
    )


def to_holding(position: Position | None) -> Holding | None:
    if position is None:
        return None
    return Holding(shares=position.shares, avg_cost=position.avg_cost, cost_basis_twd=position.cost_basis_twd)


async def price_order(db: Session, symbol: str) -> PricedOrder:
    """成交價一律由後端取得（最新盤中價或最近收盤價），不接受前端傳入的價格。"""
    entry = await catalog_service.resolve(db, symbol)
    quote = await quote_service.get_quote(entry)
    if quote.price is None:
        raise PriceUnavailableError(f"{entry.symbol} 目前沒有可用的成交價，暫時無法模擬交易", details={"symbol": entry.symbol})
    fx = await fx_service.get_usd_twd() if entry.currency == "USD" else None
    return PricedOrder(entry=entry, quote=quote, price=quote.price, fx=fx)


def _fill(side: str, account: Account, position: Position | None, shares: int, order: PricedOrder) -> Fill:
    apply = apply_buy if side == "BUY" else apply_sell
    return apply(account.cash, to_holding(position), shares, order.price, order.fx_rate)


async def preview_trade(db: Session, request: TradeRequest) -> TradePreviewOut:
    order = await price_order(db, request.symbol)
    account = get_account(db)
    position = find_position(db, account, order.entry.market, order.entry.symbol)
    held = position.shares if position else 0
    common = {
        "symbol": order.entry.symbol,
        "market": order.entry.market,
        "name": order.entry.name,
        "side": request.side,
        "shares": request.shares,
        "price": order.price,
        "currency": order.entry.currency,
        "price_kind": order.quote.kind,
        "price_source": order.quote.source,
        "price_as_of": order.quote.as_of,
        "fx_rate": order.fx_rate,
        "fx_date": order.fx.rate_date if order.fx else None,
        "cash_before": account.cash,
        "shares_held": held,
    }
    try:
        fill = _fill(request.side, account, position, request.shares, order)
    except BusinessRuleError as exc:
        gross, amount = trade_amounts(order.price, request.shares, order.fx_rate)
        return TradePreviewOut(
            **common,
            gross_amount=gross,
            amount_twd=amount,
            fee_twd=Decimal("0"),
            tax_twd=Decimal("0"),
            cash_after=None,
            shares_after=None,
            can_execute=False,
            reason=exc.message,
            reason_code=exc.code,
        )
    return TradePreviewOut(
        **common,
        gross_amount=fill.gross_amount,
        amount_twd=fill.amount_twd,
        fee_twd=fill.fee_twd,
        tax_twd=fill.tax_twd,
        cash_after=fill.cash_after,
        shares_after=fill.holding_after.shares if fill.holding_after else 0,
        estimated_realized_pnl_twd=fill.realized_pnl_twd,
        can_execute=True,
    )


async def execute_trade(db: Session, request: TradeRequest) -> Trade:
    order = await price_order(db, request.symbol)
    entry = order.entry
    # 取得價格之後才讀帳戶，計算與寫入之間沒有任何 await，不會被其他請求插隊
    account = get_account(db)
    position = find_position(db, account, entry.market, entry.symbol)
    fill = _fill(request.side, account, position, request.shares, order)
    now = clock.now()

    try:
        account.cash = fill.cash_after
        account.updated_at = now
        holding = fill.holding_after
        if holding is None:
            if position is not None:
                db.delete(position)
        elif position is None:
            db.add(
                Position(
                    account_id=account.id,
                    market=entry.market,
                    symbol=entry.symbol,
                    name=entry.name,
                    exchange=entry.exchange,
                    currency=entry.currency,
                    shares=holding.shares,
                    avg_cost=holding.avg_cost,
                    cost_basis_twd=holding.cost_basis_twd,
                    opened_at=now,
                    updated_at=now,
                )
            )
        else:
            position.shares = holding.shares
            position.avg_cost = holding.avg_cost
            position.cost_basis_twd = holding.cost_basis_twd
            position.updated_at = now

        trade = Trade(
            account_id=account.id,
            cycle=account.cycle,
            market=entry.market,
            symbol=entry.symbol,
            name=entry.name,
            side=request.side,
            shares=request.shares,
            price=fill.price,
            currency=entry.currency,
            fx_rate=fill.fx_rate,
            fx_date=order.fx.rate_date if order.fx else None,
            gross_amount=fill.gross_amount,
            amount_twd=fill.amount_twd,
            fee_twd=fill.fee_twd,
            tax_twd=fill.tax_twd,
            realized_pnl_twd=fill.realized_pnl_twd,
            cash_after_twd=fill.cash_after,
            price_kind=order.quote.kind,
            price_source=order.quote.source,
            price_as_of=order.quote.as_of,
            created_at=now,
        )
        db.add(trade)
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(trade)
    return trade


def list_trades(db: Session, scope: Literal["current", "all"] = "current", limit: int = 100) -> tuple[Account, list[Trade]]:
    account = get_account(db)
    statement = select(Trade).where(Trade.account_id == account.id)
    if scope == "current":
        statement = statement.where(Trade.cycle == account.cycle)
    statement = statement.order_by(Trade.created_at.desc(), Trade.id.desc()).limit(limit)
    return account, list(db.scalars(statement))


def reset_account(db: Session) -> Account:
    """清空持股、現金回到初始金額，cycle + 1；歷史交易紀錄保留。"""
    account = get_account(db)
    try:
        db.execute(delete(Position).where(Position.account_id == account.id))
        account.cash = account.initial_cash
        account.cycle += 1
        account.reset_at = clock.now()
        account.updated_at = account.reset_at
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(account)
    return account
