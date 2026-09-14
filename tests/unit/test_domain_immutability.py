"""Evidence Pack, Decision and experience records are immutable (§90, TC-ADR-018)."""

from __future__ import annotations

import pytest
from pydantic import ValidationError
from tc_domain.enums import ConvergenceDomain, DecisionOutcome, RegimeType
from tc_domain.evidence import Decision, DomainEvidence, EvidencePack
from tc_domain.instrument import CANONICAL_UNIVERSE, Instrument
from tc_domain.time import ensure_utc, utc_now


def _pack() -> EvidencePack:
    return EvidencePack(
        pack_id="ep-1",
        instrument="XAUUSD",
        decision_timestamp=utc_now(),
        regime=RegimeType.STRONG_TREND,
        domain_evidence=(
            DomainEvidence(
                domain=ConvergenceDomain.MARKET_STRUCTURE,
                strength=80.0,
                rationale="higher highs on 1h/4h",
            ),
        ),
    )


def test_evidence_pack_is_frozen() -> None:
    pack = _pack()
    with pytest.raises(ValidationError):
        pack.instrument = "EURUSD"  # type: ignore[misc]


def test_decision_is_frozen() -> None:
    d = Decision(
        id="d-1",
        opportunity_id="o-1",
        evidence_pack_id="ep-1",
        outcome=DecisionOutcome.WAIT,
        decided_at=utc_now(),
        plain_english="Await breakout confirmation.",
        detailed_evidence="structure strong; momentum strong; macro moderate",
    )
    with pytest.raises(ValidationError):
        d.outcome = DecisionOutcome.LONG  # type: ignore[misc]


def test_instruments_are_frozen() -> None:
    inst: Instrument = CANONICAL_UNIVERSE[0]
    with pytest.raises(ValidationError):
        inst.permission = inst.permission  # type: ignore[misc]


def test_naive_datetime_rejected() -> None:
    import datetime as _dt

    with pytest.raises(ValueError):
        ensure_utc(_dt.datetime(2026, 1, 1, 12, 0, 0))  # naive → rejected (§125)
