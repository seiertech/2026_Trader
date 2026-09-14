"""UTC time helpers.

TC-SPEC-001 §125: all internal timestamps SHALL use UTC. Display MAY convert to local
time — but that is a UI concern, never a domain concern. Every timestamp created in
the domain flows through here so the rule is enforced in one place.
"""

from __future__ import annotations

from datetime import UTC, datetime


def utc_now() -> datetime:
    """Return the current time as a timezone-aware UTC datetime."""
    return datetime.now(UTC)


def ensure_utc(dt: datetime) -> datetime:
    """Return ``dt`` as UTC, rejecting naive datetimes.

    A naive datetime has ambiguous meaning and would silently violate §125, so we
    fail loudly rather than guess a timezone.
    """
    if dt.tzinfo is None:
        raise ValueError(
            "naive datetime is not permitted in the domain (TC-SPEC-001 §125: "
            "all internal timestamps SHALL be UTC-aware)"
        )
    return dt.astimezone(UTC)
