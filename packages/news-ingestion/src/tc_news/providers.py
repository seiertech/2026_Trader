"""Provider adapter interface (§27) + offline fixture adapter (§24).

    interface IntelligenceProvider { id: string; fetch(since: Date): RawIntelligenceItem[] }

No business logic depends on a specific provider (§27). Every external observation
retains provenance (§124): provider, source, timestamp, ingestedAt, original id.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol, runtime_checkable

from tc_domain.time import utc_now


@dataclass(frozen=True)
class RawIntelligenceItem:
    """A raw item from a provider, before normalisation. Provenance retained (§124)."""

    provider: str          # e.g. "gdelt", "fixture"
    source: str            # e.g. "BBC", "Guardian" — the reporting organisation
    original_id: str       # provider's own id for dedup/idempotency
    title: str
    published_at: datetime  # source timestamp (UTC)
    body: str = ""
    url: str = ""
    ingested_at: datetime = field(default_factory=utc_now)


@runtime_checkable
class IntelligenceProvider(Protocol):
    """A news/intelligence source adapter (§27)."""

    id: str

    def fetch(self, since: datetime) -> Sequence[RawIntelligenceItem]: ...


class FixtureProvider:
    """Offline provider returning a fixed set of items — deterministic, no network.

    Used for tests + demos so the whole pipeline runs with zero external dependency.
    Real RSS/GDELT adapters implement the same protocol.
    """

    def __init__(self, id: str, items: Sequence[RawIntelligenceItem]) -> None:
        self.id = id
        self._items = tuple(items)

    def fetch(self, since: datetime) -> Sequence[RawIntelligenceItem]:
        return tuple(i for i in self._items if i.published_at >= since)
