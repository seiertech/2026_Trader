"""Portfolio & exposure (§66, §77): aggregation, correlated clusters, portfolio fit."""

from __future__ import annotations

from decimal import Decimal

import pytest
from tc_portfolio import OpenPosition, Portfolio, cluster_of


def _pos(inst: str, direction: str = "LONG", risk: str = "0.01") -> OpenPosition:
    return OpenPosition(
        instrument=inst, direction=direction, size=Decimal("0.1"),
        entry_price=Decimal("2650"), stop_price=Decimal("2645"),
        risk_fraction=Decimal(risk),
    )


def test_clusters_group_correlated_instruments() -> None:
    assert cluster_of("EURUSD") == cluster_of("GBPUSD") == "USD_MAJORS"
    assert cluster_of("NAS100") == cluster_of("US500") == "EQUITY_INDICES"
    assert cluster_of("UNKNOWN_THING") == "UNKNOWN_THING"


def test_exposure_aggregates() -> None:
    p = Portfolio()
    p.open("1", _pos("EURUSD", risk="0.01"))
    p.open("2", _pos("GBPUSD", risk="0.01"))
    p.open("3", _pos("XAUUSD", risk="0.02"))
    e = p.exposure()
    assert e.open_positions == 3
    assert e.total_risk_fraction == Decimal("0.04")
    # Correlated USD majors add into ONE cluster (§77).
    assert e.by_cluster["USD_MAJORS"] == Decimal("0.02")
    assert e.by_cluster["METALS"] == Decimal("0.02")
    assert e.by_direction["LONG"] == 3


def test_nominal_distinct_from_risk() -> None:
    p = Portfolio()
    p.open("1", _pos("XAUUSD", risk="0.01"))
    e = p.exposure()
    # v1.2: nominal exposure and risk-at-stop are different quantities.
    assert e.nominal_exposure == Decimal("265.0")
    assert e.total_risk_fraction == Decimal("0.01")


def test_cluster_limit_breach_detected() -> None:
    p = Portfolio()
    p.open("1", _pos("EURUSD", risk="0.03"))
    # Adding GBPUSD risk lands in the same cluster → would breach a 0.05 cap.
    assert p.would_breach_cluster_limit("GBPUSD", Decimal("0.03"), Decimal("0.05"))
    assert not p.would_breach_cluster_limit("GBPUSD", Decimal("0.01"), Decimal("0.05"))


def test_uncorrelated_instrument_has_own_headroom() -> None:
    p = Portfolio()
    p.open("1", _pos("EURUSD", risk="0.04"))
    # Gold is a different cluster, so USD-major exposure does not constrain it.
    assert not p.would_breach_cluster_limit("XAUUSD", Decimal("0.02"), Decimal("0.05"))


def test_opposing_position_detected() -> None:
    p = Portfolio()
    p.open("1", _pos("XAUUSD", direction="LONG"))
    assert p.has_opposing_position("XAUUSD", "SHORT")
    assert not p.has_opposing_position("XAUUSD", "LONG")


def test_close_removes_exposure() -> None:
    p = Portfolio()
    p.open("1", _pos("XAUUSD", risk="0.02"))
    p.close("1")
    assert p.exposure().open_positions == 0
    assert p.exposure().total_risk_fraction == Decimal(0)


def test_duplicate_position_id_refused() -> None:
    p = Portfolio()
    p.open("1", _pos("XAUUSD"))
    with pytest.raises(ValueError):
        p.open("1", _pos("EURUSD"))


def test_instrument_and_cluster_risk_helpers() -> None:
    p = Portfolio()
    p.open("1", _pos("US500", risk="0.01"))
    p.open("2", _pos("NAS100", risk="0.015"))
    assert p.instrument_risk("US500") == Decimal("0.01")
    assert p.cluster_risk("US500") == Decimal("0.025")  # both indices, one cluster
