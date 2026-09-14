"""Forward-outcome labelling (§49, §50, §89).

For a decision made at time T at reference price P (long or short bias), record what
the market subsequently did at each horizon: 5m, 15m, 30m, 1h, 4h, 1d. This is
MANDATORY for every detected opportunity — whether it was traded or rejected (§50:
rejected opportunities must be measured too, so we can ask whether the filters/critic
actually improved expectancy).

No look-ahead into the label itself is a non-issue (a forward label is *supposed* to
look forward), but the label must never leak back into the decision: labels are
computed and stored AFTER the decision timestamp and are keyed to it (§89, §90). The
decision's own Evidence Pack remains immutable.

Return is expressed two ways per horizon:
  * ``price_return`` — signed price change from P over the horizon (raw).
  * ``directional_return`` — price_return oriented to the opportunity's bias, so a
    positive number means "the market moved the way the opportunity expected". For a
    SHORT bias this is the negative of the raw move.

Bars are the base-timeframe series AFTER the decision. A horizon that extends beyond
the available data is labelled ``None`` (not fabricated) — honest about missing data.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal

from tc_domain.market import Bar

# Horizon label -> duration. Mirrors tc_domain.enums.OUTCOME_HORIZONS (§49).
HORIZONS: dict[str, timedelta] = {
    "5m": timedelta(minutes=5),
    "15m": timedelta(minutes=15),
    "30m": timedelta(minutes=30),
    "1h": timedelta(hours=1),
    "4h": timedelta(hours=4),
    "1d": timedelta(days=1),
}


@dataclass(frozen=True)
class ForwardLabel:
    """Forward outcomes for one decision, keyed to its decision timestamp (§49)."""

    decided_at: datetime
    reference_price: Decimal
    bias: str  # "LONG" | "SHORT" — the direction the opportunity expected
    # horizon -> signed price move from reference_price (None if data runs out)
    price_return: dict[str, Decimal | None]
    # horizon -> move oriented to bias (positive = market moved as expected)
    directional_return: dict[str, Decimal | None]

    def outcome_known(self, horizon: str) -> bool:
        return self.price_return.get(horizon) is not None


def label_forward_outcomes(
    decided_at: datetime,
    reference_price: Decimal,
    bias: str,
    future_bars: Sequence[Bar],
) -> ForwardLabel:
    """Compute forward outcomes at each §49 horizon.

    ``future_bars`` are base-timeframe bars at/after ``decided_at`` (ascending). For
    each horizon we take the close of the last bar whose open_time <= decided_at +
    horizon. If no such bar exists (horizon beyond the data), the label is None.
    """
    if bias not in ("LONG", "SHORT"):
        raise ValueError(f"bias must be LONG or SHORT, got {bias!r}")

    price_ret: dict[str, Decimal | None] = {}
    dir_ret: dict[str, Decimal | None] = {}
    sign = Decimal(1) if bias == "LONG" else Decimal(-1)

    # The data "reaches" a horizon only if the last available bar is at or beyond the
    # horizon cutoff. If the series ends before the horizon, that horizon's outcome is
    # genuinely unknown → None (never fabricated from an earlier bar).
    last_open = future_bars[-1].open_time if future_bars else None

    for name, delta in HORIZONS.items():
        cutoff = decided_at + delta
        close_at_horizon: Decimal | None = None
        if last_open is not None and last_open >= cutoff:
            # Take the close of the last bar whose open_time <= cutoff.
            for bar in future_bars:
                if bar.open_time <= cutoff:
                    close_at_horizon = bar.close
                else:
                    break
        if close_at_horizon is None:
            price_ret[name] = None
            dir_ret[name] = None
        else:
            move = close_at_horizon - reference_price
            price_ret[name] = move
            dir_ret[name] = move * sign

    return ForwardLabel(
        decided_at=decided_at,
        reference_price=reference_price,
        bias=bias,
        price_return=price_ret,
        directional_return=dir_ret,
    )
