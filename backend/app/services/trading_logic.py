"""模擬交易的核心計算（純函式，不碰資料庫與網路）。

- 金額全部使用 Decimal，台幣金額四捨五入到 0.01
- 買進：可用現金必須足夠；平均成本採加權平均
- 賣出：不可超過持股；已實現損益 = 賣出金額 - 依比例分攤的台幣成本
- 美股以成交當時的 USD/TWD 匯率換算成台幣，台幣成本因此包含匯率
- 第一版不計手續費與證交稅（欄位保留為 0）
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

from app.core.errors import InsufficientFundsError, InsufficientSharesError, InvalidRequestError
from app.core.money import quantize_money

ZERO = Decimal("0")
ONE = Decimal("1")
AVG_COST_PLACES = Decimal("0.000001")


@dataclass(frozen=True)
class Holding:
    shares: int
    avg_cost: Decimal  # 原幣每股平均成本
    cost_basis_twd: Decimal  # 台幣總成本


@dataclass(frozen=True)
class Fill:
    side: str
    shares: int
    price: Decimal
    fx_rate: Decimal
    gross_amount: Decimal  # 原幣成交金額
    amount_twd: Decimal
    fee_twd: Decimal
    tax_twd: Decimal
    realized_pnl_twd: Decimal | None
    cash_before: Decimal
    cash_after: Decimal
    holding_after: Holding | None


def _validate(shares: int, price: Decimal, fx_rate: Decimal) -> None:
    if shares <= 0:
        raise InvalidRequestError("股數必須大於 0")
    if price <= 0:
        raise InvalidRequestError("成交價必須大於 0")
    if fx_rate <= 0:
        raise InvalidRequestError("匯率必須大於 0")


def trade_amounts(price: Decimal, shares: int, fx_rate: Decimal = ONE) -> tuple[Decimal, Decimal]:
    """回傳（原幣成交金額, 台幣成交金額）。"""
    gross = price * shares
    return gross, quantize_money(gross * fx_rate)


def fees_and_taxes(side: str, amount_twd: Decimal) -> tuple[Decimal, Decimal]:
    """手續費與證交稅的擴充點；第一版一律為 0。"""
    return ZERO, ZERO


def apply_buy(cash: Decimal, holding: Holding | None, shares: int, price: Decimal, fx_rate: Decimal = ONE) -> Fill:
    _validate(shares, price, fx_rate)
    gross, amount = trade_amounts(price, shares, fx_rate)
    fee, tax = fees_and_taxes("BUY", amount)
    total_cost = amount + fee + tax
    if total_cost > cash:
        raise InsufficientFundsError(
            f"可用資金不足：需要 NT$ {total_cost:,.2f}，目前可用 NT$ {cash:,.2f}",
            details={"required": str(total_cost), "available": str(cash)},
        )

    old_shares = holding.shares if holding else 0
    old_cost = holding.avg_cost * old_shares if holding else ZERO
    new_shares = old_shares + shares
    new_avg = ((old_cost + gross) / new_shares).quantize(AVG_COST_PLACES, rounding=ROUND_HALF_UP)
    new_basis = (holding.cost_basis_twd if holding else ZERO) + total_cost

    return Fill(
        side="BUY",
        shares=shares,
        price=price,
        fx_rate=fx_rate,
        gross_amount=gross,
        amount_twd=amount,
        fee_twd=fee,
        tax_twd=tax,
        realized_pnl_twd=None,
        cash_before=cash,
        cash_after=cash - total_cost,
        holding_after=Holding(shares=new_shares, avg_cost=new_avg, cost_basis_twd=new_basis),
    )


def apply_sell(cash: Decimal, holding: Holding | None, shares: int, price: Decimal, fx_rate: Decimal = ONE) -> Fill:
    _validate(shares, price, fx_rate)
    held = holding.shares if holding else 0
    if holding is None or shares > held:
        raise InsufficientSharesError(
            f"持股不足：目前持有 {held:,} 股，無法賣出 {shares:,} 股",
            details={"held": held, "requested": shares},
        )

    gross, amount = trade_amounts(price, shares, fx_rate)
    fee, tax = fees_and_taxes("SELL", amount)
    proceeds = amount - fee - tax
    # 全部賣出時把剩餘成本一次扣完，避免四捨五入留下零頭
    cost_removed = holding.cost_basis_twd if shares == held else quantize_money(holding.cost_basis_twd * shares / held)
    remaining = held - shares

    return Fill(
        side="SELL",
        shares=shares,
        price=price,
        fx_rate=fx_rate,
        gross_amount=gross,
        amount_twd=amount,
        fee_twd=fee,
        tax_twd=tax,
        realized_pnl_twd=proceeds - cost_removed,
        cash_before=cash,
        cash_after=cash + proceeds,
        holding_after=None
        if remaining == 0
        else Holding(shares=remaining, avg_cost=holding.avg_cost, cost_basis_twd=holding.cost_basis_twd - cost_removed),
    )


@dataclass(frozen=True)
class Valuation:
    market_value: Decimal  # 原幣市值
    market_value_twd: Decimal
    unrealized_pnl_twd: Decimal
    unrealized_pnl_pct: Decimal | None


def value_holding(holding: Holding, price: Decimal, fx_rate: Decimal = ONE) -> Valuation:
    market_value = price * holding.shares
    market_value_twd = quantize_money(market_value * fx_rate)
    unrealized = market_value_twd - holding.cost_basis_twd
    pct = (unrealized / holding.cost_basis_twd * 100).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP) if holding.cost_basis_twd > 0 else None
    return Valuation(market_value, market_value_twd, unrealized, pct)


def roi_pct(total_assets: Decimal, initial_cash: Decimal) -> Decimal | None:
    if initial_cash <= 0:
        return None
    return ((total_assets - initial_cash) / initial_cash * 100).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
