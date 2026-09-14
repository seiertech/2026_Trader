"""Timeframe aggregation: roll a base timeframe up to higher ones (§35, §110).

Buckets are CALENDAR-ALIGNED, not "every N bars": a 1h bar always starts on the hour,
a 1d bar at 00:00 UTC, etc. This matters — a gap in the data must not shift every
subsequent bucket boundary.

By default only COMPLETE buckets are emitted (a bucket whose full interval is covered
by the available base bars). This preserves no-look-ahead when aggregating a replay
window: a partially-formed higher-timeframe bar is not shown as if it were closed
(§126). ``include_partial=True`` is available for live "current forming bar" display
but is never used in decision paths.

Aggregation rule per bucket: open=first.open, high=max(high), low=min(low),
close=last.close, volume=sum(volume).
"""

from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal

from tc_domain.enums import Timeframe
from tc_domain.market import Bar

# Target timeframe -> its interval length.
_TF_DELTA: dict[Timeframe, timedelta] = {
    Timeframe.M1: timedelta(minutes=1),
    Timeframe.M5: timedelta(minutes=5),
    Timeframe.M15: timedelta(minutes=15),
    Timeframe.H1: timedelta(hours=1),
    Timeframe.H4: timedelta(hours=4),
    Timeframe.D1: timedelta(days=1),
}

# How many base units make up one target unit — only for compatible pairs.
_MINUTES: dict[Timeframe, int] = {
    Timeframe.M1: 1,
    Timeframe.M5: 5,
    Timeframe.M15: 15,
    Timeframe.H1: 60,
    Timeframe.H4: 240,
    Timeframe.D1: 1440,
}


def interval_delta(tf: Timeframe) -> timedelta:
    return _TF_DELTA[tf]


def bucket_start(when: datetime, target: Timeframe) -> datetime:
    """Return the calendar-aligned bucket start for ``when`` at ``target`` timeframe.

    Alignment is relative to the UTC epoch day: minutes/hours align within the day,
    days align at 00:00 UTC.
    """
    minutes = _MINUTES[target]
    if target is Timeframe.D1:
        return when.replace(hour=0, minute=0, second=0, microsecond=0)
    day = when.replace(hour=0, minute=0, second=0, microsecond=0)
    elapsed = int((when - day).total_seconds() // 60)
    aligned = (elapsed // minutes) * minutes
    return day + timedelta(minutes=aligned)


def can_aggregate(base: Timeframe, target: Timeframe) -> bool:
    """True if ``base`` divides evenly into ``target`` and target is not smaller."""
    return _MINUTES[target] >= _MINUTES[base] and _MINUTES[target] % _MINUTES[base] == 0


def aggregate(
    bars: tuple[Bar, ...],
    base: Timeframe,
    target: Timeframe,
    *,
    include_partial: bool = False,
) -> tuple[Bar, ...]:
    """Aggregate ascending ``bars`` from ``base`` to ``target`` timeframe.

    Only complete buckets are returned unless ``include_partial`` is set. A bucket is
    complete when the number of base bars in it equals the expected count
    (target_minutes / base_minutes) — i.e. no missing sub-bars.
    """
    if base is target:
        return bars
    if not can_aggregate(base, target):
        raise ValueError(f"cannot aggregate {base.value} -> {target.value}")
    if not bars:
        return ()

    expected = _MINUTES[target] // _MINUTES[base]
    instrument = bars[0].instrument

    # Group base bars into their target bucket.
    buckets: dict[datetime, list[Bar]] = {}
    for b in bars:
        key = bucket_start(b.open_time, target)
        buckets.setdefault(key, []).append(b)

    out: list[Bar] = []
    for key in sorted(buckets):
        group = sorted(buckets[key], key=lambda x: x.open_time)
        complete = len(group) == expected
        if not complete and not include_partial:
            continue
        out.append(
            Bar(
                instrument=instrument,
                timeframe=target,
                open_time=key,
                open=group[0].open,
                high=max(x.high for x in group),
                low=min(x.low for x in group),
                close=group[-1].close,
                volume=sum((x.volume for x in group), Decimal(0)),
            )
        )
    return tuple(out)
