"""投資組合估值：持股以最新報價（與目前匯率）計算市值、未實現損益、總資產與報酬率。"""

from __future__ import annotations

from collections import defaultdict
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import clock
from app.core.errors import AppError
from app.core.money import quantize_money
from app.models.account import Position, Trade
from app.models.user import User
from app.schemas.market import FxRateOut
from app.schemas.trading import PortfolioOut, PositionOut
from app.services import fx_service, quote_service
from app.services.entities import StockEntry
from app.services.trading_logic import ONE, ZERO, roi_pct, value_holding
from app.services.trading_service import account_out, get_account, to_holding


def _realized_by_symbol(db: Session, account_id: int, cycle: int) -> dict[tuple[str, str], Decimal]:
    totals: dict[tuple[str, str], Decimal] = defaultdict(lambda: ZERO)
    trades = db.scalars(
        select(Trade).where(Trade.account_id == account_id, Trade.cycle == cycle, Trade.side == "SELL")
    )
    for trade in trades:
        totals[(trade.market, trade.symbol)] += trade.realized_pnl_twd or ZERO
    return totals


async def get_portfolio(db: Session, user: User) -> PortfolioOut:
    account = get_account(db, user)
    positions = list(db.scalars(select(Position).where(Position.account_id == account.id).order_by(Position.id)))
    entries = [StockEntry(p.market, p.symbol, p.name, p.exchange) for p in positions]
    results = {r.entry.key: r for r in await quote_service.get_quotes(entries)} if entries else {}

    warnings: list[str] = []
    fx: FxRateOut | None = None
    if any(p.currency == "USD" for p in positions):
        try:
            fx = await fx_service.get_usd_twd()
        except AppError as exc:
            warnings.append(f"無法取得 USD/TWD 匯率，美股市值暫時無法換算：{exc.message}")

    realized = _realized_by_symbol(db, account.id, account.cycle)
    rows: list[PositionOut] = []
    market_value_total = ZERO
    cost_total = ZERO
    unrealized_total = ZERO
    incomplete = False

    for position, entry in zip(positions, entries):
        result = results.get(entry.key)
        quote = result.quote if result else None
        fx_rate = ONE if position.currency == "TWD" else (fx.rate if fx else None)
        holding = to_holding(position)
        cost_total += position.cost_basis_twd

        valuation = None
        quote_error = None
        if quote is None or quote.price is None:
            quote_error = result.error.message if result and result.error else "目前取不到價格"
        elif fx_rate is None:
            quote_error = "匯率暫時無法取得"
        else:
            valuation = value_holding(holding, quote.price, fx_rate)
            market_value_total += valuation.market_value_twd
            unrealized_total += valuation.unrealized_pnl_twd

        if valuation is None:
            incomplete = True
            warnings.append(f"{position.symbol} {position.name}：{quote_error}，未計入總市值")

        rows.append(
            PositionOut(
                symbol=position.symbol,
                market=position.market,
                name=position.name,
                exchange=position.exchange,
                currency=position.currency,
                shares=position.shares,
                avg_cost=position.avg_cost,
                cost_basis_twd=position.cost_basis_twd,
                current_price=quote.price if quote else None,
                day_change_pct=quote.change_pct if quote else None,
                price_kind=quote.kind if quote else None,
                price_source=quote.source if quote else None,
                price_as_of=quote.as_of if quote else None,
                fx_rate=fx_rate,
                market_value=valuation.market_value if valuation else None,
                market_value_twd=valuation.market_value_twd if valuation else None,
                unrealized_pnl_twd=valuation.unrealized_pnl_twd if valuation else None,
                unrealized_pnl_pct=valuation.unrealized_pnl_pct if valuation else None,
                realized_pnl_twd=realized.get((position.market, position.symbol), ZERO),
                weight_pct=None,
                quote_error=quote_error,
            )
        )

    if market_value_total > 0:
        for row in rows:
            if row.market_value_twd is not None:
                row.weight_pct = (row.market_value_twd / market_value_total * 100).quantize(
                    Decimal("0.01"), rounding=ROUND_HALF_UP
                )

    realized_total = sum(realized.values(), ZERO)
    total_assets = account.cash + market_value_total
    return PortfolioOut(
        account=account_out(account),
        positions=rows,
        cash_twd=account.cash,
        market_value_twd=quantize_money(market_value_total),
        cost_basis_twd=quantize_money(cost_total),
        unrealized_pnl_twd=quantize_money(unrealized_total),
        realized_pnl_twd=quantize_money(realized_total),
        total_assets_twd=quantize_money(total_assets),
        total_pnl_twd=quantize_money(total_assets - account.initial_cash),
        roi_pct=roi_pct(total_assets, account.initial_cash),
        fx=fx,
        incomplete=incomplete,
        warnings=warnings,
        as_of=clock.now(),
    )
