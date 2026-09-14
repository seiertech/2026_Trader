"""A minimal deterministic trend/breakout strategy for the golden path.

IMPORTANT: this is a PIPELINE-PROVING strategy, not a validated edge. No strategy is
presumed profitable (TC-ADR-020, §71). Its only job is to occasionally emit a
well-formed LONG/SHORT intent from the visible (no-look-ahead) bars so the shadow
simulator and metrics have something to measure.

Rule (regime-aware, §34/§72):
  * Only consider entries when the regime is a trend or a breakout.
  * LONG when EMA-fast > EMA-slow and the last close makes a new recent high.
  * SHORT when EMA-fast < EMA-slow and the last close makes a new recent low.
  * Stop = ATR-multiple from entry; target = reward:risk multiple of the stop distance
    (>= MIN_REWARD_RISK, §77).
Returns None (WAIT/REJECT) when no clean setup exists — NO OPPORTUNITY is valid (§3).
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal

from tc_domain.enums import RegimeType
from tc_domain.market import Bar
from tc_quant.indicators import atr, ema
from tc_quant.regime import RegimeAssessment
from tc_quant.series import closes, highs, lows

_TREND_REGIMES = {RegimeType.STRONG_TREND, RegimeType.WEAK_TREND, RegimeType.BREAKOUT}


@dataclass(frozen=True)
class Setup:
    direction: str  # "LONG" | "SHORT"
    entry_price: Decimal
    stop_price: Decimal
    target_price: Decimal
    rationale: str


def find_setup(
    bars: Sequence[Bar],
    regime: RegimeAssessment,
    *,
    ema_fast: int = 12,
    ema_slow: int = 26,
    atr_period: int = 14,
    atr_stop_mult: Decimal = Decimal("1.5"),
    reward_risk: Decimal = Decimal("2.0"),
    breakout_lookback: int = 20,
) -> Setup | None:
    """Return a Setup from the visible ``bars`` or None (no clean opportunity)."""
    if regime.regime not in _TREND_REGIMES:
        return None
    n = len(bars)
    if n < ema_slow + 2:
        return None

    c = closes(bars)
    h = highs(bars)
    low = lows(bars)
    ef = ema(c, ema_fast)
    es = ema(c, ema_slow)
    a = atr(h, low, c, atr_period)
    if ef[-1] is None or es[-1] is None or a[-1] is None or a[-1] <= 0:
        return None

    last_close = Decimal(str(c[-1]))
    atr_val = Decimal(str(a[-1]))
    stop_dist = atr_val * atr_stop_mult
    if stop_dist <= 0:
        return None

    prior_hi = max(h[-breakout_lookback - 1 : -1]) if n > breakout_lookback else max(h[:-1])
    prior_lo = min(low[-breakout_lookback - 1 : -1]) if n > breakout_lookback else min(low[:-1])

    up = ef[-1] > es[-1]
    down = ef[-1] < es[-1]

    if up and c[-1] > prior_hi:
        return Setup(
            direction="LONG",
            entry_price=last_close,
            stop_price=last_close - stop_dist,
            target_price=last_close + stop_dist * reward_risk,
            rationale=f"uptrend (EMA{ema_fast}>EMA{ema_slow}) + new {breakout_lookback}-bar high",
        )
    if down and c[-1] < prior_lo:
        return Setup(
            direction="SHORT",
            entry_price=last_close,
            stop_price=last_close + stop_dist,
            target_price=last_close - stop_dist * reward_risk,
            rationale=f"downtrend (EMA{ema_fast}<EMA{ema_slow}) + new {breakout_lookback}-bar low",
        )
    return None
