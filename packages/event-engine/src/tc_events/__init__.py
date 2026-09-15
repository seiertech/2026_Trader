"""tc_events — Event classification & lifecycle (§15-17).

Classifies events into the spec's three families and manages status transitions:

  SCHEDULED  — CPI, GDP, PMI, employment, rate decisions, budgets, speeches, earnings,
               elections (known in advance → blackout windows are computable)
  BREAKING   — military escalation, emergency rate action, resignation, sanction,
               tariff, cyberattack, energy disruption, corporate shock
  DEVELOPING — war, trade dispute, political instability, election trend, energy crisis,
               supply-chain disruption, banking stress

Status lifecycle (§16): EMERGING → DEVELOPING → CONFIRMED → STABLE → RESOLVED, driven
by corroboration (source count) and age — deterministic, not opinion.

Scheduled events also drive EVENT_BLACKOUT (§77): no new entries inside the window
around a high-impact release.
"""

from tc_events.engine import (
    BREAKING_TYPES,
    DEVELOPING_TYPES,
    HIGH_IMPACT_SCHEDULED,
    SCHEDULED_TYPES,
    BlackoutWindow,
    EventFamily,
    classify_event_type,
    in_blackout,
    next_status,
)

__all__ = [
    "EventFamily",
    "classify_event_type",
    "next_status",
    "in_blackout",
    "BlackoutWindow",
    "SCHEDULED_TYPES",
    "BREAKING_TYPES",
    "DEVELOPING_TYPES",
    "HIGH_IMPACT_SCHEDULED",
]
