"""DuckDB-backed append-only Experience Store (§48, §88, §90, TC-ADR-018).

Implements the same :class:`ExperienceStore` protocol as the in-memory store, so
engines are storage-agnostic (separation of concerns; TC-ADR-010). Persists to a
DuckDB file (or in-memory ``:memory:``) so experience survives across runs — the
prerequisite for any later learning/attribution (Phase 11).

Immutability is enforced at this layer, not merely by convention:
  * ``append`` refuses to overwrite an existing ``record_id`` (§90);
  * there is NO update or delete method (removing auditability needs an ADR, Part XXXI).

duckdb is an OPTIONAL dependency (pyproject ``store`` extra). Importing this module
requires it; the protocol + in-memory store in ``experience.py`` do not.

Timestamps are stored as UTC ISO-8601 strings and re-parsed to tz-aware datetimes on
read (§125). Payloads are stored as JSON text.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import duckdb
from tc_domain.time import ensure_utc

from tc_database.experience import ExperienceRecord

_SCHEMA = """
CREATE TABLE IF NOT EXISTS experience (
    record_id  VARCHAR PRIMARY KEY,
    kind       VARCHAR NOT NULL,
    at_utc     VARCHAR NOT NULL,
    as_of_utc  VARCHAR NOT NULL,
    payload    VARCHAR NOT NULL,
    seq        BIGINT  NOT NULL
);
CREATE SEQUENCE IF NOT EXISTS experience_seq START 1;
"""


class DuckDBExperienceStore:
    """Append-only, immutable experience store backed by DuckDB."""

    def __init__(self, path: str | Path = ":memory:") -> None:
        self._path = str(path)
        if self._path != ":memory:":
            Path(self._path).parent.mkdir(parents=True, exist_ok=True)
        self._con = duckdb.connect(self._path)
        # Execute schema statements individually (duckdb executes one at a time).
        for stmt in filter(None, (s.strip() for s in _SCHEMA.split(";"))):
            self._con.execute(stmt)

    # ---- ExperienceStore protocol ----

    def append(self, record: ExperienceRecord) -> None:
        if self.get(record.record_id) is not None:
            # Append-only + immutable: re-writing an id is rejected (§90, TC-ADR-018).
            raise ValueError(
                f"experience record '{record.record_id}' already exists; "
                "the store is append-only and immutable (TC-SPEC §90, TC-ADR-018)."
            )
        self._con.execute(
            "INSERT INTO experience (record_id, kind, at_utc, as_of_utc, payload, seq) "
            "VALUES (?, ?, ?, ?, ?, nextval('experience_seq'))",
            [
                record.record_id,
                record.kind,
                ensure_utc(record.at).isoformat(),
                ensure_utc(record.as_of).isoformat(),
                json.dumps(record.payload, default=str),
            ],
        )

    def get(self, record_id: str) -> ExperienceRecord | None:
        row = self._con.execute(
            "SELECT record_id, kind, at_utc, as_of_utc, payload "
            "FROM experience WHERE record_id = ?",
            [record_id],
        ).fetchone()
        return _row_to_record(row) if row else None

    def all(self) -> tuple[ExperienceRecord, ...]:
        rows = self._con.execute(
            "SELECT record_id, kind, at_utc, as_of_utc, payload "
            "FROM experience ORDER BY seq"
        ).fetchall()
        return tuple(_row_to_record(r) for r in rows)

    def count(self) -> int:
        row = self._con.execute("SELECT COUNT(*) FROM experience").fetchone()
        return int(row[0]) if row else 0

    # ---- lifecycle ----

    def close(self) -> None:
        self._con.close()

    def __enter__(self) -> DuckDBExperienceStore:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()


def _row_to_record(row: tuple) -> ExperienceRecord:
    record_id, kind, at_utc, as_of_utc, payload = row
    return ExperienceRecord(
        record_id=record_id,
        kind=kind,
        at=datetime.fromisoformat(at_utc),
        as_of=datetime.fromisoformat(as_of_utc),
        payload=json.loads(payload),
    )
