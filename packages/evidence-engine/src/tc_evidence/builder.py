"""Assemble an immutable EvidencePack (§43).

The pack captures, as of the decision timestamp: instrument, regime, the convergence
domain evidence (retained, §38), and a structured context dict (§43) holding the
strategy, proposed direction, convergence score/detail and any additional context the
pipeline supplies. Only information available at ``decision_timestamp`` may be included
(§89 no-look-ahead) — the builder does not fetch anything forward; it records what the
caller already holds.

The pack is frozen (Pydantic ``frozen=True`` on EvidencePack) so it is immutable once
built (§90, TC-ADR-018).
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from typing import Any

from tc_domain.enums import RegimeType
from tc_domain.evidence import DomainEvidence, EvidencePack


def pack_id_for(instrument: str, decided_at: datetime, strategy: str) -> str:
    """Stable, unique pack id keyed to instrument + decision instant + strategy.

    Several strategies can produce opportunities on the same bar; including the
    strategy keeps pack ids distinct (append-only stores reject collisions, §90).
    """
    return f"ep:{instrument}:{decided_at.isoformat()}:{strategy}"


def build_evidence_pack(
    *,
    instrument: str,
    decided_at: datetime,
    regime: RegimeType,
    strategy: str,
    direction: str,
    convergence_score: float,
    domain_evidence: Sequence[DomainEvidence] = (),
    convergence_detail: str = "",
    extra_context: dict[str, Any] | None = None,
) -> EvidencePack:
    """Build the immutable Evidence Pack for a decision (§43).

    ``domain_evidence`` is the retained per-domain breakdown from the Convergence
    Engine (§38). ``extra_context`` lets later engines attach macro/news/etc. context
    without changing this signature's core.
    """
    context: dict[str, Any] = {
        "strategy": strategy,
        "direction": direction,
        "convergence_score": convergence_score,
        "convergence_detail": convergence_detail,
    }
    if extra_context:
        # Caller-supplied context is merged but never allowed to overwrite the core
        # decision facts above (they define the pack's identity).
        for k, v in extra_context.items():
            context.setdefault(k, v)

    return EvidencePack(
        pack_id=pack_id_for(instrument, decided_at, strategy),
        instrument=instrument,
        decision_timestamp=decided_at,
        regime=regime,
        domain_evidence=tuple(domain_evidence),
        context=context,
    )
