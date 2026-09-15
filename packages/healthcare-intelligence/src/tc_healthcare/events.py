"""Healthcare event taxonomy, issuer impact and convergence bridge (§140-143)."""

from __future__ import annotations

from dataclasses import dataclass

from tc_domain.enums import ConvergenceDomain, ImpactDirection

# §140 event taxonomy, verbatim.
HEALTHCARE_EVENT_TYPES: frozenset[str] = frozenset({
    "CLINICAL_TRIAL_RESULT", "TRIAL_HALT", "DRUG_APPROVAL", "DRUG_REJECTION",
    "LABEL_EXPANSION", "SAFETY_WARNING", "PRODUCT_RECALL", "PATENT_DECISION",
    "DRUG_PRICING_CHANGE", "REIMBURSEMENT_CHANGE", "HEALTH_POLICY_CHANGE",
    "M_AND_A", "PIPELINE_UPDATE", "DISEASE_OUTBREAK", "PUBLIC_HEALTH_EMERGENCY",
    "VACCINE_DEVELOPMENT", "SUPPLY_SHORTAGE",
})

# §141 authority sources carry more weight than general coverage; provenance retained.
AUTHORITY_SOURCES: frozenset[str] = frozenset({
    "FDA", "EMA", "MHRA", "NHS", "CDC", "WHO",
})

# Default issuer impact per event type: +1 good for the issuer, -1 bad, 0 ambiguous.
_ISSUER_IMPACT: dict[str, int] = {
    "DRUG_APPROVAL": +1,
    "LABEL_EXPANSION": +1,
    "VACCINE_DEVELOPMENT": +1,
    "PIPELINE_UPDATE": 0,
    "CLINICAL_TRIAL_RESULT": 0,      # depends on the result; caller may override
    "M_AND_A": 0,
    "PATENT_DECISION": 0,
    "TRIAL_HALT": -1,
    "DRUG_REJECTION": -1,
    "SAFETY_WARNING": -1,
    "PRODUCT_RECALL": -1,
    "SUPPLY_SHORTAGE": -1,
    "DRUG_PRICING_CHANGE": -1,       # pricing pressure squeezes margins
    "REIMBURSEMENT_CHANGE": -1,
    "HEALTH_POLICY_CHANGE": 0,
    "DISEASE_OUTBREAK": 0,           # bad for consumer/travel, good for diagnostics
    "PUBLIC_HEALTH_EMERGENCY": 0,
}


def issuer_impact(event_type: str) -> int:
    """Default impact on the ISSUING company (+1/-1/0). 0 means it depends (§143)."""
    return _ISSUER_IMPACT.get(event_type.upper(), 0)


@dataclass(frozen=True)
class HealthcareEvent:
    """A healthcare event (§140) with its provenance and order of effect (§143)."""

    event_type: str
    company: str = ""
    therapeutic_area: str = ""
    sources: tuple[str, ...] = ()
    severity: float = 0.5            # 0..1
    # 1 = direct issuer effect, 2 = sector, 3 = index. Higher order => lower confidence.
    order: int = 1
    # Optional explicit override when the type alone is ambiguous (e.g. trial result).
    impact_override: int | None = None

    @property
    def authority_weight(self) -> float:
        """0..1 — regulator/agency sources outrank general news (§141)."""
        if not self.sources:
            return 0.3
        authoritative = sum(1 for s in self.sources if s.upper() in AUTHORITY_SOURCES)
        base = 0.5 + 0.5 * (authoritative / len(self.sources))
        return round(min(1.0, base), 3)

    @property
    def impact(self) -> int:
        return (
            self.impact_override
            if self.impact_override is not None
            else issuer_impact(self.event_type)
        )


# Confidence decay by order of effect (§143): 1st order trusted, 3rd order speculative.
_ORDER_DECAY: dict[int, float] = {1: 1.0, 2: 0.6, 3: 0.35}


def healthcare_convergence_input(event: HealthcareEvent, *, freshness: float = 1.0):
    """Adapt a healthcare event to a HEALTHCARE_LIFE_SCIENCES convergence input (§150).

    Strength = severity × authority weight × order decay. An ambiguous event type with
    no override yields UNCERTAIN — the model declines to pick a side rather than guess.
    """
    from tc_convergence import DomainInput

    impact = event.impact
    if impact > 0:
        direction = ImpactDirection.BULLISH
    elif impact < 0:
        direction = ImpactDirection.BEARISH
    else:
        direction = ImpactDirection.UNCERTAIN

    decay = _ORDER_DECAY.get(event.order, 0.2)
    strength = round(
        min(100.0, event.severity * 100.0 * event.authority_weight * decay), 2
    )
    who = event.company or event.therapeutic_area or "sector"
    return DomainInput(
        domain=ConvergenceDomain.HEALTHCARE_LIFE_SCIENCES,
        strength=strength,
        direction=direction,
        rationale=(
            f"{event.event_type} ({who}), order-{event.order}, "
            f"authority {event.authority_weight:.2f}"
        ),
        freshness=freshness,
        # One event is one factor across all its downstream expressions (§39).
        correlation_group=f"health:{event.event_type}:{who}",
    )
