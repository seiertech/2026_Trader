"""Risk Engine gate (§73, §77): deterministic APPROVE/REDUCE/REJECT + reasons."""

from __future__ import annotations

from decimal import Decimal

from tc_risk.gate import (
    GateVerdict,
    PortfolioState,
    ProposedTrade,
    RiskReason,
    evaluate,
)

# A permissive control set; individual tests tighten one control at a time.
CONTROLS: dict[str, object] = {
    "MAX_RISK_PER_TRADE": 0.01,
    "MAX_DAILY_LOSS": 0.03,
    "MAX_WEEKLY_LOSS": 0.06,
    "MAX_DRAWDOWN": 0.15,
    "MAX_OPEN_RISK": 0.04,
    "MAX_POSITIONS": 3,
    "MAX_LEVERAGE": 10,
    "MAX_CORRELATED_EXPOSURE": 0.05,
    "MAX_INSTRUMENT_EXPOSURE": 0.02,
    "MIN_REWARD_RISK": 1.5,
    "MAX_SPREAD": None,
    "MAX_SLIPPAGE": None,
    "MAX_CONSECUTIVE_LOSSES": 5,
    "MANDATORY_STOP": True,
    "EVENT_BLACKOUT": True,
    "STALE_DATA_BLOCK": True,
    "KILL_SWITCH": False,
    "KELLY_FRACTION": 0.25,
}


def _trade(**kw) -> ProposedTrade:
    base = dict(
        instrument="XAUUSD", direction="LONG",
        requested_risk_fraction=Decimal("0.01"), reward_risk=Decimal("2.0"),
        has_stop=True, spread=None,
    )
    base.update(kw)
    return ProposedTrade(**base)


def test_clean_trade_approved() -> None:
    r = evaluate(_trade(), PortfolioState(), CONTROLS)
    assert r.verdict is GateVerdict.APPROVE
    assert r.approved_risk_fraction == Decimal("0.01")
    assert r.reasons == ()


def test_kill_switch_rejects() -> None:
    r = evaluate(_trade(), PortfolioState(kill_switch=True), CONTROLS)
    assert r.verdict is GateVerdict.REJECT
    assert RiskReason.KILL_SWITCH in r.reasons
    assert r.approved_risk_fraction == Decimal(0)


def test_missing_stop_rejects() -> None:
    r = evaluate(_trade(has_stop=False), PortfolioState(), CONTROLS)
    assert r.verdict is GateVerdict.REJECT
    assert RiskReason.MANDATORY_STOP_MISSING in r.reasons


def test_reward_risk_below_floor_rejects() -> None:
    r = evaluate(_trade(reward_risk=Decimal("1.0")), PortfolioState(), CONTROLS)
    assert RiskReason.REWARD_RISK_TOO_LOW in r.reasons
    assert r.verdict is GateVerdict.REJECT


def test_stale_data_rejects() -> None:
    r = evaluate(_trade(), PortfolioState(data_is_stale=True), CONTROLS)
    assert RiskReason.STALE_DATA in r.reasons


def test_max_positions_rejects() -> None:
    r = evaluate(_trade(), PortfolioState(open_positions=3), CONTROLS)
    assert RiskReason.MAX_POSITIONS in r.reasons


def test_consecutive_losses_rejects() -> None:
    r = evaluate(_trade(), PortfolioState(consecutive_losses=5), CONTROLS)
    assert RiskReason.MAX_CONSECUTIVE_LOSSES in r.reasons


def test_daily_loss_budget_rejects() -> None:
    r = evaluate(_trade(), PortfolioState(daily_loss_fraction=Decimal("0.03")), CONTROLS)
    assert RiskReason.MAX_DAILY_LOSS in r.reasons


def test_spread_too_wide_rejects() -> None:
    controls = {**CONTROLS, "MAX_SPREAD": 0.50}
    r = evaluate(_trade(spread=Decimal("0.80")), PortfolioState(), controls)
    assert RiskReason.SPREAD_TOO_WIDE in r.reasons


def test_open_risk_reduces_not_rejects() -> None:
    # 0.035 already open, cap 0.04 → only 0.005 headroom; request 0.01 → reduced.
    r = evaluate(_trade(), PortfolioState(open_risk_fraction=Decimal("0.035")), CONTROLS)
    assert r.verdict is GateVerdict.REDUCE
    assert r.approved_risk_fraction == Decimal("0.005")
    assert RiskReason.MAX_OPEN_RISK in r.reasons


def test_open_risk_exhausted_rejects() -> None:
    r = evaluate(_trade(), PortfolioState(open_risk_fraction=Decimal("0.04")), CONTROLS)
    assert r.verdict is GateVerdict.REJECT
    assert RiskReason.MAX_OPEN_RISK in r.reasons


def test_instrument_exposure_reduces() -> None:
    # instrument cap 0.02, already 0.018 → 0.002 headroom; request 0.01 → reduced.
    r = evaluate(_trade(), PortfolioState(instrument_risk_fraction=Decimal("0.018")), CONTROLS)
    assert r.verdict is GateVerdict.REDUCE
    assert r.approved_risk_fraction == Decimal("0.002")
    assert RiskReason.MAX_INSTRUMENT_EXPOSURE in r.reasons


def test_gate_never_raises_risk() -> None:
    # Even with huge headroom, approved never exceeds the requested fraction.
    r = evaluate(_trade(requested_risk_fraction=Decimal("0.005")), PortfolioState(), CONTROLS)
    assert r.approved_risk_fraction == Decimal("0.005")


def test_multiple_hard_breaches_all_reported() -> None:
    r = evaluate(
        _trade(has_stop=False, reward_risk=Decimal("1.0")),
        PortfolioState(kill_switch=True),
        CONTROLS,
    )
    assert r.verdict is GateVerdict.REJECT
    assert RiskReason.KILL_SWITCH in r.reasons
    assert RiskReason.MANDATORY_STOP_MISSING in r.reasons
    assert RiskReason.REWARD_RISK_TOO_LOW in r.reasons
