"""Deterministic replay provider (Shadow) with strict no-look-ahead (§126).

Loads historical bars from a CSV file and serves them *as they would have been known*
at a movable "replay clock". A bar is only visible once its interval has fully closed
at or before the clock — so nothing downstream can ever peek at the future
(mandatory, §89/§126, TC-ADR-018 spirit).

CSV columns (header required):
    open_time,open,high,low,close,volume
``open_time`` is an ISO-8601 UTC timestamp (e.g. 2026-01-05T13:37:00+00:00).

This is the reference MarketDataProvider for the XAUUSD golden path (§123). The live
Mt5 provider implements the same protocol on the Windows edge (ADR-032).
"""

from __future__ import annotations

import csv
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path

from tc_domain.enums import Timeframe
from tc_domain.market import AccountSnapshot, Bar, Quote
from tc_domain.time import ensure_utc, utc_now

# Interval length per timeframe, used to compute when a bar's interval has "closed".
_TF_DELTA: dict[Timeframe, timedelta] = {
    Timeframe.M1: timedelta(minutes=1),
    Timeframe.M5: timedelta(minutes=5),
    Timeframe.M15: timedelta(minutes=15),
    Timeframe.H1: timedelta(hours=1),
    Timeframe.H4: timedelta(hours=4),
    Timeframe.D1: timedelta(days=1),
}


def interval_delta(tf: Timeframe) -> timedelta:
    return _TF_DELTA[tf]


class ReplayMarketDataProvider:
    """A single-instrument, single-base-timeframe replay source.

    The base timeframe is whatever resolution the CSV is in (typically 1m). Aggregation
    to higher timeframes is a separate concern (aggregation module).
    """

    def __init__(
        self,
        instrument: str,
        base_timeframe: Timeframe,
        bars: tuple[Bar, ...],
        *,
        account_currency: str = "GBP",
        starting_balance: Decimal = Decimal(250),  # reference unit (§74)
    ) -> None:
        self._instrument = instrument
        self._tf = base_timeframe
        # Stored oldest→newest, validated ascending by open_time.
        self._bars = tuple(sorted(bars, key=lambda b: b.open_time))
        self._currency = account_currency
        self._balance = starting_balance
        # Clock starts before all data; caller advances it.
        self._clock: datetime = (
            self._bars[0].open_time if self._bars else utc_now()
        )

    # ---- clock control (replay engine drives this) ----

    @property
    def clock(self) -> datetime:
        return self._clock

    def seek(self, when: datetime) -> None:
        self._clock = ensure_utc(when)

    def advance(self, delta: timedelta) -> None:
        self._clock = self._clock + delta

    def step(self) -> Bar | None:
        """Advance the clock to reveal the next bar; return it, or None if exhausted.

        Sets the clock to the moment that bar's interval closes, so the bar is the
        newest *closed* bar visible.
        """
        visible = self.bars(self._instrument, self._tf)
        n = len(visible)
        if n >= len(self._bars):
            return None
        nxt = self._bars[n]
        self._clock = nxt.open_time + interval_delta(self._tf)
        return nxt

    # ---- MarketDataProvider protocol ----

    def symbols(self) -> tuple[str, ...]:
        return (self._instrument,)

    def account(self) -> AccountSnapshot:
        return AccountSnapshot(
            time=self._clock,
            currency=self._currency,
            balance=self._balance,
            equity=self._balance,
        )

    def quote(self, instrument: str) -> Quote | None:
        if instrument != self._instrument:
            return None
        visible = self.bars(instrument, self._tf)
        if not visible:
            return None
        last = visible[-1]
        # Synthetic quote from the last closed bar's close. A tiny symmetric spread is
        # applied so the mid equals close; real spread is modeled in the shadow engine.
        half = Decimal("0.0001") * last.close
        return Quote(
            instrument=instrument,
            time=self._clock,
            bid=last.close - half,
            ask=last.close + half,
        )

    def aggregated_bars(
        self,
        instrument: str,
        timeframe: Timeframe,
        *,
        limit: int | None = None,
    ) -> tuple[Bar, ...]:
        """Bars at a higher ``timeframe``, aggregated from currently-visible base bars.

        No-look-ahead is preserved: only base bars already closed at/before the clock
        feed the aggregation, and only COMPLETE higher-timeframe buckets are returned.
        """
        from tc_market_data.aggregation import aggregate

        if timeframe is self._tf:
            return self.bars(instrument, timeframe, limit=limit)
        base_visible = self.bars(instrument, self._tf)
        rolled = aggregate(base_visible, self._tf, timeframe, include_partial=False)
        return rolled[-limit:] if limit is not None else rolled

    def bars(
        self,
        instrument: str,
        timeframe: Timeframe,
        *,
        since: datetime | None = None,
        limit: int | None = None,
    ) -> tuple[Bar, ...]:
        if instrument != self._instrument or timeframe != self._tf:
            return ()
        delta = interval_delta(timeframe)
        # No-look-ahead: a bar is visible only once its interval has CLOSED at/before
        # the clock (open_time + interval <= clock).  (§126)
        visible = [b for b in self._bars if b.open_time + delta <= self._clock]
        if since is not None:
            since = ensure_utc(since)
            visible = [b for b in visible if b.open_time >= since]
        if limit is not None:
            visible = visible[-limit:]
        return tuple(visible)


def load_bars_csv(
    path: str | Path, instrument: str, timeframe: Timeframe
) -> tuple[Bar, ...]:
    """Load bars from a CSV with header open_time,open,high,low,close,volume."""
    p = Path(path)
    out: list[Bar] = []
    with p.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            out.append(
                Bar(
                    instrument=instrument,
                    timeframe=timeframe,
                    open_time=ensure_utc(datetime.fromisoformat(row["open_time"])),
                    open=Decimal(row["open"]),
                    high=Decimal(row["high"]),
                    low=Decimal(row["low"]),
                    close=Decimal(row["close"]),
                    volume=Decimal(row.get("volume", "0") or "0"),
                )
            )
    return tuple(out)


def provider_from_csv(
    path: str | Path,
    instrument: str,
    timeframe: Timeframe = Timeframe.M1,
    **kwargs: object,
) -> ReplayMarketDataProvider:
    bars = load_bars_csv(path, instrument, timeframe)
    return ReplayMarketDataProvider(instrument, timeframe, bars, **kwargs)  # type: ignore[arg-type]
