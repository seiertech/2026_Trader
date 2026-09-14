"""Helpers to extract aligned float series from a sequence of Bars.

Keeps ``indicators`` dependency-free (it only knows floats). Decimal→float conversion
happens here at the boundary; indicator math is fine in float, but any *money* math
(sizing, P&L in the shadow engine) stays in Decimal.
"""

from __future__ import annotations

from collections.abc import Sequence

from tc_domain.market import Bar


def closes(bars: Sequence[Bar]) -> list[float]:
    return [float(b.close) for b in bars]


def highs(bars: Sequence[Bar]) -> list[float]:
    return [float(b.high) for b in bars]


def lows(bars: Sequence[Bar]) -> list[float]:
    return [float(b.low) for b in bars]


def opens(bars: Sequence[Bar]) -> list[float]:
    return [float(b.open) for b in bars]


def volumes(bars: Sequence[Bar]) -> list[float]:
    return [float(b.volume) for b in bars]
