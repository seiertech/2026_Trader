"""Decision Engine (§68–§70): precedence, WAIT first-class, dual explainability."""

from __future__ import annotations

from datetime import UTC, datetime

from tc_decision import DecisionInputs, decide
from tc_domain.enums import CriticVerdict, DecisionOutcome, RegimeType
from tc_domain.evidence import CriticAssessment

T = datetime(2026, 1, 5, 12, 0, tzinfo=UTC)


def _inp(**kw) -> DecisionInputs:
    base = dict(
        opportunity_id="o1", evidence_pack_id="ep1", instrument="XAUUSD",
        bias="LONG", regime=RegimeType.STRONG_TREND, convergence_score=80.0,
        decided_at=T, expired=False, critic=None,
        gate_verdict="APPROVE", gate_reasons=(),
    )
    base.update(kw)
    return DecisionInputs(**base)


def test_clean_long() -> None:
    d = decide(_inp(), decision_id="d1")
    assert d.outcome is DecisionOutcome.LONG
    assert d.id == "d1" and d.opportunity_id == "o1"
    assert d.plain_english and d.detailed_evidence  # both registers present (§101)


def test_clean_short() -> None:
    assert decide(_inp(bias="SHORT"), decision_id="d1").outcome is DecisionOutcome.SHORT


def test_critic_veto_rejects() -> None:
    crit = CriticAssessment(verdict=CriticVerdict.VETO, reason_codes=("OVEREXTENDED",))
    d = decide(_inp(critic=crit), decision_id="d1")
    assert d.outcome is DecisionOutcome.REJECT
    assert "VETO" in d.plain_english


def test_gate_reject_rejects() -> None:
    d = decide(_inp(gate_verdict="REJECT", gate_reasons=("MAX_OPEN_RISK",)), decision_id="d1")
    assert d.outcome is DecisionOutcome.REJECT
    assert "MAX_OPEN_RISK" in d.detailed_evidence


def test_veto_beats_everything_else() -> None:
    # Even with a clean gate and bias, a veto rejects (precedence #1).
    crit = CriticAssessment(verdict=CriticVerdict.VETO, reason_codes=("NEWS_RISK",))
    d = decide(_inp(critic=crit, gate_verdict="APPROVE"), decision_id="d1")
    assert d.outcome is DecisionOutcome.REJECT


def test_expired_rejects() -> None:
    assert decide(_inp(expired=True), decision_id="d1").outcome is DecisionOutcome.REJECT


def test_unclear_bias_waits() -> None:
    d = decide(_inp(bias=""), decision_id="d1")
    assert d.outcome is DecisionOutcome.WAIT  # WAIT is first-class (§70)


def test_critic_caution_waits() -> None:
    crit = CriticAssessment(verdict=CriticVerdict.CAUTION, reason_codes=("THIN_LIQUIDITY",))
    d = decide(_inp(critic=crit), decision_id="d1")
    assert d.outcome is DecisionOutcome.WAIT
    assert "CAUTION" in d.plain_english


def test_gate_reduce_waits() -> None:
    d = decide(_inp(gate_verdict="REDUCE", gate_reasons=("MAX_OPEN_RISK",)), decision_id="d1")
    assert d.outcome is DecisionOutcome.WAIT


def test_no_objection_critic_allows_trade() -> None:
    crit = CriticAssessment(verdict=CriticVerdict.NO_OBJECTION)
    assert decide(_inp(critic=crit), decision_id="d1").outcome is DecisionOutcome.LONG


def test_decision_is_immutable() -> None:
    import pytest
    from pydantic import ValidationError

    d = decide(_inp(), decision_id="d1")
    with pytest.raises(ValidationError):
        d.outcome = DecisionOutcome.REJECT  # type: ignore[misc]
