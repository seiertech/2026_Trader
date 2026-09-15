"""Opportunity lifecycle (§40-42, §70, §90)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from tc_domain.enums import OpportunityOrigin
from tc_opportunity import OpportunityEngine

T0 = datetime(2026, 1, 5, 10, 0, tzinfo=UTC)


def _engine() -> OpportunityEngine:
    e = OpportunityEngine()
    e.detect(opportunity_id="o1", instrument="XAUUSD",
             origin=OpportunityOrigin.CONVERGENCE, detected_at=T0,
             convergence_score=80.0, ttl=timedelta(hours=2))
    return e


def test_detect_sets_expiry() -> None:
    e = _engine()
    rec = e.get("o1")
    assert rec is not None
    assert rec.opportunity.expires_at == T0 + timedelta(hours=2)  # §42 must expire


def test_live_then_expired() -> None:
    e = _engine()
    assert len(e.live(T0 + timedelta(minutes=30))) == 1
    assert len(e.live(T0 + timedelta(hours=3))) == 0
    assert len(e.expired(T0 + timedelta(hours=3))) == 1


def test_wait_keeps_opportunity_live() -> None:
    e = _engine()
    rec = e.reassess("o1", at=T0 + timedelta(minutes=10), outcome="WAIT")
    assert not rec.resolved                    # WAIT is first-class (§70)
    assert rec.latest_outcome == "WAIT"
    assert len(e.live(T0 + timedelta(minutes=20))) == 1


def test_reassessment_is_append_only() -> None:
    e = _engine()
    e.reassess("o1", at=T0 + timedelta(minutes=5), outcome="WAIT", note="await confirm")
    rec = e.reassess("o1", at=T0 + timedelta(minutes=15), outcome="WAIT", note="still flat")
    # History accumulates; nothing is edited (§90, TC-ADR-018).
    assert len(rec.assessments) == 2
    assert rec.assessments[0][2] == "await confirm"


def test_trade_resolves() -> None:
    e = _engine()
    rec = e.reassess("o1", at=T0 + timedelta(minutes=5), outcome="LONG")
    assert rec.resolved
    assert e.live(T0 + timedelta(minutes=10)) == ()


def test_reassess_after_expiry_is_rejected() -> None:
    e = _engine()
    rec = e.reassess("o1", at=T0 + timedelta(hours=5), outcome="LONG")
    # Stale opportunities are REJECTED regardless of what the caller asked for (§42).
    assert rec.latest_outcome == "REJECT"
    assert rec.resolved


def test_expire_stale_sweeps() -> None:
    e = _engine()
    rejected = e.expire_stale(T0 + timedelta(hours=6))
    assert len(rejected) == 1
    assert rejected[0].latest_outcome == "REJECT"


def test_cannot_reassess_resolved() -> None:
    e = _engine()
    e.reassess("o1", at=T0 + timedelta(minutes=5), outcome="LONG")
    with pytest.raises(ValueError):
        e.reassess("o1", at=T0 + timedelta(minutes=6), outcome="WAIT")


def test_unknown_opportunity_raises() -> None:
    with pytest.raises(KeyError):
        OpportunityEngine().reassess("nope", at=T0, outcome="WAIT")


def test_origin_retained() -> None:
    e = _engine()
    assert e.get("o1").origin is OpportunityOrigin.CONVERGENCE  # §40
