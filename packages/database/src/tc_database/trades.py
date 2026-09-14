"""Persist SimulatedTrades into the Experience Store (§84, §88).

A closed trade is exactly the kind of proprietary experience §88 wants recorded:
what was decided and what subsequently occurred. This module serialises a
``SimulatedTrade`` into an immutable :class:`ExperienceRecord` (kind="trade") and
reconstructs it on read, so downstream learning/attribution (Phase 11) can query it.

Decimals are stored as strings (exact, no float drift); datetimes as UTC ISO-8601.
The §77a sizing audit travels with the record so we can later check whether the edge
estimate used for sizing was borne out.

Kept in the database package (not the shadow engine) so the simulator stays
storage-agnostic — it produces trades; persistence is a separate concern.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from tc_domain.time import utc_now

from tc_database.experience import ExperienceRecord, ExperienceStore

if TYPE_CHECKING:
    from tc_shadow.simulator import SimulatedTrade

_DECIMAL_FIELDS = (
    "entry_price", "stop_price", "target_price", "exit_price", "size",
    "gross_pnl", "costs", "net_pnl", "r_multiple", "mfe_r", "mae_r",
)
_DATETIME_FIELDS = ("entry_time", "exit_time")


def trade_to_payload(trade: SimulatedTrade) -> dict[str, Any]:
    """Serialise a SimulatedTrade to a JSON-safe payload dict."""
    payload: dict[str, Any] = {
        "instrument": trade.instrument,
        "direction": trade.direction,
        "exit_reason": trade.exit_reason,
        "evidence_pack_id": trade.evidence_pack_id,
        "sizing_audit": trade.sizing_audit,
        "strategy": trade.strategy,
        "regime": trade.regime,
    }
    for f in _DECIMAL_FIELDS:
        payload[f] = str(getattr(trade, f))
    for f in _DATETIME_FIELDS:
        payload[f] = getattr(trade, f).isoformat()
    return payload


def payload_to_trade(payload: dict[str, Any]) -> SimulatedTrade:
    """Reconstruct a SimulatedTrade from a stored payload (round-trip exact)."""
    from tc_shadow.simulator import SimulatedTrade  # local import: no hard dep

    kwargs: dict[str, Any] = {
        "instrument": payload["instrument"],
        "direction": payload["direction"],
        "exit_reason": payload["exit_reason"],
        "evidence_pack_id": payload.get("evidence_pack_id", ""),
        "sizing_audit": payload.get("sizing_audit"),
        "strategy": payload.get("strategy", ""),
        "regime": payload.get("regime", ""),
    }
    for f in _DECIMAL_FIELDS:
        kwargs[f] = Decimal(payload[f])
    for f in _DATETIME_FIELDS:
        kwargs[f] = datetime.fromisoformat(payload[f])
    return SimulatedTrade(**kwargs)


def persist_trade(store: ExperienceStore, trade: SimulatedTrade) -> ExperienceRecord:
    """Append ``trade`` to ``store`` as an immutable experience record.

    The record id is derived from instrument + entry time so it is stable and a
    duplicate persist is rejected by the append-only store (§90).
    """
    rid = f"trade:{trade.instrument}:{trade.entry_time.isoformat()}"
    record = ExperienceRecord(
        record_id=rid,
        kind="trade",
        at=utc_now(),
        as_of=trade.exit_time,  # a closed trade is known as of its exit
        payload=trade_to_payload(trade),
    )
    store.append(record)
    return record


def load_trades(store: ExperienceStore) -> tuple[SimulatedTrade, ...]:
    """Reconstruct all persisted trades from ``store`` (in insertion order)."""
    return tuple(
        payload_to_trade(r.payload) for r in store.all() if r.kind == "trade"
    )
