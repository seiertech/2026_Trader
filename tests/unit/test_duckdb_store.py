"""DuckDB-backed Experience Store: append-only, immutable, persistent (§88, §90)."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from tc_database.duckdb_store import DuckDBExperienceStore
from tc_database.experience import ExperienceRecord, ExperienceStore, new_record


def _rec(rid: str) -> ExperienceRecord:
    now = datetime(2026, 1, 5, 12, 0, tzinfo=UTC)
    return ExperienceRecord(record_id=rid, kind="test", at=now, as_of=now, payload={"k": 1})


def test_implements_protocol() -> None:
    store = DuckDBExperienceStore(":memory:")
    assert isinstance(store, ExperienceStore)  # runtime_checkable protocol


def test_append_get_all_count() -> None:
    store = DuckDBExperienceStore(":memory:")
    assert store.count() == 0
    store.append(_rec("a"))
    store.append(_rec("b"))
    assert store.count() == 2
    got = store.get("a")
    assert got is not None and got.record_id == "a"
    assert [r.record_id for r in store.all()] == ["a", "b"]  # insertion order


def test_rewrite_is_rejected() -> None:
    store = DuckDBExperienceStore(":memory:")
    store.append(_rec("dup"))
    with pytest.raises(ValueError):
        store.append(_rec("dup"))  # append-only + immutable (§90)


def test_no_update_or_delete_method() -> None:
    # Removing auditability requires an ADR (Part XXXI): the store exposes neither.
    store = DuckDBExperienceStore(":memory:")
    assert not hasattr(store, "update")
    assert not hasattr(store, "delete")


def test_timestamps_roundtrip_utc() -> None:
    store = DuckDBExperienceStore(":memory:")
    r = new_record("obs", {"x": "y"}, as_of=datetime(2026, 2, 1, 9, 30, tzinfo=UTC))
    store.append(r)
    back = store.get(r.record_id)
    assert back is not None
    assert back.as_of == datetime(2026, 2, 1, 9, 30, tzinfo=UTC)
    assert back.at.tzinfo is not None  # tz-aware (§125)


def test_persists_across_reopen(tmp_path) -> None:
    path = tmp_path / "exp.duckdb"
    s1 = DuckDBExperienceStore(path)
    s1.append(_rec("persisted"))
    s1.close()
    # Reopen the same file — data survives (the whole point of persistence).
    s2 = DuckDBExperienceStore(path)
    assert s2.count() == 1
    assert s2.get("persisted") is not None
    s2.close()
