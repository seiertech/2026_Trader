"""End-to-end golden path (§123): replay -> quant/regime -> strategy -> shadow -> metrics.

This is the integration proof that the whole XAUUSD Shadow pipeline is wired correctly.
It does NOT assert profitability — no strategy is presumed to have edge (TC-ADR-020),
and a non-positive expectancy is a valid, honest outcome (§0, §130).
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from tc_domain.enums import OperatingMode, Timeframe
from tc_runtime.golden_path import format_report, run_golden_path

SAMPLE = Path(__file__).resolve().parents[2] / "data" / "reference" / "XAUUSD_1m_sample.csv"


def test_golden_path_runs_in_shadow_and_produces_metrics() -> None:
    r = run_golden_path(SAMPLE, decision_timeframe=Timeframe.H1)
    # Mode is asserted SHADOW — no broker orders (§79).
    assert r.mode is OperatingMode.SHADOW
    # It processed the aggregated decision bars and looked for opportunities.
    assert r.bars_processed > 0
    assert r.opportunities >= 0
    # Every trade is a well-formed immutable record.
    for t in r.trades:
        assert t.instrument == "XAUUSD"
        assert t.direction in ("LONG", "SHORT")
        assert t.exit_reason in ("STOP", "TARGET", "TIME")
        assert t.size > 0
    # Metrics object is always produced, even with few/no trades.
    assert r.metrics.trades == len(r.trades)


def test_reference_unit_is_not_a_target() -> None:
    r = run_golden_path(SAMPLE, decision_timeframe=Timeframe.H1)
    # £250 is the starting reference unit; the ledger moves but there is no target and
    # no compounding mandate (§74, §0, TC-ADR-016/017).
    assert r.starting_balance == Decimal("250")
    # Ending balance = start + sum(net_pnl); consistency check.
    total_net = sum((t.net_pnl for t in r.trades), Decimal(0))
    assert r.ending_balance == Decimal("250") + total_net


def test_most_intraday_opportunities_are_rejected_or_waited() -> None:
    # On £250, tight 15m stops mean most setups are unaffordable (§85) or sent to WAIT
    # by the pipeline — far more opportunities than executed trades. We assert the
    # SELECTIVITY (§3), not a brittle exact count: the middle of the pipeline filters
    # heavily and every opportunity is still accounted for (§50).
    r = run_golden_path(SAMPLE, decision_timeframe=Timeframe.M15)
    assert r.opportunities > 0
    assert r.metrics.trades < r.opportunities          # heavy filtering, not free trading
    assert r.rejected + r.metrics.trades == r.opportunities  # every opp accounted for
    # WAIT/REJECT dominate — the system is selective, not active (§3).
    assert r.decisions["WAIT"] + r.decisions["REJECT"] >= r.decisions["LONG"] + r.decisions["SHORT"]


def test_report_is_renderable() -> None:
    r = run_golden_path(SAMPLE, decision_timeframe=Timeframe.H1)
    report = format_report(r)
    assert "XAUUSD GOLDEN PATH (SHADOW)" in report
    assert "expectancy (R)" in report
