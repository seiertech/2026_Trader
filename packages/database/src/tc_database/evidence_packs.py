"""Persist immutable EvidencePacks (§43, §88, §90).

The pack is the record every decision/trade points at via pack_id, and the thing
attribution and post-trade review reconstruct. Stored append-only and immutable like
all experience; a reassessment is a new pack, never an edit (§90, TC-ADR-018).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from tc_domain.time import utc_now

from tc_database.experience import ExperienceRecord, ExperienceStore

if TYPE_CHECKING:
    from tc_domain.evidence import EvidencePack


def _pack_payload(pack: EvidencePack) -> dict[str, Any]:
    return {
        "pack_id": pack.pack_id,
        "instrument": pack.instrument,
        "decision_timestamp": pack.decision_timestamp.isoformat(),
        "regime": pack.regime.value,
        "domain_evidence": [
            {"domain": de.domain.value, "strength": de.strength, "rationale": de.rationale}
            for de in pack.domain_evidence
        ],
        "context": pack.context,
    }


def persist_evidence_pack(store: ExperienceStore, pack: EvidencePack) -> ExperienceRecord:
    """Append an immutable Evidence Pack to the store (§43, §90)."""
    record = ExperienceRecord(
        record_id=pack.pack_id,
        kind="evidence_pack",
        at=utc_now(),
        as_of=pack.decision_timestamp,
        payload=_pack_payload(pack),
    )
    store.append(record)
    return record


def load_evidence_packs(store: ExperienceStore) -> tuple[dict[str, Any], ...]:
    """Return raw evidence-pack payloads from the store."""
    return tuple(r.payload for r in store.all() if r.kind == "evidence_pack")
