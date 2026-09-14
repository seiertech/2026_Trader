"""The Experience Store (§48, §88, §90).

From first deployment Trading Command builds its own proprietary experience: what was
observed, what was known at the time, what agents concluded, what was decided, and
what subsequently occurred. Records are append-only and immutable (TC-ADR-018).

This module defines the storage-agnostic protocol plus an in-memory implementation.
The DuckDB implementation lives in ``duckdb_store.py`` and is loaded only when the
optional ``duckdb`` dependency is present, so the domain has no hard DB dependency.
"""

from __future__ import annotations

from datetime import datetime
from typing import Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict
from tc_domain.time import utc_now


class ExperienceRecord(BaseModel):
    """One immutable entry in the experience store (§88)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    record_id: str
    kind: str                     # e.g. "observation", "decision", "outcome"
    at: datetime                  # when the record was written (UTC)
    as_of: datetime               # the decision/observation timestamp (no look-ahead)
    payload: dict[str, object]    # structured content; typed as engines land


@runtime_checkable
class ExperienceStore(Protocol):
    """Append-only store. Implementations MUST NOT expose update/delete."""

    def append(self, record: ExperienceRecord) -> None: ...

    def get(self, record_id: str) -> ExperienceRecord | None: ...

    def all(self) -> tuple[ExperienceRecord, ...]: ...

    def count(self) -> int: ...


class InMemoryExperienceStore:
    """In-memory append-only store for tests and Shadow bring-up."""

    def __init__(self) -> None:
        self._by_id: dict[str, ExperienceRecord] = {}
        self._order: list[str] = []

    def append(self, record: ExperienceRecord) -> None:
        if record.record_id in self._by_id:
            # Append-only + immutable: re-writing an id is a programming error (§90).
            raise ValueError(
                f"experience record '{record.record_id}' already exists; "
                "the store is append-only and immutable (TC-SPEC §90, TC-ADR-018)."
            )
        self._by_id[record.record_id] = record
        self._order.append(record.record_id)

    def get(self, record_id: str) -> ExperienceRecord | None:
        return self._by_id.get(record_id)

    def all(self) -> tuple[ExperienceRecord, ...]:
        return tuple(self._by_id[rid] for rid in self._order)

    def count(self) -> int:
        return len(self._order)


def new_record(kind: str, payload: dict[str, object], as_of: datetime) -> ExperienceRecord:
    """Convenience factory using a time-ordered id and UTC write time."""
    now = utc_now()
    rid = f"{kind}:{now.strftime('%Y%m%dT%H%M%S%f')}"
    return ExperienceRecord(record_id=rid, kind=kind, at=now, as_of=as_of, payload=payload)
