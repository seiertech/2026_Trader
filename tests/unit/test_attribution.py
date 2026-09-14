"""Per-cell attribution (§91) + small-sample honesty (§53)."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from tc_learning.attribution import EvidenceStrength, attribute


@dataclass
class FakeTrade:
    """Minimal trade-like object for attribution (matches the attributes read)."""

    instrument: str
    direction: str
    regime: str
    r_multiple: Decimal
    net_pnl: Decimal


def _t(inst: str, dir_: str, regime: str, r: str, net: str) -> FakeTrade:
    return FakeTrade(inst, dir_, regime, Decimal(r), Decimal(net))


def test_groups_by_dimensions() -> None:
    trades = [
        _t("XAUUSD", "LONG", "STRONG_TREND", "2", "5"),
        _t("XAUUSD", "LONG", "STRONG_TREND", "-1", "-3"),
        _t("GBPUSD", "SHORT", "RANGE", "1", "2"),
    ]
    cells = attribute(trades, ("instrument", "direction"))
    keys = {c.cell for c in cells}
    assert ("XAUUSD", "LONG") in keys
    assert ("GBPUSD", "SHORT") in keys


def test_expectancy_and_win_rate() -> None:
    trades = [
        _t("XAUUSD", "LONG", "T", "2", "10"),
        _t("XAUUSD", "LONG", "T", "-1", "-5"),
    ]
    cells = attribute(trades, ("instrument",))
    c = cells[0]
    assert c.trades == 2
    assert c.wins == 1 and c.losses == 1
    assert c.win_rate == Decimal("0.5000")
    assert c.expectancy_r == Decimal("0.5000")   # (2 + -1)/2
    assert c.profit_factor == Decimal("2.0000")  # 10 / 5


def test_small_sample_flagged_weak() -> None:
    # 3 trades is well below MIN_SAMPLE → WEAK, however good the numbers look (§53).
    trades = [_t("XAUUSD", "LONG", "T", "3", "9") for _ in range(3)]
    cells = attribute(trades, ("instrument",))
    assert cells[0].is_weak
    assert cells[0].strength is EvidenceStrength.WEAK


def test_adequate_sample_is_provisional_not_proven() -> None:
    # >= MIN_SAMPLE clears WEAK but is only PROVISIONAL — never auto-"proven" (§75).
    trades = [_t("XAUUSD", "LONG", "T", "1", "2") for _ in range(40)]
    cells = attribute(trades, ("instrument",), min_sample=30)
    assert not cells[0].is_weak
    assert cells[0].strength is EvidenceStrength.PROVISIONAL


def test_sorted_by_expectancy_desc() -> None:
    trades = [
        _t("A", "LONG", "T", "-1", "-1"),
        _t("B", "LONG", "T", "3", "3"),
    ]
    cells = attribute(trades, ("instrument",))
    assert cells[0].cell == ("B",)  # higher expectancy first


def test_empty_input() -> None:
    assert attribute([], ("instrument",)) == []
