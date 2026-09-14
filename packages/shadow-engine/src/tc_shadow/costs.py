"""Cost model for simulated execution (§84).

Every simulated trade must account for spread, estimated slippage and commission —
the point of Shadow is expectancy AFTER costs (§87, §131), so costs are never
optional. Values are research parameters (per-instrument, discovered against Eightcap
later); here they are explicit and conservative.

All amounts are Decimal and expressed in the account currency (GBP) unless noted.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class TradingCosts:
    """Itemised costs for one round-trip trade (entry + exit)."""

    spread_cost: Decimal
    slippage_cost: Decimal
    commission: Decimal

    @property
    def total(self) -> Decimal:
        return self.spread_cost + self.slippage_cost + self.commission


@dataclass(frozen=True)
class CostModel:
    """Estimates trade costs. Research parameters; calibrate against the broker later.

    * ``spread_price`` — typical spread in PRICE units of the instrument (e.g. gold
      quoted in USD/oz, a spread of 0.30 means 30 cents).
    * ``slippage_price`` — estimated adverse slippage per fill in price units.
    * ``commission_per_unit`` — commission per unit of position size, per side.
    * ``value_per_price_unit`` — account-currency value of a 1.0 price move for a
      position size of 1.0 (contract value). For the golden path we model gold as
      1 unit = 1 oz, so a $1 move on 1 unit ≈ the FX-converted value; kept explicit
      and configurable rather than hard-coded broker contract maths.
    """

    spread_price: Decimal = Decimal("0.30")
    slippage_price: Decimal = Decimal("0.10")
    commission_per_unit: Decimal = Decimal("0.02")
    value_per_price_unit: Decimal = Decimal("1")

    def estimate(self, size: Decimal) -> TradingCosts:
        """Round-trip cost for a position of ``size`` units.

        Spread is paid once (crossing the spread on entry); slippage is modeled on
        both entry and exit; commission is charged per side (x2).
        """
        size = abs(size)
        spread_cost = self.spread_price * self.value_per_price_unit * size
        slippage_cost = self.slippage_price * self.value_per_price_unit * size * Decimal(2)
        commission = self.commission_per_unit * size * Decimal(2)
        return TradingCosts(
            spread_cost=spread_cost,
            slippage_cost=slippage_cost,
            commission=commission,
        )

    def pnl_price_to_cash(self, price_move: Decimal, size: Decimal) -> Decimal:
        """Convert a price move × size into account-currency P&L (before costs)."""
        return price_move * self.value_per_price_unit * size
