"""tc_ai — the AI gateway (Part XIII, §54-§57).

AI performs interpretation, contextual reasoning, scenario analysis, thesis
construction and adversarial criticism (§54). It SHALL NOT perform price/indicator/
sizing/risk/statistics calculations (§55) and it CANNOT override deterministic risk
(TC-ADR-012). The gateway enforces this structurally: an :class:`AiAssessment` is
ADVISORY ONLY — it carries a thesis, considerations and a confidence, but no risk
fraction, no position size, no order. Nothing downstream can turn it into a risk
override.

Provider-abstracted (§56): engines depend on the :class:`AiProvider` protocol, never a
vendor. A deterministic, offline provider ships for tests/Shadow-without-keys; OpenAI/
Anthropic adapters (BYOK) implement the same protocol. AI is invoked SELECTIVELY per
the routing tiers (§57, TC-ADR-011), not on every opportunity.
"""

from tc_ai.gateway import (
    AiAssessment,
    AiProvider,
    AiRequest,
    AiRoute,
    DeterministicProvider,
    ValueTier,
    route,
)

__all__ = [
    "AiProvider",
    "AiRequest",
    "AiAssessment",
    "AiRoute",
    "ValueTier",
    "DeterministicProvider",
    "route",
]
