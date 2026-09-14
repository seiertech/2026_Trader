"""Deterministic Adversarial Critic (§67): VETO/CAUTION/NO_OBJECTION + reason codes."""

from __future__ import annotations

from decimal import Decimal

from tc_decision import CriticInputs, criticise
from tc_domain.enums import CriticVerdict


def _inp(**kw) -> CriticInputs:
    base = dict(
        reward_risk=Decimal("2.0"), has_stop=True, convergence_score=80.0,
        data_is_stale=False, in_event_blackout=False,
        spread=None, caution_spread=Decimal("0.50"),
        consecutive_losses=0, regime_eligible=True,
    )
    base.update(kw)
    return CriticInputs(**base)


def test_no_objection_on_clean_trade() -> None:
    assert criticise(_inp()).verdict is CriticVerdict.NO_OBJECTION


def test_stale_data_vetoes() -> None:
    a = criticise(_inp(data_is_stale=True))
    assert a.verdict is CriticVerdict.VETO
    assert "STALE_DATA" in a.reason_codes


def test_event_blackout_vetoes() -> None:
    assert "EVENT_BLACKOUT" in criticise(_inp(in_event_blackout=True)).reason_codes


def test_missing_stop_vetoes() -> None:
    a = criticise(_inp(has_stop=False))
    assert a.verdict is CriticVerdict.VETO
    assert "NO_STOP" in a.reason_codes


def test_low_reward_risk_vetoes() -> None:
    a = criticise(_inp(reward_risk=Decimal("1.0")))
    assert a.verdict is CriticVerdict.VETO
    assert "REWARD_RISK_TOO_LOW" in a.reason_codes


def test_wide_spread_cautions() -> None:
    a = criticise(_inp(spread=Decimal("0.80")))
    assert a.verdict is CriticVerdict.CAUTION
    assert "WIDE_SPREAD" in a.reason_codes


def test_low_convergence_cautions() -> None:
    a = criticise(_inp(convergence_score=20.0))
    assert a.verdict is CriticVerdict.CAUTION
    assert "LOW_CONVERGENCE" in a.reason_codes


def test_loss_streak_cautions() -> None:
    a = criticise(_inp(consecutive_losses=3))
    assert a.verdict is CriticVerdict.CAUTION
    assert "LOSS_STREAK" in a.reason_codes


def test_ineligible_regime_cautions() -> None:
    a = criticise(_inp(regime_eligible=False))
    assert "REGIME_NOT_ELIGIBLE" in a.reason_codes


def test_veto_beats_caution() -> None:
    # Both a veto (stale) and a caution (low convergence) present → VETO wins.
    a = criticise(_inp(data_is_stale=True, convergence_score=10.0))
    assert a.verdict is CriticVerdict.VETO
    assert "STALE_DATA" in a.reason_codes


def test_multiple_veto_codes_reported() -> None:
    a = criticise(_inp(has_stop=False, reward_risk=Decimal("0.5")))
    assert set(a.reason_codes) >= {"NO_STOP", "REWARD_RISK_TOO_LOW"}
