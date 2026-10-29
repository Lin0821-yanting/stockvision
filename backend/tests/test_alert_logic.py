"""價格提醒判斷邏輯：≤、≥、20 日新低、邊緣觸發與觸發模式。"""

from decimal import Decimal

import pytest

from app.services.alert_logic import EVERY_CROSS, NEW_20D_LOW, ONCE, PRICE_GTE, PRICE_LTE, condition_met, evaluate

D = Decimal


@pytest.mark.parametrize(
    ("condition", "price", "target", "expected"),
    [
        (PRICE_LTE, "899.9", "900", True),
        (PRICE_LTE, "900", "900", True),  # 等於也算成立
        (PRICE_LTE, "900.1", "900", False),
        (PRICE_GTE, "1000", "1000", True),
        (PRICE_GTE, "999.99", "1000", False),
    ],
)
def test_price_conditions(condition, price, target, expected):
    assert condition_met(condition, D(price), D(target), None) is expected


def test_new_20_day_low_requires_strictly_lower_price():
    assert condition_met(NEW_20D_LOW, D("2384"), None, D("2385")) is True
    assert condition_met(NEW_20D_LOW, D("2385"), None, D("2385")) is False
    assert condition_met(NEW_20D_LOW, D("2000"), None, None) is False  # 資料不足 20 天不判斷


def test_triggers_only_when_condition_becomes_true():
    first = evaluate(condition=PRICE_LTE, target=D("900"), trigger_mode=EVERY_CROSS, previously_met=False, price=D("890"))
    again = evaluate(condition=PRICE_LTE, target=D("900"), trigger_mode=EVERY_CROSS, previously_met=True, price=D("880"))

    assert first.triggered is True and first.deactivate is False
    assert again.condition_met is True and again.triggered is False  # 仍低於目標價，但不重複通知


def test_every_cross_rearms_after_condition_clears():
    cleared = evaluate(condition=PRICE_LTE, target=D("900"), trigger_mode=EVERY_CROSS, previously_met=True, price=D("950"))
    crossed = evaluate(condition=PRICE_LTE, target=D("900"), trigger_mode=EVERY_CROSS, previously_met=cleared.condition_met, price=D("899"))

    assert cleared.condition_met is False
    assert crossed.triggered is True


def test_once_mode_deactivates_after_trigger():
    result = evaluate(condition=PRICE_GTE, target=D("100"), trigger_mode=ONCE, previously_met=False, price=D("101"))

    assert result.triggered is True and result.deactivate is True


def test_unknown_condition_is_rejected():
    with pytest.raises(ValueError):
        condition_met("PRICE_EQ", D("1"), D("1"), None)
