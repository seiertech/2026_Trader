"""Evidence Pack builder (§43, §89, §90): immutable snapshot at decision time."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError
from tc_convergence import DomainInput, score_convergence
from tc_domain.enums import ConvergenceDomain as CD
from tc_domain.enums import ImpactDirection as D
from tc_domain.enums import RegimeType
from tc_evidence import build_evidence_pack, pack_id_for

T = datetime(2026, 1, 5, 12, 0, tzinfo=UTC)


def test_pack_id_stable_and_strategy_scoped() -> None:
    a = pack_id_for("XAUUSD", T, "trend_following")
    b = pack_id_for("XAUUSD", T, "mean_reversion")
    assert a != b  # same bar, different strategy → distinct ids (§90 no collision)
    assert pack_id_for("XAUUSD", T, "trend_following") == a  # deterministic


def test_build_pack_carries_regime_and_convergence() -> None:
    conv = score_convergence([DomainInput(CD.MARKET_STRUCTURE, 80, D.BULLISH)])
    pack = build_evidence_pack(
        instrument="XAUUSD", decided_at=T, regime=RegimeType.STRONG_TREND,
        strategy="trend_following", direction="LONG",
        convergence_score=conv.score, domain_evidence=conv.contributing,
        convergence_detail=conv.detail,
    )
    assert pack.instrument == "XAUUSD"
    assert pack.regime is RegimeType.STRONG_TREND
    assert pack.decision_timestamp == T
    assert pack.context["strategy"] == "trend_following"
    assert pack.context["convergence_score"] == conv.score
    assert len(pack.domain_evidence) == len(conv.contributing)


def test_pack_is_immutable() -> None:
    pack = build_evidence_pack(
        instrument="XAUUSD", decided_at=T, regime=RegimeType.RANGE,
        strategy="s", direction="LONG", convergence_score=50.0,
    )
    with pytest.raises(ValidationError):
        pack.instrument = "EURUSD"  # type: ignore[misc]


def test_extra_context_cannot_overwrite_core_facts() -> None:
    pack = build_evidence_pack(
        instrument="XAUUSD", decided_at=T, regime=RegimeType.RANGE,
        strategy="real_strategy", direction="LONG", convergence_score=50.0,
        extra_context={"strategy": "SPOOF", "note": "hi"},
    )
    # Core identity fact wins; extra context only adds.
    assert pack.context["strategy"] == "real_strategy"
    assert pack.context["note"] == "hi"
