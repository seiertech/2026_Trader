"""Deterministic position sizing (§55, §73, §76).

Risk-based sizing: risk a fixed fraction of the reference unit per trade
(MAX_RISK_PER_TRADE, §76 initial 1% => £2.50 on £250) and let the stop distance
determine the position size. AI SHALL NOT do this — it is deterministic risk code
(§55, TC-ADR-012).

    risk_cash   = reference_unit * risk_fraction
    risk_per_unit = |entry - stop| * value_per_price_unit
    size        = risk_cash / risk_per_unit   (0 if stop distance is 0)

The simulator additionally enforces §85: a trade a real £250 account could not
execute is rejected. Sizing itself just returns the maths; the caller applies caps.
"""

from __future__ import annotations

from decimal import ROUND_DOWN, Decimal


def size_position(
    *,
    reference_unit: Decimal,
    risk_fraction: Decimal,
    entry_price: Decimal,
    stop_price: Decimal,
    value_per_price_unit: Decimal = Decimal("1"),
    min_size: Decimal = Decimal("0.01"),
    size_step: Decimal = Decimal("0.01"),
) -> Decimal:
    """Return position size in units, rounded DOWN to ``size_step``.

    Returns Decimal(0) when the stop distance is zero (no valid risk) or the computed
    size is below the broker minimum — both mean "do not trade" (fail closed).
    """
    stop_distance = abs(entry_price - stop_price)
    if stop_distance == 0:
        return Decimal(0)
    risk_cash = reference_unit * risk_fraction
    risk_per_unit = stop_distance * value_per_price_unit
    if risk_per_unit <= 0:
        return Decimal(0)
    raw = risk_cash / risk_per_unit
    # Round DOWN to the tradable step so we never exceed the risk budget.
    stepped = (raw / size_step).to_integral_value(rounding=ROUND_DOWN) * size_step
    if stepped < min_size:
        return Decimal(0)
    return stepped
