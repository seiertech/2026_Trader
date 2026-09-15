"""AI gateway (§54-§57): routing, advisory-only output, never overrides risk."""

from __future__ import annotations

from tc_ai import (
    AiAssessment,
    AiProvider,
    AiRequest,
    AiRoute,
    DeterministicProvider,
    ValueTier,
    route,
)


def _req(score: float, direction: str = "LONG", ambiguous: bool = False) -> AiRequest:
    return AiRequest(
        instrument="XAUUSD", proposed_direction=direction, regime="STRONG_TREND",
        convergence_score=score,
        route=route(ValueTier.HIGH, ambiguous=ambiguous),
    )


# --- routing (§57) ---

def test_routing_tiers() -> None:
    assert route(ValueTier.LOW) is AiRoute.NONE            # LOW -> no AI
    assert route(ValueTier.MEDIUM) is AiRoute.FAST         # MEDIUM -> cheap/fast
    assert route(ValueTier.HIGH) is AiRoute.STRONG         # HIGH -> strong
    assert route(ValueTier.HIGH, ambiguous=True) is AiRoute.STRONG_PLUS_CRITIC


# --- deterministic provider (§44, §54, §56) ---

def test_provider_is_a_provider() -> None:
    assert isinstance(DeterministicProvider(), AiProvider)


def test_supports_on_strong_convergence() -> None:
    a = DeterministicProvider().analyse(_req(85.0))
    assert a.lean == "SUPPORTS"
    assert a.confidence > 0.5
    assert "XAUUSD" in a.thesis


def test_challenges_on_thin_convergence() -> None:
    a = DeterministicProvider().analyse(_req(20.0))
    assert a.lean == "CHALLENGES"


def test_neutral_on_middling() -> None:
    a = DeterministicProvider().analyse(_req(50.0))
    assert a.lean == "NEUTRAL"


def test_reasons_over_supplied_evidence_only() -> None:
    req = AiRequest(
        instrument="XAUUSD", proposed_direction="LONG", regime="RANGE",
        convergence_score=80.0, evidence={"macro": "hawkish", "news": "escalation"},
    )
    a = DeterministicProvider().analyse(req)
    # The supplied evidence keys appear in considerations; nothing invented beyond them.
    joined = " ".join(a.considerations)
    assert "macro=hawkish" in joined
    assert "news=escalation" in joined


# --- the hard rule: advisory only, never overrides risk (§55, TC-ADR-012) ---

def test_assessment_has_no_risk_or_size_fields() -> None:
    a = DeterministicProvider().analyse(_req(90.0))
    fields = set(vars(a))
    for forbidden in ("risk", "risk_fraction", "size", "position_size", "order", "leverage"):
        assert forbidden not in fields
    assert a.overrides_risk is False


def test_assessment_confidence_bounded() -> None:
    for score in (0.0, 20.0, 50.0, 80.0, 100.0):
        a = DeterministicProvider().analyse(_req(score))
        assert 0.0 <= a.confidence <= 1.0


def test_assessment_carries_provider_and_route() -> None:
    a = DeterministicProvider().analyse(_req(85.0, ambiguous=True))
    assert a.provider == "deterministic"
    assert a.route is AiRoute.STRONG_PLUS_CRITIC
    assert isinstance(a, AiAssessment)
