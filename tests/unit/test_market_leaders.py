"""Market leaders (§19, §148): baskets + one-factor collapse + convergence bridge."""

from __future__ import annotations

from tc_convergence import score_convergence
from tc_domain.enums import ConvergenceDomain, ImpactDirection
from tc_leaders import (
    Basket,
    ConstituentMove,
    basket_convergence_input,
    basket_factor,
    load_baskets_from_config,
)

SEMIS = Basket("SEMICONDUCTOR", "Semis", "SEMICONDUCTORS",
               ("NVIDIA", "AMD", "Broadcom", "TSMC", "ASML"))


def _m(pairs: dict[str, float]) -> list[ConstituentMove]:
    return [ConstituentMove(c, v) for c, v in pairs.items()]


def test_config_loads_baskets() -> None:
    baskets = load_baskets_from_config("config/companies.yaml")
    assert "SEMICONDUCTOR" in baskets
    assert "NVIDIA" in baskets["SEMICONDUCTOR"].members
    assert baskets["HEALTHCARE"].sector == "HEALTHCARE"


def test_coherent_down_move_is_bearish_factor() -> None:
    f = basket_factor(SEMIS, _m({"NVIDIA": -3.0, "AMD": -2.5, "Broadcom": -2.8}))
    assert f is not None
    assert f.direction is ImpactDirection.BEARISH
    assert f.coherence == 1.0          # all down
    assert f.strength > 50.0


def test_incoherent_move_downweighted() -> None:
    coherent = basket_factor(SEMIS, _m({"NVIDIA": -3.0, "AMD": -3.0, "Broadcom": -3.0}))
    mixed = basket_factor(SEMIS, _m({"NVIDIA": -3.0, "AMD": 3.0, "Broadcom": -3.0}))
    # Same magnitude, but the mixed (incoherent) move is not one clean factor (§148).
    assert mixed.coherence < coherent.coherence
    assert mixed.strength < coherent.strength


def test_no_relevant_moves_returns_none() -> None:
    assert basket_factor(SEMIS, _m({"SomeBank": -2.0})) is None


def test_basket_is_one_factor_not_n_signals() -> None:
    # THE §148 point: three semis moving down must NOT count as 3 independent domains.
    f = basket_factor(SEMIS, _m({"NVIDIA": -3.0, "AMD": -3.0, "Broadcom": -3.0}))
    di = basket_convergence_input(f)
    assert di.domain is ConvergenceDomain.CORPORATE_SECTOR
    assert di.correlation_group == "basket:SEMICONDUCTOR"

    # Feed the SAME basket factor three times (as if triple-counted) — the convergence
    # engine collapses them via the shared correlation_group (§39), so the score does
    # NOT balloon versus a single contribution.
    one = score_convergence([di])
    tripled = score_convergence([di, di, di])
    assert abs(tripled.score - one.score) < 1e-6
    assert "basket:SEMICONDUCTOR" in tripled.collapsed_groups


def test_flat_move_is_uncertain() -> None:
    f = basket_factor(SEMIS, _m({"NVIDIA": 0.0, "AMD": 0.0}))
    assert f.direction is ImpactDirection.UNCERTAIN
