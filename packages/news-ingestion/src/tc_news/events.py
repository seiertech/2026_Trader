"""The Event model (§16) and its intelligence dimensions (§17).

An Event is the deduplicated, clustered representation of what multiple sources are
reporting (§29). It carries the §16 attributes plus the §17 dimensions (relevance,
severity, novelty, velocity, confidence), which are distinct measurements.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from tc_domain.enums import EventStatus


class Novelty:
    """Novelty classes (§31). A repeated headline must not re-trigger analysis."""

    NEW = "NEW"
    REPEATED = "REPEATED"
    UPDATE = "UPDATE"
    MATERIAL_UPDATE = "MATERIAL_UPDATE"


# News taxonomy categories (§14). Kept as a tuple for config-free classification.
NEWS_CATEGORIES: tuple[str, ...] = (
    "Economy", "Politics", "Geopolitics", "Conflict", "Trade", "Tariffs", "Sanctions",
    "Energy", "Technology", "AI", "Semiconductors", "Banking", "Regulation",
    "Corporate", "Supply Chain", "Cybersecurity", "Natural Disaster", "Labour", "Other",
)


@dataclass
class Event:
    """A clustered market/world event (§16, §17)."""

    event_id: str
    title: str
    first_seen: datetime
    last_updated: datetime
    category: str = "Other"
    countries: tuple[str, ...] = ()
    entities: tuple[str, ...] = ()
    themes: tuple[str, ...] = ()
    source_count: int = 1               # distinct reporting orgs (§29)
    sources: tuple[str, ...] = ()
    status: EventStatus = EventStatus.EMERGING
    # §17 dimensions — distinct measurements.
    relevance: float = 0.0              # 0..1
    severity: float = 0.0               # 0..1
    novelty: str = Novelty.NEW
    velocity: float = 0.0               # sources per hour (§30)
    confidence: float = 0.0             # 0..1 confidence the event EXISTS (§29)
    item_ids: tuple[str, ...] = field(default_factory=tuple)
