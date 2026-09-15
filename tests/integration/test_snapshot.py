"""Cockpit snapshot (§98-102): the runtime serialises its state for the dashboard."""

from __future__ import annotations

import json
from pathlib import Path

from tc_domain.enums import Timeframe
from tc_runtime.golden_path import run_golden_path
from tc_runtime.snapshot import build_snapshot, write_snapshot

SAMPLE = Path(__file__).resolve().parents[2] / "data" / "reference" / "XAUUSD_1m_sample.csv"


def test_snapshot_has_cockpit_fields() -> None:
    snap = build_snapshot(run_golden_path(SAMPLE, decision_timeframe=Timeframe.H1))
    # §98 main cockpit fields present.
    for key in ("mode", "system_health", "shadow_equity", "realized_pnl",
                "total_return_pct", "max_drawdown", "kill_switch"):
        assert key in snap
    # §0/§75 — no return target, ever.
    assert snap["return_target"] is None
    assert snap["reference_unit_gbp"] == 250.0


def test_snapshot_has_funnel_and_performance() -> None:
    snap = build_snapshot(run_golden_path(SAMPLE, decision_timeframe=Timeframe.M15))
    # §100 funnel + §102 rejection view.
    assert snap["opportunities"] >= 0
    assert set(snap["decisions"]) == {"LONG", "SHORT", "WAIT", "REJECT"}
    assert "rejected" in snap
    # §86 performance block.
    perf = snap["performance"]
    for key in ("trades", "win_rate", "expectancy_r", "expectancy_cash", "total_costs"):
        assert key in perf


def test_snapshot_is_json_serialisable_and_writable(tmp_path) -> None:
    result = run_golden_path(SAMPLE, decision_timeframe=Timeframe.H1)
    out = tmp_path / "snap.json"
    write_snapshot(result, out)
    loaded = json.loads(out.read_text())
    assert loaded["mode"] == "SHADOW"
    assert isinstance(loaded["recent_trades"], list)


def test_recent_trades_capped() -> None:
    snap = build_snapshot(run_golden_path(SAMPLE, decision_timeframe=Timeframe.M15))
    assert len(snap["recent_trades"]) <= 10  # §98 recent — capped
