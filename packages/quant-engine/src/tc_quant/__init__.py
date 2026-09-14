"""tc_quant — deterministic quantitative engine (§33, Part VII).

Pure, deterministic calculations. AI SHALL NOT perform these (§55, TC-ADR-012): price
math, technical indicators and statistics live here as ordinary code so they are
reproducible, testable and un-overridable.

No numpy/pandas dependency in Phase 0 — plain Python keeps the golden path light. A
vectorised backend can replace the internals later behind the same functions.
"""

from tc_quant.indicators import (
    adx,
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
from tc_quant.regime import RegimeAssessment, classify_regime

__all__ = [
    "sma",
    "ema",
    "stdev",
    "rsi",
    "macd",
    "true_range",
    "atr",
    "adx",
    "roc",
    "bollinger",
    "classify_regime",
    "RegimeAssessment",
]
