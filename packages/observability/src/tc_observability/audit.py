"""Append-only audit trail (§105).

Every important action is timestamped (UTC) and recorded. Audit records are immutable:
the log exposes append + read, never update or delete. Removing auditability requires
an ADR (Part XXXI). The Phase 0 implementation is in-memory + an optional JSONL sink;
the DuckDB-backed store is wired in Phase 0.3's database layer.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, ConfigDict
from tc_domain.time import utc_now


class AuditEvent(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    at: datetime
    actor: str          # e.g. "risk-engine", "operator", "decision-engine"
    action: str         # e.g. "MODE_CHANGE", "KILL_SWITCH_ENGAGED", "DECISION"
    subject: str = ""   # optional target id (opportunity id, instrument, ...)
    detail: dict[str, object] = {}


class AuditLog:
    """Append-only audit log. Optionally mirrors to a JSONL file."""

    def __init__(self, sink_path: str | Path | None = None) -> None:
        self._events: list[AuditEvent] = []
        self._sink = Path(sink_path) if sink_path else None
        if self._sink:
            self._sink.parent.mkdir(parents=True, exist_ok=True)

    def record(
        self,
        actor: str,
        action: str,
        subject: str = "",
        **detail: object,
    ) -> AuditEvent:
        event = AuditEvent(
            at=utc_now(), actor=actor, action=action, subject=subject, detail=detail
        )
        self._events.append(event)
        if self._sink:
            with self._sink.open("a", encoding="utf-8") as fh:
                fh.write(event.model_dump_json() + "\n")
        return event

    def events(self) -> tuple[AuditEvent, ...]:
        return tuple(self._events)
