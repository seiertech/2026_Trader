"""The replay provider must never reveal a bar before its interval closes (§126)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

from tc_domain.enums import Timeframe
from tc_domain.market import Bar
from tc_market_data.replay import ReplayMarketDataProvider, provider_from_csv

SAMPLE = Path(__file__).resolve().parents[2] / "data" / "reference" / "XAUUSD_1m_sample.csv"


def _bars(n: int) -> tuple[Bar, ...]:
    base = datetime(2026, 1, 5, 0, 0, tzinfo=UTC)
    out = []
    px = Decimal("2650")
    for i in range(n):
        out.append(
            Bar(
                instrument="XAUUSD",
                timeframe=Timeframe.M1,
                open_time=base + timedelta(minutes=i),
                open=px,
                high=px + Decimal("1"),
                low=px - Decimal("1"),
                close=px,
                volume=Decimal("10"),
            )
        )
    return tuple(out)


def test_no_bars_visible_before_first_interval_closes() -> None:
    bars = _bars(3)
    p = ReplayMarketDataProvider("XAUUSD", Timeframe.M1, bars)
    # Clock at the very first open_time: the 1m interval has NOT closed yet.
    p.seek(bars[0].open_time)
    assert p.bars("XAUUSD", Timeframe.M1) == ()
    # One second before close: still not visible.
    p.seek(bars[0].open_time + timedelta(seconds=59))
    assert p.bars("XAUUSD", Timeframe.M1) == ()
    # Exactly at close: now visible.
    p.seek(bars[0].open_time + timedelta(minutes=1))
    assert len(p.bars("XAUUSD", Timeframe.M1)) == 1


def test_step_reveals_one_bar_at_a_time_in_order() -> None:
    bars = _bars(5)
    p = ReplayMarketDataProvider("XAUUSD", Timeframe.M1, bars)
    seen = []
    while (b := p.step()) is not None:
        seen.append(b)
        # Invariant: everything visible is strictly older than the clock.
        for v in p.bars("XAUUSD", Timeframe.M1):
            assert v.open_time + timedelta(minutes=1) <= p.clock
    assert [b.open_time for b in seen] == [b.open_time for b in bars]


def test_sample_csv_loads_and_replays_without_lookahead() -> None:
    p = provider_from_csv(SAMPLE, "XAUUSD", Timeframe.M1)
    assert p.symbols() == ("XAUUSD",)
    # Walk the first 100 steps; visible count must equal steps taken.
    for expected in range(1, 101):
        p.step()
        assert len(p.bars("XAUUSD", Timeframe.M1)) == expected


def test_quote_derives_from_last_closed_bar() -> None:
    p = provider_from_csv(SAMPLE, "XAUUSD", Timeframe.M1)
    assert p.quote("XAUUSD") is None  # nothing closed yet
    p.step()
    q = p.quote("XAUUSD")
    assert q is not None
    assert q.ask > q.bid  # positive spread
