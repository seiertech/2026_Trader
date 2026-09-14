"""Trade persistence: SimulatedTrade -> store -> exact round-trip (§84, §88, §90)."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest
from tc_database import (
    InMemoryExperienceStore,
    load_trades,
    open_duckdb_store,
    persist_trade,
)
from tc_domain.enums import Timeframe
from tc_runtime.golden_path import run_golden_path
from tc_shadow.simulator import SimulatedTrade

SAMPLE = Path(__file__).resolve().parents[2] / "data" / "reference" / "XAUUSD_1m_sample.csv"


def _trade() -> SimulatedTrade:
    t0 = datetime(2026, 1, 5, 1, 0, tzinfo=UTC)
    t1 = datetime(2026, 1, 5, 3, 0, tzinfo=UTC)
    return SimulatedTrade(
        instrument="XAUUSD", direction="LONG",
        entry_time=t0, exit_time=t1,
        entry_price=Decimal("2650.00"), stop_price=Decimal("2645.00"),
        target_price=Decimal("2660.00"), exit_price=Decimal("2660.00"),
        size=Decimal("0.50"),
        gross_pnl=Decimal("5.00"), costs=Decimal("0.43"), net_pnl=Decimal("4.57"),
        r_multiple=Decimal("2"), mfe_r=Decimal("2.1"), mae_r=Decimal("-0.3"),
        exit_reason="TARGET", evidence_pack_id="ep-1",
        sizing_audit={"binding_constraint": "unvalidated_fallback", "mode": "SHADOW"},
    )


def test_roundtrip_is_exact_in_memory() -> None:
    store = InMemoryExperienceStore()
    persist_trade(store, _trade())
    loaded = load_trades(store)
    assert len(loaded) == 1
    back = loaded[0]
    orig = _trade()
    # Decimals and datetimes survive exactly — no float drift.
    assert back.entry_price == orig.entry_price
    assert back.net_pnl == orig.net_pnl
    assert back.r_multiple == orig.r_multiple
    assert back.entry_time == orig.entry_time
    assert back.sizing_audit == orig.sizing_audit


def test_duplicate_persist_rejected() -> None:
    store = InMemoryExperienceStore()
    persist_trade(store, _trade())
    with pytest.raises(ValueError):
        persist_trade(store, _trade())  # same id (instrument+entry) → append-only (§90)


def test_golden_path_persists_to_duckdb(tmp_path) -> None:
    path = tmp_path / "run.duckdb"
    store = open_duckdb_store(str(path))
    result = run_golden_path(SAMPLE, decision_timeframe=Timeframe.H1, store=store)
    # Every simulated trade was persisted (the store also holds opportunity labels,
    # so compare trade records specifically, not the total record count).
    assert len(load_trades(store)) == len(result.trades)
    store.close()

    # Reopen and reconstruct — results survive the run (basis for later learning).
    store2 = open_duckdb_store(str(path))
    loaded = load_trades(store2)
    assert len(loaded) == len(result.trades)
    if loaded:
        assert loaded[0].instrument == "XAUUSD"
    store2.close()



def test_rejected_opportunities_are_labelled_and_persisted(tmp_path) -> None:
    """§50: rejected opportunities must be measured (forward-labelled) and stored.

    At 15m on the sample, every opportunity is rejected by the affordability guard —
    so we get rejected labels and zero trades, but the labels persist regardless.
    """
    from tc_database import load_opportunity_labels, open_duckdb_store

    path = tmp_path / "labels.duckdb"
    store = open_duckdb_store(str(path))
    result = run_golden_path(
        SAMPLE, decision_timeframe=Timeframe.M15, forward_bars=16, store=store
    )
    assert result.opportunities > 0
    assert result.rejected > 0  # the pipeline rejects/waits most 15m setups on £250
    # EVERY opportunity is labelled — traded and rejected alike (§50).
    labels = load_opportunity_labels(store)
    assert len(labels) == result.opportunities
    rej = [x for x in labels if x["outcome"] == "REJECTED"]
    assert len(rej) == result.rejected
    # Each label carries forward directional returns keyed to the §49 horizons.
    assert "5m" in rej[0]["label"]["directional_return"]
    store.close()



def test_evidence_packs_persisted_and_linked(tmp_path) -> None:
    """§43/§90: every opportunity produces an immutable pack; trades/decisions link to it."""
    from tc_database import load_evidence_packs, load_trades, open_duckdb_store

    path = tmp_path / "packs.duckdb"
    store = open_duckdb_store(str(path))
    result = run_golden_path(SAMPLE, decision_timeframe=Timeframe.M15, forward_bars=16, store=store)
    packs = load_evidence_packs(store)
    # One pack per opportunity (§43).
    assert len(packs) == result.opportunities
    # Every persisted trade references a pack that exists in the store.
    pack_ids = {p["pack_id"] for p in packs}
    for t in load_trades(store):
        assert t.evidence_pack_id in pack_ids
    # Packs carry the regime + convergence context.
    assert "regime" in packs[0]
    assert "convergence_score" in packs[0]["context"]
    store.close()
