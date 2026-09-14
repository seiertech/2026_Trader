"""Shadow trade simulator (§79, §84, §85).

Given a decision to enter (direction, entry, stop, target) and the subsequent bars,
simulate a realistic fill and exit and record everything §84 requires: entry, size,
stop, target, spread, estimated slippage, commission, exit, P&L, R, MFE, MAE.

Exit logic per bar after entry:
  * LONG:  stop hit if bar.low <= stop; target hit if bar.high >= target.
  * SHORT: stop hit if bar.high >= stop; target hit if bar.low <= target.
  * If BOTH could hit within the same bar we assume the STOP first (conservative /
    worst-case fill — never flatter the result; §87 honesty).
  * If neither hits by the last bar, exit at the final close ("time exit").

MFE/MAE are tracked in R (favourable/adverse excursion relative to initial risk).
NO broker orders are placed (§79). Money math is Decimal.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from tc_domain.market import Bar

from tc_shadow.account import ShadowAccount
from tc_shadow.costs import CostModel
from tc_shadow.sizing import size_position


@dataclass(frozen=True)
class TradeIntent:
    """A decision to enter, as handed to the simulator."""

    instrument: str
    direction: str  # "LONG" | "SHORT"
    entry_price: Decimal
    stop_price: Decimal
    target_price: Decimal
    decided_at: datetime
    evidence_pack_id: str = ""


@dataclass(frozen=True)
class SimulatedTrade:
    """Immutable record of one simulated trade (§84, §90)."""

    instrument: str
    direction: str
    entry_time: datetime
    exit_time: datetime
    entry_price: Decimal
    stop_price: Decimal
    target_price: Decimal
    exit_price: Decimal
    size: Decimal
    gross_pnl: Decimal
    costs: Decimal
    net_pnl: Decimal
    r_multiple: Decimal
    mfe_r: Decimal
    mae_r: Decimal
    exit_reason: str  # "TARGET" | "STOP" | "TIME"
    evidence_pack_id: str = ""


class ShadowSimulator:
    """Simulates trades against a virtual account with a cost model."""

    def __init__(
        self,
        account: ShadowAccount,
        cost_model: CostModel,
        *,
        risk_fraction: Decimal = Decimal("0.01"),  # §76 initial 1%
    ) -> None:
        self._account = account
        self._costs = cost_model
        self._risk_fraction = risk_fraction

    def simulate(
        self, intent: TradeIntent, future_bars: Sequence[Bar]
    ) -> SimulatedTrade | None:
        """Simulate ``intent`` over ``future_bars`` (bars AT/AFTER the entry bar).

        Returns None if the trade cannot be sized/afforded (§85) — a valid "no trade".
        ``future_bars`` must be the bars available going forward; passing only
        already-known bars keeps the no-look-ahead contract with the caller.
        """
        if intent.direction not in ("LONG", "SHORT"):
            raise ValueError(f"bad direction {intent.direction!r}")
        if not future_bars:
            return None

        entry = intent.entry_price
        stop = intent.stop_price
        target = intent.target_price
        risk_per_unit = abs(entry - stop)
        if risk_per_unit == 0:
            return None  # no stop distance → cannot risk-size (fail closed)

        size = size_position(
            reference_unit=self._account.starting_balance,
            risk_fraction=self._risk_fraction,
            entry_price=entry,
            stop_price=stop,
            value_per_price_unit=self._costs.value_per_price_unit,
        )
        if size <= 0:
            return None
        # §85: a real £250 account could not execute what it cannot afford.
        notional = entry * self._costs.value_per_price_unit * size
        if not self._account.can_afford(notional):
            return None

        long = intent.direction == "LONG"
        entry_time = future_bars[0].open_time
        exit_price = future_bars[-1].close
        exit_time = future_bars[-1].open_time
        exit_reason = "TIME"

        # Track excursions in R.
        best = Decimal(0)   # most favourable (in R)
        worst = Decimal(0)  # most adverse (in R)

        def to_r(move_in_favour: Decimal) -> Decimal:
            return move_in_favour / risk_per_unit

        for bar in future_bars:
            hi, lo = bar.high, bar.low
            # Excursions
            fav = (hi - entry) if long else (entry - lo)
            adv = (entry - lo) if long else (hi - entry)
            best = max(best, to_r(fav))
            worst = min(worst, -to_r(adv))

            stop_hit = (lo <= stop) if long else (hi >= stop)
            target_hit = (hi >= target) if long else (lo <= target)
            if stop_hit and target_hit:
                exit_price, exit_reason = stop, "STOP"  # conservative worst-case
                exit_time = bar.open_time
                break
            if stop_hit:
                exit_price, exit_reason = stop, "STOP"
                exit_time = bar.open_time
                break
            if target_hit:
                exit_price, exit_reason = target, "TARGET"
                exit_time = bar.open_time
                break

        price_move = (exit_price - entry) if long else (entry - exit_price)
        gross = self._costs.pnl_price_to_cash(price_move, size)
        costs = self._costs.estimate(size).total
        net = gross - costs
        r_multiple = price_move / risk_per_unit

        self._account.apply_realised(net)

        return SimulatedTrade(
            instrument=intent.instrument,
            direction=intent.direction,
            entry_time=entry_time,
            exit_time=exit_time,
            entry_price=entry,
            stop_price=stop,
            target_price=target,
            exit_price=exit_price,
            size=size,
            gross_pnl=gross,
            costs=costs,
            net_pnl=net,
            r_multiple=r_multiple,
            mfe_r=best,
            mae_r=worst,
            exit_reason=exit_reason,
            evidence_pack_id=intent.evidence_pack_id,
        )
