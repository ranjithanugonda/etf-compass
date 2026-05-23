import pytest

from backend.app.strategy.allocator import (
    get_tranche_amount,
    max_affordable_tranches,
    validate_tranche_schedule,
)
from backend.app.strategy.models import StrategyParams


def test_tranche_1_is_initial() -> None:
    assert get_tranche_amount(1, StrategyParams(initial_tranche=300_000)) == 300_000


def test_tranche_2_is_second() -> None:
    assert get_tranche_amount(2, StrategyParams(second_tranche=200_000)) == 200_000


def test_tranche_3_is_third() -> None:
    assert get_tranche_amount(3, StrategyParams(third_tranche=150_000)) == 150_000


def test_tranche_4_plus_is_addon() -> None:
    assert get_tranche_amount(4, StrategyParams(addon_tranche=100_000)) == 100_000
    assert get_tranche_amount(9, StrategyParams(addon_tranche=100_000)) == 100_000


def test_tranche_zero_raises() -> None:
    with pytest.raises(ValueError):
        get_tranche_amount(0, StrategyParams())


def test_validate_valid_schedule() -> None:
    params = StrategyParams(max_position_size=1_250_000, max_tranches=9)
    valid, msg = validate_tranche_schedule(params)
    assert valid
    assert msg == ""


def test_validate_oversized_schedule() -> None:
    # shrink max to force failure
    params = StrategyParams(
        max_position_size=500_000,
        max_tranches=9,
        initial_tranche=300_000,
        second_tranche=200_000,
    )
    valid, msg = validate_tranche_schedule(params)
    assert not valid
    assert "exceeds" in msg


def test_max_affordable_tranches_normal() -> None:
    params = StrategyParams(max_position_size=1_250_000, max_tranches=9)
    assert max_affordable_tranches(params) == 9


def test_max_affordable_tranches_clipped() -> None:
    params = StrategyParams(
        max_position_size=500_000,
        max_tranches=9,
        initial_tranche=300_000,
        second_tranche=200_000,
        third_tranche=150_000,
        addon_tranche=100_000,
    )
    assert max_affordable_tranches(params) == 2
