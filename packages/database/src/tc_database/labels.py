"""Persist forward-outcome labels and rejected opportunities (§49, §50, §88).

§50 is explicit: Trading Command SHALL measure what would have happened to REJECTED
candidates, so it can later ask whether the filters/critic actually improved
expectancy. That means rejected opportunities — with their forward labels — must be
stored too, not just executed trades.

Records are immutable/append-only like everything in the Experience Store (§90).
Decimals stored as strings; datetimes as UTC ISO-8601.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from tc_domain.time import utc_now

from tc_database.experience import ExperienceRecord, ExperienceStore

if TYPE_CHECKING:
    from tc_learning.labelling import ForwardLabel


def _label_payload(label: ForwardLabel) -> dict[str, Any]:
    return {
        "decided_at": label.decided_at.isoformat(),
        "reference_price": str(label.reference_price),
        "bias": label.bias,
        "price_return": {k: (None if v is None else str(v)) for k, v in label.price_return.items()},
        "directional_return": {
            k: (None if v is None else str(v)) for k, v in label.directional_return.items()
        },
    }


def persist_opportunity_label(
    store: ExperienceStore,
    *,
    instrument: str,
    outcome: str,          # "TRADED" | "REJECTED"
    reject_reason: str,     # e.g. "affordability", "no_positive_edge", "" if traded
    label: ForwardLabel,
    cell: dict[str, str] | None = None,  # attribution dims known at decision time
) -> ExperienceRecord:
    """Append a forward-labelled opportunity (traded or rejected) to the store (§50)."""
    rid = f"opp:{instrument}:{label.decided_at.isoformat()}"
    payload: dict[str, Any] = {
        "instrument": instrument,
        "outcome": outcome,
        "reject_reason": reject_reason,
        "cell": cell or {},
        "label": _label_payload(label),
    }
    record = ExperienceRecord(
        record_id=rid,
        kind="opportunity_label",
        at=utc_now(),
        as_of=label.decided_at,  # keyed to the decision instant (no leak-back, §89)
        payload=payload,
    )
    store.append(record)
    return record


def load_opportunity_labels(store: ExperienceStore) -> tuple[dict[str, Any], ...]:
    """Return raw label payloads for every recorded opportunity (traded + rejected)."""
    return tuple(r.payload for r in store.all() if r.kind == "opportunity_label")
