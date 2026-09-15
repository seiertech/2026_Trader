"""Specialist agents (§58-66): thin assessors, advisory only, never invent facts."""

from __future__ import annotations

from decimal import Decimal

from tc_agents import (
    Assessment,
    EventIntelligenceSpecialist,
    MacroSpecialist,
    MarketLeadersSpecialist,
    MomentumSpecialist,
    PortfolioSpecialist,
    RegimeSpecialist,
    Specialist,
    StructureSpecialist,
    TrendSpecialist,
    VolatilitySpecialist,
    all_specialists,
)
from tc_domain.enums import RegimeType
from tc_leaders import Basket, ConstituentMove, basket_factor
from tc_macro import MacroRelease, macro_convergence_input
from tc_portfolio import OpenPosition, Portfolio
from tc_quant.regime import RegimeAssessment


def _regime(regime=RegimeType.STRONG_TREND, adx=32.0, up=True, ratio=1.0,
            breakout=False, breakdown=False) -> RegimeAssessment:
    return RegimeAssessment(regime, adx, up, ratio, breakout, breakdown, "test")


def test_all_conform_to_protocol() -> None:
    for s in all_specialists():
        assert isinstance(s, Specialist)
        assert s.name


def test_all_return_assessment_with_empty_context() -> None:
    # No context => low-confidence NEUTRAL, never a guess (§44).
    for s in all_specialists():
        a = s.assess({})
        assert isinstance(a, Assessment)
        assert a.confidence <= 0.35
        assert a.overrides_risk is False


def test_regime_specialist() -> None:
    a = RegimeSpecialist().assess({"regime": _regime()})
    assert a.verdict == "STRONG_TREND"


def test_trend_specialist_up_and_down() -> None:
    up = TrendSpecialist().assess({"regime": _regime(up=True)})
    assert up.verdict == "TRENDING_UP" and up.supports == "LONG"
    dn = TrendSpecialist().assess({"regime": _regime(up=False)})
    assert dn.verdict == "TRENDING_DOWN" and dn.supports == "SHORT"


def test_trend_specialist_no_trend_in_range() -> None:
    a = TrendSpecialist().assess({"regime": _regime(regime=RegimeType.RANGE)})
    assert a.verdict == "NO_TREND" and a.supports == "NEITHER"


def test_momentum_extremes() -> None:
    assert MomentumSpecialist().assess({"rsi": 82.0}).supports == "SHORT"
    assert MomentumSpecialist().assess({"rsi": 18.0}).supports == "LONG"
    assert MomentumSpecialist().assess({"rsi": 50.0}).supports == "NEITHER"


def test_structure_breakout_breakdown() -> None:
    assert StructureSpecialist().assess({"regime": _regime(breakout=True)}).verdict == "BREAKOUT"
    assert StructureSpecialist().assess({"regime": _regime(breakdown=True)}).verdict == "BREAKDOWN"


def test_volatility_states() -> None:
    assert VolatilitySpecialist().assess({"regime": _regime(ratio=2.0)}).verdict == "EXPANDING"
    assert VolatilitySpecialist().assess({"regime": _regime(ratio=0.4)}).verdict == "CONTRACTING"
    assert VolatilitySpecialist().assess({"regime": _regime(ratio=1.0)}).verdict == "NORMAL"


def test_macro_specialist_reads_release() -> None:
    r = MacroRelease("CPI", "US", actual=3.4, forecast=3.0, previous=3.1)
    a = MacroSpecialist().assess({"macro_input": macro_convergence_input(r)})
    assert a.supports == "LONG"  # CPI beat => hawkish/bullish
    assert a.confidence > 0


def test_event_specialist_confidence_follows_corroboration() -> None:
    class Ev:
        source_count = 5
        category = "Geopolitics"
        novelty = "NEW"
    a = EventIntelligenceSpecialist().assess({"event": Ev()})
    assert a.confidence == 1.0
    assert a.verdict == "Geopolitics"


def test_event_specialist_flags_blackout() -> None:
    class Ev:
        source_count = 3
        category = "Economy"
        novelty = "NEW"
    a = EventIntelligenceSpecialist().assess({"event": Ev(), "in_blackout": True})
    assert a.verdict == "BLACKOUT"


def test_market_leaders_specialist_uses_one_factor() -> None:
    b = Basket("SEMI", "Semis", "SEMICONDUCTORS", ("NVIDIA", "AMD"))
    f = basket_factor(b, [ConstituentMove("NVIDIA", -3.0), ConstituentMove("AMD", -3.0)])
    a = MarketLeadersSpecialist().assess({"basket_factor": f})
    assert a.supports == "SHORT"
    assert a.confidence > 0


def test_portfolio_specialist_flags_opposing_book() -> None:
    p = Portfolio()
    p.open("1", OpenPosition("XAUUSD", "LONG", Decimal("0.1"), Decimal("2650"),
                             Decimal("2645"), Decimal("0.01")))
    a = PortfolioSpecialist().assess({
        "exposure": p.exposure(), "instrument": "XAUUSD", "direction": "SHORT",
        "has_opposing": p.has_opposing_position("XAUUSD", "SHORT"),
    })
    assert a.verdict == "CONFLICTS_WITH_BOOK"
    assert a.supports == "NEITHER"


def test_no_specialist_can_override_risk() -> None:
    for s in all_specialists():
        a = s.assess({})
        assert a.overrides_risk is False
        assert not hasattr(a, "risk_fraction")
        assert not hasattr(a, "size")
