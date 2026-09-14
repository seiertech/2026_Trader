"""Strategy family implementations (§71). Deterministic; no edge presumed (TC-ADR-020).

Each strategy is regime-eligible (§72) and returns a Setup or None. Stops are ATR-based
and targets are a reward:risk multiple of the stop distance (>= MIN_REWARD_RISK, §77).
These are RESEARCH strategies — their thresholds are parameters to be evaluated in
Shadow, and any of them may be shown to have no edge (a valid, useful result, §130).
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from decimal import Decimal

from tc_domain.enums import RegimeType
from tc_domain.market import Bar
from tc_quant.indicators import atr, bollinger, ema, rsi
from tc_quant.regime import RegimeAssessment
from tc_quant.series import closes, highs, lows

from tc_strategies.base import Setup


def _atr_stop_target(
    last_close: float, atr_val: float, direction: str, stop_mult: Decimal, rr: Decimal
) -> tuple[Decimal, Decimal, Decimal]:
    entry = Decimal(str(last_close))
    stop_dist = Decimal(str(atr_val)) * stop_mult
    if direction == "LONG":
        return entry, entry - stop_dist, entry + stop_dist * rr
    return entry, entry + stop_dist, entry - stop_dist * rr


@dataclass(frozen=True)
class TrendFollowing:
    """EMA structure + fresh breakout in a trending/breakout regime."""

    name: str = "trend_following"
    eligible_regimes: frozenset[RegimeType] = field(
        default_factory=lambda: frozenset(
            {RegimeType.STRONG_TREND, RegimeType.WEAK_TREND, RegimeType.BREAKOUT}
        )
    )
    ema_fast: int = 12
    ema_slow: int = 26
    atr_period: int = 14
    stop_mult: Decimal = Decimal("1.5")
    reward_risk: Decimal = Decimal("2.0")
    lookback: int = 20

    def find_setup(self, bars: Sequence[Bar], regime: RegimeAssessment) -> Setup | None:
        if regime.regime not in self.eligible_regimes or len(bars) < self.ema_slow + 2:
            return None
        c, h, low = closes(bars), highs(bars), lows(bars)
        ef, es = ema(c, self.ema_fast), ema(c, self.ema_slow)
        a = atr(h, low, c, self.atr_period)
        if ef[-1] is None or es[-1] is None or not a[-1] or a[-1] <= 0:
            return None
        n = len(bars)
        prior_hi = max(h[-self.lookback - 1 : -1]) if n > self.lookback else max(h[:-1])
        prior_lo = min(low[-self.lookback - 1 : -1]) if n > self.lookback else min(low[:-1])
        if ef[-1] > es[-1] and c[-1] > prior_hi:
            e, s, t = _atr_stop_target(c[-1], a[-1], "LONG", self.stop_mult, self.reward_risk)
            return Setup(self.name, "LONG", e, s, t, "uptrend + new high")
        if ef[-1] < es[-1] and c[-1] < prior_lo:
            e, s, t = _atr_stop_target(c[-1], a[-1], "SHORT", self.stop_mult, self.reward_risk)
            return Setup(self.name, "SHORT", e, s, t, "downtrend + new low")
        return None


@dataclass(frozen=True)
class MeanReversion:
    """Fade RSI extremes in a RANGE / low-volatility regime."""

    name: str = "mean_reversion"
    eligible_regimes: frozenset[RegimeType] = field(
        default_factory=lambda: frozenset(
            {RegimeType.RANGE, RegimeType.VOLATILITY_CONTRACTION}
        )
    )
    rsi_period: int = 14
    oversold: float = 30.0
    overbought: float = 70.0
    atr_period: int = 14
    stop_mult: Decimal = Decimal("1.0")
    reward_risk: Decimal = Decimal("1.5")

    def find_setup(self, bars: Sequence[Bar], regime: RegimeAssessment) -> Setup | None:
        if regime.regime not in self.eligible_regimes or len(bars) < self.rsi_period + 5:
            return None
        c, h, low = closes(bars), highs(bars), lows(bars)
        r = rsi(c, self.rsi_period)
        a = atr(h, low, c, self.atr_period)
        if r[-1] is None or not a[-1] or a[-1] <= 0:
            return None
        # Buy oversold, sell overbought — expecting reversion to the mean.
        if r[-1] <= self.oversold:
            e, s, t = _atr_stop_target(c[-1], a[-1], "LONG", self.stop_mult, self.reward_risk)
            return Setup(self.name, "LONG", e, s, t, f"RSI {r[-1]:.0f} oversold in range")
        if r[-1] >= self.overbought:
            e, s, t = _atr_stop_target(c[-1], a[-1], "SHORT", self.stop_mult, self.reward_risk)
            return Setup(self.name, "SHORT", e, s, t, f"RSI {r[-1]:.0f} overbought in range")
        return None


@dataclass(frozen=True)
class MomentumContinuation:
    """Ride established momentum (EMA slope) in a strong trend, pullback entry."""

    name: str = "momentum_continuation"
    eligible_regimes: frozenset[RegimeType] = field(
        default_factory=lambda: frozenset({RegimeType.STRONG_TREND})
    )
    ema_period: int = 20
    atr_period: int = 14
    stop_mult: Decimal = Decimal("2.0")
    reward_risk: Decimal = Decimal("2.0")

    def find_setup(self, bars: Sequence[Bar], regime: RegimeAssessment) -> Setup | None:
        if regime.regime not in self.eligible_regimes or len(bars) < self.ema_period + 5:
            return None
        c, h, low = closes(bars), highs(bars), lows(bars)
        e_ = ema(c, self.ema_period)
        a = atr(h, low, c, self.atr_period)
        if e_[-1] is None or e_[-5] is None or not a[-1] or a[-1] <= 0:
            return None
        slope_up = e_[-1] > e_[-5]
        # Enter in the trend direction on a shallow pullback toward the EMA.
        near_ema = abs(c[-1] - e_[-1]) <= a[-1]
        if slope_up and near_ema and c[-1] >= e_[-1]:
            e, s, t = _atr_stop_target(c[-1], a[-1], "LONG", self.stop_mult, self.reward_risk)
            return Setup(self.name, "LONG", e, s, t, "up-momentum pullback to EMA")
        if (not slope_up) and near_ema and c[-1] <= e_[-1]:
            e, s, t = _atr_stop_target(c[-1], a[-1], "SHORT", self.stop_mult, self.reward_risk)
            return Setup(self.name, "SHORT", e, s, t, "down-momentum pullback to EMA")
        return None


@dataclass(frozen=True)
class VolatilityExpansion:
    """Trade the direction of a Bollinger-band break as volatility expands."""

    name: str = "volatility_expansion"
    eligible_regimes: frozenset[RegimeType] = field(
        default_factory=lambda: frozenset(
            {RegimeType.VOLATILITY_EXPANSION, RegimeType.BREAKOUT}
        )
    )
    bb_period: int = 20
    bb_std: float = 2.0
    atr_period: int = 14
    stop_mult: Decimal = Decimal("1.5")
    reward_risk: Decimal = Decimal("2.0")

    def find_setup(self, bars: Sequence[Bar], regime: RegimeAssessment) -> Setup | None:
        if regime.regime not in self.eligible_regimes or len(bars) < self.bb_period + 5:
            return None
        c, h, low = closes(bars), highs(bars), lows(bars)
        lower, _mid, upper = bollinger(c, self.bb_period, self.bb_std)
        a = atr(h, low, c, self.atr_period)
        if upper[-1] is None or lower[-1] is None or not a[-1] or a[-1] <= 0:
            return None
        if c[-1] > upper[-1]:
            e, s, t = _atr_stop_target(c[-1], a[-1], "LONG", self.stop_mult, self.reward_risk)
            return Setup(self.name, "LONG", e, s, t, "close above upper Bollinger band")
        if c[-1] < lower[-1]:
            e, s, t = _atr_stop_target(c[-1], a[-1], "SHORT", self.stop_mult, self.reward_risk)
            return Setup(self.name, "SHORT", e, s, t, "close below lower Bollinger band")
        return None
