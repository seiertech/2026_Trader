"""Deterministic indicator maths (§33). Verified against known/hand-computed values."""

from __future__ import annotations

import math

from tc_quant.indicators import (
    atr,
    bollinger,
    ema,
    macd,
    roc,
    rsi,
    sma,
    stdev,
    true_range,
)


def test_sma_basic() -> None:
    vals = [1, 2, 3, 4, 5]
    out = sma(vals, 3)
    assert out[:2] == [None, None]
    assert out[2] == 2.0  # (1+2+3)/3
    assert out[3] == 3.0
    assert out[4] == 4.0


def test_ema_seeds_with_sma_then_smooths() -> None:
    vals = [1, 2, 3, 4, 5, 6]
    out = ema(vals, 3)
    assert out[0] is None and out[1] is None
    assert out[2] == 2.0  # SMA seed of first 3
    # next: 4*0.5 + 2*0.5 = 3.0 ; k = 2/(3+1) = 0.5
    assert out[3] == 3.0
    assert out[4] == 4.0
    assert out[5] == 5.0


def test_stdev_zero_for_constant() -> None:
    out = stdev([5, 5, 5, 5], 4)
    assert out[-1] == 0.0


def test_rsi_all_gains_is_100() -> None:
    vals = list(range(1, 20))  # strictly increasing → no losses
    out = rsi(vals, 14)
    assert out[14] == 100.0


def test_rsi_midrange_for_alternating() -> None:
    vals = []
    p = 100.0
    for i in range(40):
        p += 1 if i % 2 == 0 else -1
        vals.append(p)
    out = rsi(vals, 14)
    last = out[-1]
    assert last is not None
    assert 30.0 < last < 70.0  # choppy → mid-range, not extreme


def test_true_range_and_atr() -> None:
    high = [10, 12, 11, 13]
    low = [8, 9, 9, 11]
    close = [9, 11, 10, 12]
    tr = true_range(high, low, close)
    assert tr[0] == 2.0  # high-low
    # bar1: max(12-9, |12-9|, |9-9|) = 3
    assert tr[1] == 3.0
    a = atr(high, low, close, 2)
    assert a[1] is not None


def test_macd_shapes_align() -> None:
    vals = [float(i) for i in range(60)]
    line, signal, hist = macd(vals)
    assert len(line) == len(signal) == len(hist) == 60
    # For a linear ramp, once warmed, MACD line is positive (fast > slow).
    assert line[-1] is not None and line[-1] > 0


def test_roc() -> None:
    vals = [100, 110, 121]
    out = roc(vals, 1)
    assert out[1] is not None and math.isclose(out[1], 10.0)
    assert out[2] is not None and math.isclose(out[2], 10.0, rel_tol=1e-9)


def test_bollinger_envelops_price() -> None:
    vals = [10.0 + math.sin(i / 3) for i in range(40)]
    lower, mid, upper = bollinger(vals, 20, 2.0)
    i = 39
    assert lower[i] is not None and mid[i] is not None and upper[i] is not None
    assert lower[i] < mid[i] < upper[i]
