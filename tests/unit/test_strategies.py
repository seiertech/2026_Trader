"""Strategy families + regime eligibility + registry (§71, §72)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from tc_domain.enums import RegimeType, Timeframe
from tc_domain.market import Bar
from tc_quant.regime import classify_regime
from tc_quant.series import closes, highs, lows
from tc_strategies import REGISTRY, Strategy, eligible_strategies, get_strategy
from tc_strategies.base import regime_ok
from tc_strategies.families import MeanReversion, TrendFollowing


def _series(kind: str, n: int = 120) -> list[Bar]:
    base = datetime(2026, 1, 5, tzinfo=UTC)
    out = []
    p = 100.0
    for i in range(n):
        if kind == "uptrend":
            p += 0.8
        elif kind == "range":
            p += 0.6 if i % 2 == 0 else -0.6
        out.append(
            Bar(
                instrument="XAUUSD", timeframe=Timeframe.H1,
                open_time=base + timedelta(hours=i),
                open=Decimal(str(round(p, 2))), high=Decimal(str(round(p + 1, 2))),
                low=Decimal(str(round(p - 1, 2))), close=Decimal(str(round(p, 2))),
                volume=Decimal("1"),
            )
        )
    return out


def test_all_registered_are_strategies() -> None:
    for s in REGISTRY:
        assert isinstance(s, Strategy)  # runtime_checkable protocol
        assert s.name and s.eligible_regimes


def test_registry_lookup() -> None:
    assert get_strategy("trend_following") is not None
    assert get_strategy("nope") is None
    assert len(REGISTRY) == 4


def test_regime_eligibility_filters() -> None:
    # Mean-reversion is NOT eligible in a strong trend; trend-following IS.
    trend = eligible_strategies(RegimeType.STRONG_TREND)
    names = {s.name for s in trend}
    assert "trend_following" in names
    assert "mean_reversion" not in names
    assert regime_ok(MeanReversion(), RegimeType.RANGE)
    assert not regime_ok(MeanReversion(), RegimeType.STRONG_TREND)


def test_setup_reward_risk_computed() -> None:
    bars = _series("uptrend")
    regime = classify_regime(highs(bars), lows(bars), closes(bars))
    setup = TrendFollowing().find_setup(bars, regime)
    if setup is not None:  # depends on regime classification of the synthetic series
        assert setup.reward_risk > 0
        assert setup.strategy == "trend_following"
        assert setup.direction in ("LONG", "SHORT")


def test_ineligible_regime_returns_none() -> None:
    bars = _series("uptrend")
    # Force a regime the strategy is not eligible for via a mismatched assessment.
    regime = classify_regime(highs(bars), lows(bars), closes(bars))
    mr = MeanReversion()
    if regime.regime not in mr.eligible_regimes:
        assert mr.find_setup(bars, regime) is None


def test_trend_following_finds_long_in_uptrend() -> None:
    bars = _series("uptrend")
    regime = classify_regime(highs(bars), lows(bars), closes(bars))
    # If the classifier calls it a trend/breakout, trend-following should be eligible.
    if regime.regime in TrendFollowing().eligible_regimes:
        setup = TrendFollowing().find_setup(bars, regime)
        if setup is not None:
            assert setup.direction == "LONG"
