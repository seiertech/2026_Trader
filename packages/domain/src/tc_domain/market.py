"""Market-data value objects: bars, quotes, and account/position snapshots.

These are the raw factual observations the system reads from a provider (§12, §23).
They are immutable — an observed fact does not change (§124 provenance). All
timestamps are UTC-aware (§125).

A ``Bar`` carries its ``open_time`` (the start of the interval) and ``timeframe``.
No-look-ahead (§126) is a *usage* contract enforced by the replay provider: a bar is
only visible once its interval has closed at or before the replay clock.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, model_validator

from tc_domain.enums import Timeframe


class Bar(BaseModel):
    """A single OHLCV candle for one instrument and timeframe."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    instrument: str
    timeframe: Timeframe
    open_time: datetime  # start of the interval, UTC
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal = Decimal(0)

    @model_validator(mode="after")
    def _check_ohlc(self) -> Bar:
        # High must be the max and low the min — reject malformed candles at the door
        # rather than let bad data corrupt indicators downstream (fail closed).
        if self.high < self.low:
            raise ValueError(f"bar high < low ({self.high} < {self.low})")
        hi = max(self.open, self.close, self.high)
        lo = min(self.open, self.close, self.low)
        if self.high < hi or self.low > lo:
            raise ValueError(
                "bar high/low do not envelope open/close "
                f"(o={self.open} h={self.high} l={self.low} c={self.close})"
            )
        if self.volume < 0:
            raise ValueError("bar volume is negative")
        return self


class Quote(BaseModel):
    """A bid/ask snapshot at an instant (§23). Spread is derived, never stored twice."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    instrument: str
    time: datetime  # UTC
    bid: Decimal
    ask: Decimal

    @model_validator(mode="after")
    def _check(self) -> Quote:
        if self.ask < self.bid:
            raise ValueError(f"quote ask < bid ({self.ask} < {self.bid})")
        return self

    @property
    def spread(self) -> Decimal:
        return self.ask - self.bid

    @property
    def mid(self) -> Decimal:
        return (self.bid + self.ask) / Decimal(2)


class AccountSnapshot(BaseModel):
    """Broker/simulated account state (§23, §94)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    time: datetime
    currency: str
    balance: Decimal
    equity: Decimal
    margin_used: Decimal = Decimal(0)
