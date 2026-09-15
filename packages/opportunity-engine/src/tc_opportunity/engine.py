"""Opportunity lifecycle (§40-42, §70, §90, §151)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta

from tc_domain.enums import OpportunityOrigin
from tc_domain.evidence import Opportunity

# Default life of an opportunity if the caller does not specify (§42 — must expire).
DEFAULT_TTL = timedelta(hours=4)


@dataclass(frozen=True)
class OpportunityRecord:
    """An opportunity plus its immutable assessment history (§90).

    ``assessments`` holds successive (timestamp, outcome, note) entries. A reassessment
    APPENDS; the original opportunity and each prior assessment are never edited.
    """

    opportunity: Opportunity
    origin: OpportunityOrigin
    assessments: tuple[tuple[datetime, str, str], ...] = field(default_factory=tuple)
    resolved: bool = False

    @property
    def id(self) -> str:
        return self.opportunity.id

    @property
    def latest_outcome(self) -> str | None:
        return self.assessments[-1][1] if self.assessments else None


class OpportunityEngine:
    """Tracks live opportunities, their expiry and their reassessment history."""

    def __init__(self) -> None:
        self._records: dict[str, OpportunityRecord] = {}

    # ---- detect (§40) ----

    def detect(
        self,
        *,
        opportunity_id: str,
        instrument: str,
        origin: OpportunityOrigin,
        detected_at: datetime,
        convergence_score: float,
        ttl: timedelta = DEFAULT_TTL,
        evidence_ids: tuple[str, ...] = (),
    ) -> OpportunityRecord:
        """Register a newly detected opportunity. Every one gets an expiry (§42)."""
        opp = Opportunity(
            id=opportunity_id,
            instrument=instrument,
            origin=origin,
            detected_at=detected_at,
            expires_at=detected_at + ttl,
            convergence_score=convergence_score,
            evidence_ids=evidence_ids,
        )
        rec = OpportunityRecord(opportunity=opp, origin=origin)
        self._records[opportunity_id] = rec
        return rec

    # ---- query ----

    def get(self, opportunity_id: str) -> OpportunityRecord | None:
        return self._records.get(opportunity_id)

    def live(self, now: datetime) -> tuple[OpportunityRecord, ...]:
        """Unresolved, unexpired opportunities (§42)."""
        return tuple(
            r for r in self._records.values()
            if not r.resolved and not r.opportunity.is_expired(now)
        )

    def expired(self, now: datetime) -> tuple[OpportunityRecord, ...]:
        return tuple(
            r for r in self._records.values()
            if not r.resolved and r.opportunity.is_expired(now)
        )

    # ---- reassess (§70, §90) ----

    def reassess(
        self, opportunity_id: str, *, at: datetime, outcome: str, note: str = ""
    ) -> OpportunityRecord:
        """Append a new assessment. Stale opportunities are REJECTED, not reassessed (§42).

        ``outcome`` is a DecisionOutcome value (LONG/SHORT/WAIT/REJECT). WAIT keeps the
        opportunity live for a later look (§70); LONG/SHORT/REJECT resolve it.
        """
        rec = self._records.get(opportunity_id)
        if rec is None:
            raise KeyError(f"unknown opportunity '{opportunity_id}'")
        if rec.resolved:
            raise ValueError(f"opportunity '{opportunity_id}' is already resolved")

        if rec.opportunity.is_expired(at):
            outcome, note = "REJECT", note or "expired (stale) — rejected per §42"

        # Append-only history; the original opportunity object is untouched (§90).
        history = (*rec.assessments, (at, outcome, note))
        resolved = outcome in ("LONG", "SHORT", "REJECT")
        updated = OpportunityRecord(
            opportunity=rec.opportunity,
            origin=rec.origin,
            assessments=history,
            resolved=resolved,
        )
        self._records[opportunity_id] = updated
        return updated

    def expire_stale(self, now: datetime) -> tuple[OpportunityRecord, ...]:
        """Reject everything past its expiry (§42). Returns the newly rejected records."""
        out: list[OpportunityRecord] = []
        for rec in list(self._records.values()):
            if not rec.resolved and rec.opportunity.is_expired(now):
                out.append(self.reassess(rec.id, at=now, outcome="REJECT"))
        return tuple(out)
