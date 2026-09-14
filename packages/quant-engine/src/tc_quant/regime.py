"""Deterministic market-regime classifier (§34).

Maps recent price behaviour to one of the regime types in the taxonomy. This is a
*deterministic* first-pass classifier — the Regime Specialist agent (§58) may later
add interpretation, but the numeric regime call itself stays deterministic (§55).

Signals used (all from tc_quant.indicators):
  * ADX      → trend strength
  * EMA fast vs slow → trend direction / structure
  * ATR now vs ATR baseline → volatility expansion / contraction
  * Bollinger band width vs recent → range vs breakout
  * price vs recent high/low → breakout detection

The thresholds are explicit constants (not magic numbers buried in logic) and are
research parameters to be calibrated in Shadow (§150 note: config-controlled and
empirically calibrated). EVENT_DRIVEN is NOT inferred from price here — it is set by
the event engine (Phase 4) and passed in; price alone cannot know an event fired.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from tc_domain.enums import RegimeType

from tc_quant.indicators import adx, atr, ema

# --- Thresholds (research parameters; calibrate in Shadow, §150) -------------------
ADX_STRONG = 25.0            # ADX above → strong trend
ADX_WEAK = 18.0             # ADX above (but below strong) → weak trend
VOL_EXPANSION_RATIO = 1.6   # current ATR / baseline ATR above → expansion
VOL_CONTRACTION_RATIO = 0.6  # below → contraction
BREAKOUT_LOOKBACK = 20       # bars for recent high/low breakout test
MIN_BARS = 40                # below this we cannot responsibly classify


@dataclass(frozen=True)
class RegimeAssessment:
    """Result of a regime classification, with the evidence retained (§38)."""

    regime: RegimeType
    adx: float | None
    trend_up: bool | None
    vol_ratio: float | None
    breakout: bool
    breakdown: bool
    detail: str


def classify_regime(
    highs: Sequence[float],
    lows: Sequence[float],
    closes: Sequence[float],
    *,
    ema_fast: int = 12,
    ema_slow: int = 26,
    adx_period: int = 14,
    atr_period: int = 14,
) -> RegimeAssessment:
    """Classify the regime as of the LAST bar in the given series.

    Uses only the provided bars (no look-ahead: the caller passes the visible window).
    Returns UNKNOWN when there is not enough data — never guesses.
    """
    n = len(closes)
    if n < MIN_BARS:
        return RegimeAssessment(
            RegimeType.UNKNOWN, None, None, None, False, False,
            f"insufficient data ({n} < {MIN_BARS} bars)",
        )

    adx_series = adx(highs, lows, closes, adx_period)
    ema_f = ema(closes, ema_fast)
    ema_s = ema(closes, ema_slow)
    atr_series = atr(highs, lows, closes, atr_period)

    cur_adx = adx_series[-1]
    trend_up = (
        None
        if ema_f[-1] is None or ema_s[-1] is None
        else ema_f[-1] > ema_s[-1]
    )

    # Volatility ratio: latest ATR vs the ATR ~lookback bars ago.
    vol_ratio: float | None = None
    if atr_series[-1] is not None:
        baseline_idx = max(0, n - 1 - BREAKOUT_LOOKBACK)
        baseline = atr_series[baseline_idx]
        if baseline:
            vol_ratio = atr_series[-1] / baseline

    # Breakout / breakdown vs recent extremes (exclude the current bar).
    if n > BREAKOUT_LOOKBACK:
        window_hi = max(highs[-BREAKOUT_LOOKBACK - 1 : -1])
        window_lo = min(lows[-BREAKOUT_LOOKBACK - 1 : -1])
    else:
        window_hi = max(highs[:-1])
        window_lo = min(lows[:-1])
    breakout = closes[-1] > window_hi
    breakdown = closes[-1] < window_lo

    regime, detail = _decide(cur_adx, trend_up, vol_ratio, breakout, breakdown)
    return RegimeAssessment(
        regime=regime,
        adx=cur_adx,
        trend_up=trend_up,
        vol_ratio=vol_ratio,
        breakout=breakout,
        breakdown=breakdown,
        detail=detail,
    )


def _decide(
    cur_adx: float | None,
    trend_up: bool | None,
    vol_ratio: float | None,
    breakout: bool,
    breakdown: bool,
) -> tuple[RegimeType, str]:
    # Volatility extremes first — they dominate the character of the tape.
    if vol_ratio is not None and vol_ratio >= VOL_EXPANSION_RATIO:
        # Expansion coinciding with a fresh extreme reads as a breakout regime.
        if breakout or breakdown:
            return RegimeType.BREAKOUT, f"vol expansion (x{vol_ratio:.2f}) + fresh extreme"
        return RegimeType.VOLATILITY_EXPANSION, f"vol expansion (x{vol_ratio:.2f})"

    if cur_adx is not None and cur_adx >= ADX_STRONG:
        return RegimeType.STRONG_TREND, f"ADX {cur_adx:.1f} ≥ {ADX_STRONG}"
    if cur_adx is not None and cur_adx >= ADX_WEAK:
        return RegimeType.WEAK_TREND, f"ADX {cur_adx:.1f} ≥ {ADX_WEAK}"

    if vol_ratio is not None and vol_ratio <= VOL_CONTRACTION_RATIO:
        return RegimeType.VOLATILITY_CONTRACTION, f"vol contraction (x{vol_ratio:.2f})"

    # Low ADX, normal volatility, no fresh extreme → ranging.
    return RegimeType.RANGE, "low ADX, contained volatility"
