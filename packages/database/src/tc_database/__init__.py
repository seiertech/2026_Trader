"""tc_database — storage abstraction for Trading Command.

Storage is behind a repository interface so no engine depends on a concrete database
(separation of concerns, Part XXXI §1; adapters, TC-ADR-010). Phase 0 provides:

  * :class:`ExperienceStore` protocol — the append-only proprietary experience the
    system accumulates from first deployment (§48, §88);
  * an in-memory implementation for tests and Shadow bring-up;
  * a DuckDB-backed implementation (optional dep) selected via config.

Immutability (§90, TC-ADR-018) is honoured: stored evidence packs / decisions are
written once and read back, never updated.
"""

from tc_database.experience import (
    ExperienceRecord,
    ExperienceStore,
    InMemoryExperienceStore,
    new_record,
)
from tc_database.labels import (
    load_opportunity_labels,
    persist_opportunity_label,
)
from tc_database.trades import (
    load_trades,
    payload_to_trade,
    persist_trade,
    trade_to_payload,
)

__all__ = [
    "ExperienceRecord",
    "ExperienceStore",
    "InMemoryExperienceStore",
    "new_record",
    "load_trades",
    "persist_trade",
    "payload_to_trade",
    "trade_to_payload",
    "load_opportunity_labels",
    "persist_opportunity_label",
]


def open_duckdb_store(path: str = ":memory:"):
    """Lazily construct a DuckDBExperienceStore (requires the optional ``duckdb`` dep).

    Kept as a function so importing this package never hard-requires duckdb.
    """
    from tc_database.duckdb_store import DuckDBExperienceStore

    return DuckDBExperienceStore(path)
