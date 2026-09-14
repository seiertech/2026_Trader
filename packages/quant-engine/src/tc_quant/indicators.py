"""Deterministic technical indicators (§33).

All functions operate on plain float sequences and return aligned lists where each
element corresponds to the input bar at that index. Warm-up positions that cannot yet
be computed are ``None`` — never fabricated — so downstream code can tell "not enough
data" from a real value (no silent zero-fill, which would be a subtle look-ahead-like
lie about certainty).

Conventions:
  * ``ema`` uses the standard smoothing factor 2/(n+1), seeded with the SMA of the
    first ``n`` values (a common, reproducible seeding choice).
  * ``rsi`` uses Wilder's smoothing.
  * ``atr`` uses Wilder's smoothing of True Range.
  * ``adx`` uses Wilder's directional-movement method.
Extraction of OHLC series from Bars is done by the caller (see series.py helpers) so
this module is dependency-free and trivially unit-testable against known values.
"""

from __future__ import annotations

from collections.abc import Sequence
from statistics import fmean, pstdev

Number = float
OptFloat = float | None


def sma(values: Sequence[Number], period: int) -> list[OptFloat]:
    """Simple moving average."""
    if period <= 0:
        raise ValueError("period must be positive")
    out: list[OptFloat] = [None] * len(values)
    for i in range(period - 1, len(values)):
        window = values[i - period + 1 : i + 1]
        out[i] = fmean(window)
    return out


def ema(values: Sequence[Number], period: int) -> list[OptFloat]:
    """Exponential moving average, seeded with the SMA of the first `period` values."""
    if period <= 0:
        raise ValueError("period must be positive")
    out: list[OptFloat] = [None] * len(values)
    if len(values) < period:
        return out
    k = 2.0 / (period + 1)
    seed = fmean(values[:period])
    out[period - 1] = seed
    prev = seed
    for i in range(period, len(values)):
        prev = values[i] * k + prev * (1 - k)
        out[i] = prev
    return out


def stdev(values: Sequence[Number], period: int) -> list[OptFloat]:
    """Rolling population standard deviation."""
    if period <= 0:
        raise ValueError("period must be positive")
    out: list[OptFloat] = [None] * len(values)
    for i in range(period - 1, len(values)):
        out[i] = pstdev(values[i - period + 1 : i + 1])
    return out


def roc(values: Sequence[Number], period: int) -> list[OptFloat]:
    """Rate of change (%) over `period` bars."""
    out: list[OptFloat] = [None] * len(values)
    for i in range(period, len(values)):
        base = values[i - period]
        out[i] = ((values[i] - base) / base * 100.0) if base != 0 else None
    return out


def rsi(values: Sequence[Number], period: int = 14) -> list[OptFloat]:
    """Relative Strength Index (Wilder's smoothing)."""
    out: list[OptFloat] = [None] * len(values)
    if len(values) <= period:
        return out
    gains = 0.0
    losses = 0.0
    for i in range(1, period + 1):
        change = values[i] - values[i - 1]
        gains += max(change, 0.0)
        losses += max(-change, 0.0)
    avg_gain = gains / period
    avg_loss = losses / period
    out[period] = _rsi_from(avg_gain, avg_loss)
    for i in range(period + 1, len(values)):
        change = values[i] - values[i - 1]
        gain = max(change, 0.0)
        loss = max(-change, 0.0)
        avg_gain = (avg_gain * (period - 1) + gain) / period
        avg_loss = (avg_loss * (period - 1) + loss) / period
        out[i] = _rsi_from(avg_gain, avg_loss)
    return out


def _rsi_from(avg_gain: float, avg_loss: float) -> float:
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))


def macd(
    values: Sequence[Number],
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
) -> tuple[list[OptFloat], list[OptFloat], list[OptFloat]]:
    """MACD line, signal line, histogram."""
    ema_fast = ema(values, fast)
    ema_slow = ema(values, slow)
    macd_line: list[OptFloat] = [
        (f - s) if (f is not None and s is not None) else None
        for f, s in zip(ema_fast, ema_slow, strict=True)
    ]
    # Signal EMA computed over the defined portion of the MACD line.
    defined = [(i, v) for i, v in enumerate(macd_line) if v is not None]
    signal_line: list[OptFloat] = [None] * len(values)
    if len(defined) >= signal:
        vals = [v for _, v in defined]
        sig = ema(vals, signal)
        for (idx, _), s in zip(defined, sig, strict=True):
            signal_line[idx] = s
    hist: list[OptFloat] = [
        (m - s) if (m is not None and s is not None) else None
        for m, s in zip(macd_line, signal_line, strict=True)
    ]
    return macd_line, signal_line, hist


def true_range(
    high: Sequence[Number], low: Sequence[Number], close: Sequence[Number]
) -> list[OptFloat]:
    """True Range per bar. First bar TR = high-low (no prior close)."""
    n = len(high)
    out: list[OptFloat] = [None] * n
    for i in range(n):
        if i == 0:
            out[i] = high[i] - low[i]
        else:
            out[i] = max(
                high[i] - low[i],
                abs(high[i] - close[i - 1]),
                abs(low[i] - close[i - 1]),
            )
    return out


def atr(
    high: Sequence[Number],
    low: Sequence[Number],
    close: Sequence[Number],
    period: int = 14,
) -> list[OptFloat]:
    """Average True Range (Wilder's smoothing)."""
    tr = true_range(high, low, close)
    n = len(tr)
    out: list[OptFloat] = [None] * n
    if n < period:
        return out
    seed = fmean([x for x in tr[:period] if x is not None])
    out[period - 1] = seed
    prev = seed
    for i in range(period, n):
        cur = tr[i] or 0.0
        prev = (prev * (period - 1) + cur) / period
        out[i] = prev
    return out


def adx(
    high: Sequence[Number],
    low: Sequence[Number],
    close: Sequence[Number],
    period: int = 14,
) -> list[OptFloat]:
    """Average Directional Index (Wilder). Measures trend STRENGTH, not direction."""
    n = len(high)
    out: list[OptFloat] = [None] * n
    if n <= 2 * period:
        return out

    plus_dm = [0.0] * n
    minus_dm = [0.0] * n
    tr = [0.0] * n
    for i in range(1, n):
        up = high[i] - high[i - 1]
        down = low[i - 1] - low[i]
        plus_dm[i] = up if (up > down and up > 0) else 0.0
        minus_dm[i] = down if (down > up and down > 0) else 0.0
        tr[i] = max(
            high[i] - low[i],
            abs(high[i] - close[i - 1]),
            abs(low[i] - close[i - 1]),
        )

    # Wilder smoothed sums seeded over the first `period` (from index 1).
    atr_s = sum(tr[1 : period + 1])
    pdm_s = sum(plus_dm[1 : period + 1])
    mdm_s = sum(minus_dm[1 : period + 1])

    dx_values: list[float] = []
    for i in range(period + 1, n):
        atr_s = atr_s - (atr_s / period) + tr[i]
        pdm_s = pdm_s - (pdm_s / period) + plus_dm[i]
        mdm_s = mdm_s - (mdm_s / period) + minus_dm[i]
        if atr_s == 0:
            dx_values.append(0.0)
            continue
        plus_di = 100.0 * (pdm_s / atr_s)
        minus_di = 100.0 * (mdm_s / atr_s)
        denom = plus_di + minus_di
        dx = 100.0 * abs(plus_di - minus_di) / denom if denom != 0 else 0.0
        dx_values.append(dx)
        # ADX is available once we have `period` DX values.
        if len(dx_values) == period:
            out[i] = fmean(dx_values)
        elif len(dx_values) > period:
            prev = out[i - 1] or fmean(dx_values[-period:])
            out[i] = (prev * (period - 1) + dx) / period
    return out


def bollinger(
    values: Sequence[Number], period: int = 20, num_std: float = 2.0
) -> tuple[list[OptFloat], list[OptFloat], list[OptFloat]]:
    """Bollinger Bands: (lower, middle, upper)."""
    mid = sma(values, period)
    sd = stdev(values, period)
    lower: list[OptFloat] = [None] * len(values)
    upper: list[OptFloat] = [None] * len(values)
    for i in range(len(values)):
        if mid[i] is not None and sd[i] is not None:
            lower[i] = mid[i] - num_std * sd[i]
            upper[i] = mid[i] + num_std * sd[i]
    return lower, mid, upper
