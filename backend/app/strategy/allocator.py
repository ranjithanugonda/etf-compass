"""Capital allocator — tranche sizing and validation.

Per CLAUDE.md: tranche sizes and max position size are configurable.
The allocator validates that the configured schedule fits within max_position_size.
"""

from backend.app.strategy.models import StrategyParams


def get_tranche_amount(tranche_number: int, params: StrategyParams) -> float:
    """Return the amount for a given tranche number (1-indexed).

    Schedule:
      1 → initial_tranche
      2 → second_tranche
      3 → third_tranche
      4+ → addon_tranche
    """
    if tranche_number <= 0:
        raise ValueError(f"Tranche number must be >= 1, got {tranche_number}")

    if tranche_number == 1:
        return params.initial_tranche
    if tranche_number == 2:
        return params.second_tranche
    if tranche_number == 3:
        return params.third_tranche
    return params.addon_tranche


def validate_tranche_schedule(params: StrategyParams) -> tuple[bool, str]:
    """Validate that configured tranche sizes fit within max_position_size.

    Sums all tranches from 1 to max_tranches. If the sum exceeds max_position_size,
    returns (False, reason). The caller should either reject or auto-clip.

    Returns (True, "") if valid.
    """
    total = 0.0
    for i in range(1, params.max_tranches + 1):
        total += get_tranche_amount(i, params)

    if total > params.max_position_size:
        return (
            False,
            f"Sum of {params.max_tranches} tranches (₹{total:,.0f}) exceeds "
            f"max_position_size (₹{params.max_position_size:,.0f}). "
            f"Reduce max_tranches or increase max_position_size.",
        )

    return True, ""


def max_affordable_tranches(params: StrategyParams) -> int:
    """Return the maximum number of tranches that fit within max_position_size."""
    total = 0.0
    for i in range(1, params.max_tranches + 1):
        total += get_tranche_amount(i, params)
        if total > params.max_position_size:
            return i - 1
    return params.max_tranches
