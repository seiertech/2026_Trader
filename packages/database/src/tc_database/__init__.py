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
)

__all__ = [
    "ExperienceRecord",
    "ExperienceStore",
    "InMemoryExperienceStore",
]
