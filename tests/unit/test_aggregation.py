"""Timeframe aggregation: calendar-aligned, complete-bucket-only (§35, §126)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

from tc_domain.enums import Timeframe
from tc_domain.market import Bar
from tc_market_data.aggregation import aggregate, bucket_start, can_aggregate
from tc_market_data.replay import provider_from_csv

SAMPLE = Path(__file__).resolve().parents[2] / "data" / "reference" / "XAUUSD_1m_sample.csv"


def _min_bars(n: int, start: datetime | None = None) -> tuple[Bar, ...]:
    base = start or datetime(2026, 1, 5, 0, 0, tzinfo=UTC)
    out = []
    for i in range(n):
        px = Decimal(2650 + i)
        out.append(
            Bar(
                instrument="XAUUSD",
                timeframe=Timeframe.M1,
                open_time=base + timedelta(minutes=i),
                open=px,
                high=px + Decimal("2"),
                low=px - Decimal("2"),
                close=px + Decimal("1"),
                volume=Decimal("10"),
            )
        )
    return tuple(out)


def test_bucket_alignment() -> None:
    t = datetime(2026, 1, 5, 13, 37, tzinfo=UTC)
    assert bucket_start(t, Timeframe.M5) == datetime(2026, 1, 5, 13, 35, tzinfo=UTC)
    assert bucket_start(t, Timeframe.M15) == datetime(2026, 1, 5, 13, 30, tzinfo=UTC)
    assert bucket_start(t, Timeframe.H1) == datetime(2026, 1, 5, 13, 0, tzinfo=UTC)
    assert bucket_start(t, Timeframe.H4) == datetime(2026, 1, 5, 12, 0, tzinfo=UTC)
    assert bucket_start(t, Timeframe.D1) == datetime(2026, 1, 5, 0, 0, tzinfo=UTC)


def test_can_aggregate_rules() -> None:
    assert can_aggregate(Timeframe.M1, Timeframe.M5)
    assert can_aggregate(Timeframe.M1, Timeframe.H1)
    assert not can_aggregate(Timeframe.M5, Timeframe.M1)  # can't go smaller


def test_ohlcv_rollup_is_correct() -> None:
    bars = _min_bars(5)  # exactly one 5m bucket, aligned at :00
    agg = aggregate(bars, Timeframe.M1, Timeframe.M5)
    assert len(agg) == 1
    b = agg[0]
    assert b.timeframe is Timeframe.M5
    assert b.open == bars[0].open
    assert b.close == bars[-1].close
    assert b.high == max(x.high for x in bars)
    assert b.low == min(x.low for x in bars)
    assert b.volume == sum((x.volume for x in bars), Decimal(0))


def test_incomplete_bucket_excluded_by_default() -> None:
    # 7 one-minute bars = one full 5m bucket + a partial (2 bars) second bucket.
    bars = _min_bars(7)
    agg = aggregate(bars, Timeframe.M1, Timeframe.M5)
    assert len(agg) == 1  # partial bucket dropped (no-look-ahead)
    agg_partial = aggregate(bars, Timeframe.M1, Timeframe.M5, include_partial=True)
    assert len(agg_partial) == 2


def test_replay_aggregated_bars_preserve_no_lookahead() -> None:
    p = provider_from_csv(SAMPLE, "XAUUSD", Timeframe.M1)
    # Advance exactly 5 minutes of base bars.
    for _ in range(5):
        p.step()
    m5 = p.aggregated_bars("XAUUSD", Timeframe.M5)
    # First 5 aligned 1m bars (00:00-00:04) form the 00:00 bucket → exactly one M5 bar.
    assert len(m5) == 1
    assert m5[0].timeframe is Timeframe.M5

    # Advance to 60 base bars → one full H1 bar available.
    for _ in range(55):
        p.step()
    h1 = p.aggregated_bars("XAUUSD", Timeframe.H1)
    assert len(h1) == 1
