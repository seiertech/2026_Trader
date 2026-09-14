"""Regime classifier (§34): deterministic mapping of price behaviour to regime."""

from __future__ import annotations

from tc_domain.enums import RegimeType
from tc_quant.regime import MIN_BARS, classify_regime


def _synth(kind: str, n: int = 120) -> tuple[list[float], list[float], list[float]]:
    highs: list[float] = []
    lows: list[float] = []
    closes: list[float] = []
    p = 100.0
    for i in range(n):
        if kind == "uptrend":
            p += 0.8
        elif kind == "range":
            p += 0.5 if i % 2 == 0 else -0.5
        elif kind == "expansion":
            # calm then a volatility burst at the end
            p += (0.2 if i < n - 15 else (6.0 if i % 2 == 0 else -5.0))
        closes.append(p)
        highs.append(p + 1.0)
        lows.append(p - 1.0)
    return highs, lows, closes


def test_unknown_when_insufficient_data() -> None:
    h = [1.0] * (MIN_BARS - 1)
    r = classify_regime(h, h, h)
    assert r.regime is RegimeType.UNKNOWN


def test_strong_uptrend_detected() -> None:
    h, low, c = _synth("uptrend")
    r = classify_regime(h, low, c)
    assert r.regime in (RegimeType.STRONG_TREND, RegimeType.BREAKOUT)
    assert r.trend_up is True


def test_range_detected() -> None:
    h, low, c = _synth("range")
    r = classify_regime(h, low, c)
    # A choppy flat tape should be RANGE or (at most) WEAK_TREND, never STRONG_TREND.
    assert r.regime in (RegimeType.RANGE, RegimeType.WEAK_TREND, RegimeType.VOLATILITY_CONTRACTION)
    assert r.regime is not RegimeType.STRONG_TREND


def test_volatility_expansion_detected() -> None:
    h, low, c = _synth("expansion")
    r = classify_regime(h, low, c)
    assert r.regime in (RegimeType.VOLATILITY_EXPANSION, RegimeType.BREAKOUT)
    assert r.vol_ratio is not None and r.vol_ratio > 1.0


def test_assessment_retains_evidence() -> None:
    h, low, c = _synth("uptrend")
    r = classify_regime(h, low, c)
    # Score never replaces explainability (§38): the raw signals are kept.
    assert r.adx is not None
    assert r.detail
