"""模擬交易核心計算：買進、賣出、平均成本、損益、Decimal 精確度與匯率。"""

from decimal import Decimal

import pytest

from app.core.errors import InsufficientFundsError, InsufficientSharesError, InvalidRequestError
from app.services.trading_logic import Holding, apply_buy, apply_sell, roi_pct, value_holding

D = Decimal


def test_buy_deducts_cash_and_creates_holding():
    fill = apply_buy(D("1000000"), None, 100, D("2415.00"))

    assert fill.amount_twd == D("241500.00")
    assert fill.cash_after == D("758500.00")
    assert fill.holding_after == Holding(shares=100, avg_cost=D("2415.000000"), cost_basis_twd=D("241500.00"))


def test_buy_rejects_insufficient_funds():
    with pytest.raises(InsufficientFundsError) as error:
        apply_buy(D("1000000"), None, 1000, D("2415"))

    assert "可用資金不足" in error.value.message
    assert error.value.details == {"required": "2415000.00", "available": "1000000"}


def test_buy_exactly_all_cash_is_allowed():
    fill = apply_buy(D("10000"), None, 40, D("250"))

    assert fill.cash_after == D("0")


def test_weighted_average_cost():
    first = apply_buy(D("1000000"), None, 1000, D("100"))
    second = apply_buy(first.cash_after, first.holding_after, 500, D("130"))

    assert second.holding_after.shares == 1500
    assert second.holding_after.avg_cost == D("110.000000")
    assert second.holding_after.cost_basis_twd == D("165000.00")
    assert second.cash_after == D("835000.00")


def test_partial_sell_realizes_pnl_on_average_cost():
    holding = Holding(shares=1500, avg_cost=D("110"), cost_basis_twd=D("165000"))

    fill = apply_sell(D("835000"), holding, 500, D("120"))

    assert fill.amount_twd == D("60000.00")
    assert fill.realized_pnl_twd == D("5000.00")  # 60,000 - 165,000 × 500/1500
    assert fill.cash_after == D("895000.00")
    assert fill.holding_after == Holding(shares=1000, avg_cost=D("110"), cost_basis_twd=D("110000.00"))


def test_selling_everything_removes_holding_and_remaining_cost():
    holding = Holding(shares=3, avg_cost=D("33.333333"), cost_basis_twd=D("100.00"))

    fill = apply_sell(D("0"), holding, 3, D("30"))

    assert fill.holding_after is None
    assert fill.realized_pnl_twd == D("-10.00")


def test_sell_rejects_more_than_held():
    holding = Holding(shares=100, avg_cost=D("10"), cost_basis_twd=D("1000"))

    with pytest.raises(InsufficientSharesError) as error:
        apply_sell(D("0"), holding, 101, D("10"))
    assert error.value.details == {"held": 100, "requested": 101}

    with pytest.raises(InsufficientSharesError):
        apply_sell(D("0"), None, 1, D("10"))


def test_invalid_quantities_are_rejected():
    with pytest.raises(InvalidRequestError):
        apply_buy(D("1000"), None, 0, D("10"))
    with pytest.raises(InvalidRequestError):
        apply_buy(D("1000"), None, 1, D("0"))


def test_decimal_arithmetic_has_no_float_error():
    first = apply_buy(D("1"), None, 1, D("0.1"))
    second = apply_buy(first.cash_after, first.holding_after, 1, D("0.2"))

    assert second.holding_after.cost_basis_twd == D("0.30")
    assert second.cash_after == D("0.70")


def test_us_trade_is_converted_with_fx_rate():
    fill = apply_buy(D("1000000"), None, 10, D("343.83"), fx_rate=D("32.49"))

    assert fill.gross_amount == D("3438.30")
    assert fill.amount_twd == D("111710.37")  # 3,438.30 × 32.49 = 111,710.367 → 四捨五入
    assert fill.holding_after.avg_cost == D("343.830000")


def test_unrealized_pnl_includes_fx_change():
    holding = Holding(shares=10, avg_cost=D("343.83"), cost_basis_twd=D("111710.37"))

    valuation = value_holding(holding, D("343.83"), fx_rate=D("33.00"))

    assert valuation.market_value_twd == D("113463.90")
    assert valuation.unrealized_pnl_twd == D("1753.53")  # 股價不變，只有匯率變動
    assert valuation.unrealized_pnl_pct == D("1.57")


def test_roi():
    assert roi_pct(D("1050000"), D("1000000")) == D("5.00")
    assert roi_pct(D("1000000"), D("0")) is None
