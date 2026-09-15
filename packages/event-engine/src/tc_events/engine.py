"""Event families, status lifecycle and blackout windows (§15-17, §77)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum

from tc_domain.enums import EventStatus


class EventFamily(StrEnum):
    SCHEDULED = "SCHEDULED"
    BREAKING = "BREAKING"
    DEVELOPING = "DEVELOPING"
    UNKNOWN = "UNKNOWN"


# §15 taxonomies, verbatim.
SCHEDULED_TYPES: frozenset[str] = frozenset({
    "CPI", "GDP", "PMI", "EMPLOYMENT", "INTEREST_RATE_DECISION", "BUDGET",
    "CENTRAL_BANK_SPEECH", "EARNINGS", "ELECTION",
})
BREAKING_TYPES: frozenset[str] = frozenset({
    "MILITARY_ESCALATION", "EMERGENCY_RATE_ACTION", "RESIGNATION", "SANCTION",
    "TARIFF", "CYBERATTACK", "ENERGY_DISRUPTION", "CORPORATE_SHOCK",
})
DEVELOPING_TYPES: frozenset[str] = frozenset({
    "WAR", "TRADE_DISPUTE", "POLITICAL_INSTABILITY", "ELECTION_TREND",
    "ENERGY_CRISIS", "SUPPLY_CHAIN_DISRUPTION", "BANKING_STRESS",
})

# High-impact scheduled types that trigger EVENT_BLACKOUT (§77).
HIGH_IMPACT_SCHEDULED: frozenset[str] = frozenset({
    "CPI", "INTEREST_RATE_DECISION", "EMPLOYMENT", "GDP",
})


def classify_event_type(event_type: str) -> EventFamily:
    """Map an event type to its §15 family."""
    t = (event_type or "").upper()
    if t in SCHEDULED_TYPES:
        return EventFamily.SCHEDULED
    if t in BREAKING_TYPES:
        return EventFamily.BREAKING
    if t in DEVELOPING_TYPES:
        return EventFamily.DEVELOPING
    return EventFamily.UNKNOWN


# Status thresholds (research params).
CONFIRM_SOURCES = 3      # distinct sources needed to move to CONFIRMED
STABLE_AFTER = timedelta(hours=6)   # confirmed + quiet this long => STABLE


def next_status(
    *,
    current: EventStatus,
    source_count: int,
    age: timedelta,
    since_last_update: timedelta,
    resolved: bool = False,
) -> EventStatus:
    """Deterministic status transition (§16).

    EMERGING → DEVELOPING once corroborated at all; → CONFIRMED at CONFIRM_SOURCES;
    → STABLE when confirmed and quiet; → RESOLVED only when explicitly resolved.
    Status never regresses except via explicit resolution.
    """
    if resolved:
        return EventStatus.RESOLVED
    if current is EventStatus.RESOLVED:
        return EventStatus.RESOLVED

    if source_count >= CONFIRM_SOURCES:
        # Confirmed, and if nothing new for a while it has settled.
        if since_last_update >= STABLE_AFTER:
            return EventStatus.STABLE
        return EventStatus.CONFIRMED
    if source_count >= 2:
        return EventStatus.DEVELOPING
    # Single source: still emerging, however old.
    return EventStatus.EMERGING if age >= timedelta(0) else current


@dataclass(frozen=True)
class BlackoutWindow:
    """A no-new-entries window around a scheduled release (§77 EVENT_BLACKOUT)."""

    event_type: str
    scheduled_at: datetime
    before: timedelta = timedelta(minutes=30)
    after: timedelta = timedelta(minutes=15)

    def contains(self, when: datetime) -> bool:
        return (self.scheduled_at - self.before) <= when <= (self.scheduled_at + self.after)


def in_blackout(when: datetime, windows: list[BlackoutWindow]) -> bool:
    """True if ``when`` falls inside any blackout window (§77).

    Only HIGH_IMPACT_SCHEDULED types create a blackout; other scheduled events are
    context, not a trading block.
    """
    return any(
        w.contains(when)
        for w in windows
        if w.event_type.upper() in HIGH_IMPACT_SCHEDULED
    )
