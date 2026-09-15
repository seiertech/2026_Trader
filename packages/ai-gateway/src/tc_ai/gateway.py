"""AI provider abstraction, routing (§57) and a deterministic provider (§54-§56).

Routing (§57, TC-ADR-011 — AI is selective, not always on):
    LOW value            -> NONE   (no AI)
    MEDIUM               -> FAST   (cheap/fast model)
    HIGH                 -> STRONG (strong reasoning model)
    HIGH + AMBIGUOUS     -> STRONG_PLUS_CRITIC (strong reasoning + a second critic pass)

An AiAssessment is ADVISORY ONLY (§55, TC-ADR-012): thesis + considerations +
confidence + optional lean, but NO risk fraction, size, or order. The type simply has
no field to override risk — enforcement by construction.

The DeterministicProvider reasons over the SUPPLIED evidence only (§44 — AI reasons
over evidence, never invents missing facts). It produces a structured, reproducible
assessment with no network call, so the pipeline runs fully without any API key.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Protocol, runtime_checkable


class ValueTier(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class AiRoute(StrEnum):
    NONE = "NONE"
    FAST = "FAST"
    STRONG = "STRONG"
    STRONG_PLUS_CRITIC = "STRONG_PLUS_CRITIC"


def route(tier: ValueTier, *, ambiguous: bool = False) -> AiRoute:
    """Select the AI route for an opportunity (§57)."""
    if tier is ValueTier.LOW:
        return AiRoute.NONE
    if tier is ValueTier.MEDIUM:
        return AiRoute.FAST
    # HIGH
    return AiRoute.STRONG_PLUS_CRITIC if ambiguous else AiRoute.STRONG


@dataclass(frozen=True)
class AiRequest:
    """A structured request for AI reasoning over evidence (§44, §54)."""

    instrument: str
    proposed_direction: str            # LONG | SHORT (the thesis to reason about)
    regime: str
    convergence_score: float
    # Structured evidence the AI may reason over — NOT facts to invent beyond (§44).
    evidence: dict[str, object] = field(default_factory=dict)
    route: AiRoute = AiRoute.STRONG


@dataclass(frozen=True)
class AiAssessment:
    """ADVISORY-only AI output (§55, TC-ADR-012). No risk/size/order fields — ever."""

    thesis: str
    considerations: tuple[str, ...]    # points for/against, scenarios
    lean: str                          # SUPPORTS | CHALLENGES | NEUTRAL (advisory)
    confidence: float                  # 0..1, the AI's own confidence
    provider: str
    route: AiRoute

    # Explicit, permanent guarantee: this assessment cannot set risk.
    @property
    def overrides_risk(self) -> bool:
        return False


@runtime_checkable
class AiProvider(Protocol):
    """An AI reasoning provider (§56). Vendor-agnostic."""

    id: str

    def analyse(self, request: AiRequest) -> AiAssessment: ...


class DeterministicProvider:
    """Offline, reproducible provider. Reasons over supplied evidence only (§44).

    Produces a structured assessment whose lean follows the evidence it was given: a
    high convergence score aligned with the proposed direction -> SUPPORTS; low or
    conflicting -> CHALLENGES; middling -> NEUTRAL. No network, no invented facts,
    no risk output. Useful as the default and for tests/Shadow without an API key.
    """

    id = "deterministic"

    def analyse(self, request: AiRequest) -> AiAssessment:
        score = request.convergence_score
        considerations: list[str] = [
            f"regime={request.regime}",
            f"convergence={score:.1f}",
        ]
        # Reflect any evidence keys supplied, without inventing new facts (§44).
        for k, v in request.evidence.items():
            considerations.append(f"{k}={v}")

        if score >= 65.0:
            lean, thesis = "SUPPORTS", (
                f"Evidence broadly supports a {request.proposed_direction} on "
                f"{request.instrument}: convergence {score:.0f} in {request.regime}."
            )
            confidence = min(1.0, score / 100.0)
        elif score <= 35.0:
            lean, thesis = "CHALLENGES", (
                f"Evidence is thin for a {request.proposed_direction} on "
                f"{request.instrument}: convergence only {score:.0f}."
            )
            confidence = min(1.0, (100.0 - score) / 100.0)
        else:
            lean, thesis = "NEUTRAL", (
                f"Mixed evidence for {request.instrument}; convergence {score:.0f} is "
                "inconclusive — prefer to wait for confirmation."
            )
            confidence = 0.5

        return AiAssessment(
            thesis=thesis,
            considerations=tuple(considerations),
            lean=lean,
            confidence=round(confidence, 3),
            provider=self.id,
            route=request.route,
        )
