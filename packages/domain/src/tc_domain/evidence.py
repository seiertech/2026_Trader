"""Opportunity, Evidence Pack, hypotheses and decisions (Parts IX, X, XV; §152).

The Evidence Pack and the trade thesis are IMMUTABLE once created (§43, §90,
TC-ADR-018). We enforce that with frozen Pydantic models: mutation raises. Subsequent
reassessments are *separate* records, never edits.

No-look-ahead (§89, §126) is a construction-time contract: an Evidence Pack carries
its own ``decision_timestamp`` and everything inside it must be as-of that instant.
The domain type records the timestamp; enforcement that no future data leaked in is
the historical-engine's responsibility (Phase 2/8) — the type makes the intent
explicit and auditable.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from tc_domain.enums import (
    ConvergenceDomain,
    CriticVerdict,
    DecisionOutcome,
    ImpactDirection,
    OpportunityOrigin,
    RegimeType,
)


class DomainEvidence(BaseModel):
    """One convergence domain's contribution to an opportunity (§36, §38, §150)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    domain: ConvergenceDomain
    # 0..100 strength for this domain; the raw supporting facts are kept, never
    # discarded — the score never replaces explainability (§38).
    strength: float = Field(..., ge=0.0, le=100.0)
    rationale: str
    observation_ids: tuple[str, ...] = ()


class Opportunity(BaseModel):
    """A candidate situation (§41). Has an expiry; stale ones are rejected (§42)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    instrument: str  # canonical_id
    origin: OpportunityOrigin
    detected_at: datetime
    expires_at: datetime
    convergence_score: float = Field(..., ge=0.0, le=100.0)
    evidence_ids: tuple[str, ...] = ()

    def is_expired(self, now: datetime) -> bool:
        return now >= self.expires_at


class MarketImpactHypothesis(BaseModel):
    """A proposed event→instrument transmission (§152).

    A hypothesis is NEVER permission to trade (§32). It must be confirmed by market
    evidence before it contributes to a decision.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    trigger_event_id: str
    target_instrument_id: str
    expected_direction: ImpactDirection
    horizon: str
    transmission_path: tuple[str, ...]
    confidence: float = Field(..., ge=0.0, le=1.0)
    created_at: datetime
    expires_at: datetime
    confirmation_requirements: tuple[str, ...] = ()
    invalidation_conditions: tuple[str, ...] = ()


class EvidencePack(BaseModel):
    """Immutable snapshot of everything known at decision time (§43, §90).

    Frozen: once built it cannot change. Its ``pack_id`` is referenced by the
    decision, the trade and every performance record so attribution is traceable
    (v1.2 performance-integrity, TC-ADR-038).
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    pack_id: str
    instrument: str
    decision_timestamp: datetime  # the as-of instant; nothing later may be inside
    regime: RegimeType
    domain_evidence: tuple[DomainEvidence, ...]
    # Free-form structured context captured as-of decision_timestamp. Typed sub-models
    # are added as the intelligence engines land (vertical build, §107).
    context: dict[str, object] = Field(default_factory=dict)


class CriticAssessment(BaseModel):
    """Adversarial critic result (§67). VETO carries explicit reason codes."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    verdict: CriticVerdict
    reason_codes: tuple[str, ...] = ()
    notes: str = ""


class Decision(BaseModel):
    """An immutable decision bound to its evidence (§68–§70, §90, TC-ADR-018)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    opportunity_id: str
    evidence_pack_id: str
    outcome: DecisionOutcome
    decided_at: datetime
    # Explainability is mandatory in BOTH registers (§101).
    plain_english: str
    detailed_evidence: str
    critic: CriticAssessment | None = None
