"""tc_healthcare — Healthcare & Life Sciences intelligence (§139-143, TC-ADR-022).

A first-class intelligence domain. Sub-domains (§139) span pharma, biotech, devices,
insurance, services, diagnostics, vaccines, public health, drug pricing, trials,
approvals, safety/recalls, patents, M&A and outbreaks.

The event taxonomy (§140) is explicit, and each event type has a default issuer-impact
polarity: a DRUG_APPROVAL is good for the issuer and awkward for its competitors; a
TRIAL_HALT is the reverse. Higher-order effects (sector → index) inherit LOWER
confidence (§143) — a single approval rarely moves an index, and the model should say so
rather than pretend.

Authority sources (§141: FDA/EMA/MHRA/CDC/WHO...) carry a higher source-authority weight
than general news, and that weight is retained (§124).
"""

from tc_healthcare.events import (
    AUTHORITY_SOURCES,
    HEALTHCARE_EVENT_TYPES,
    HealthcareEvent,
    healthcare_convergence_input,
    issuer_impact,
)

__all__ = [
    "HEALTHCARE_EVENT_TYPES",
    "AUTHORITY_SOURCES",
    "HealthcareEvent",
    "issuer_impact",
    "healthcare_convergence_input",
]
