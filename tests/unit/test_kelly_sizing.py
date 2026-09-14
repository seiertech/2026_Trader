"""Fractional Kelly sizing (§77a, TC-CR-001, TC-ADR-042). Every rule has a test."""

from __future__ import annotations

from decimal import Decimal

import pytest
from tc_domain.enums import OperatingMode
from tc_risk.kelly import (
    BindingConstraint,
    EdgeStats,
    kelly_fraction,
    size_risk_fraction,
    wilson_lower_bound,
)

FIXED = Decimal("0.01")   # §76 research default
KF = Decimal("0.25")      # quarter-Kelly
CEIL = Decimal("0.01")    # MAX_RISK_PER_TRADE ceiling


def _validated(p: float, b: float, n: int = 500, mode=OperatingMode.SHADOW) -> EdgeStats:
    return EdgeStats(p=p, b=b, sample_size=n, mode=mode, validated=True)


# --- formula -----------------------------------------------------------------------

def test_kelly_formula_known_value() -> None:
    # p=0.6, b=1 → f* = (1*0.6 - 0.4)/1 = 0.2
    assert kelly_fraction(0.6, 1.0) == pytest.approx(0.2)
    # p=0.5, b=1 → 0 (no edge)
    assert kelly_fraction(0.5, 1.0) == pytest.approx(0.0)
    # p=0.4, b=1 → negative
    assert kelly_fraction(0.4, 1.0) < 0


def test_kelly_rejects_bad_inputs() -> None:
    with pytest.raises(ValueError):
        kelly_fraction(0.6, 0.0)  # b must be > 0
    with pytest.raises(ValueError):
        kelly_fraction(1.5, 1.0)  # p out of range


# --- quarter-Kelly + ceiling clamp -------------------------------------------------

def test_quarter_kelly_applied_below_ceiling() -> None:
    # Strong edge but we deliberately raise the ceiling so Kelly binds.
    edge = _validated(p=0.6, b=1.0)  # f* = 0.2
    r = size_risk_fraction(
        edge, max_risk_per_trade=Decimal("0.10"),
        kelly_fraction_setting=KF, fixed_research_risk=FIXED,
        use_conservative_estimate=False,
    )
    # f_applied = 0.25 * 0.2 = 0.05 ; below the 0.10 ceiling → Kelly binds.
    # (p,b are float estimates, so compare with tolerance — not exact rationals.)
    assert r.binding_constraint is BindingConstraint.KELLY
    assert float(r.risk_fraction) == pytest.approx(0.05, abs=1e-9)
    assert float(r.f_star) == pytest.approx(0.2, abs=1e-9)


def test_ceiling_clamps_and_never_raises() -> None:
    edge = _validated(p=0.9, b=3.0)  # very strong → f_applied well above 1% ceiling
    r = size_risk_fraction(
        edge, max_risk_per_trade=CEIL,
        kelly_fraction_setting=KF, fixed_research_risk=FIXED,
        use_conservative_estimate=False,
    )
    assert r.binding_constraint is BindingConstraint.MAX_RISK_PER_TRADE
    assert r.risk_fraction == CEIL  # clamped down to the ceiling, never above
    assert r.f_applied > CEIL       # Kelly wanted more, but was capped


# --- positive-edge gate ------------------------------------------------------------

def test_no_positive_edge_gives_zero() -> None:
    edge = _validated(p=0.4, b=1.0)  # f* < 0
    r = size_risk_fraction(
        edge, max_risk_per_trade=CEIL,
        kelly_fraction_setting=KF, fixed_research_risk=FIXED,
        use_conservative_estimate=False,
    )
    assert r.binding_constraint is BindingConstraint.NO_POSITIVE_EDGE
    assert r.risk_fraction == Decimal(0)  # no trade


def test_zero_edge_boundary_is_no_trade() -> None:
    edge = _validated(p=0.5, b=1.0)  # f* == 0 exactly
    r = size_risk_fraction(
        edge, max_risk_per_trade=CEIL,
        kelly_fraction_setting=KF, fixed_research_risk=FIXED,
        use_conservative_estimate=False,
    )
    assert r.risk_fraction == Decimal(0)
    assert r.binding_constraint is BindingConstraint.NO_POSITIVE_EDGE


# --- unvalidated / missing → fallback ----------------------------------------------

def test_none_edge_falls_back_to_fixed() -> None:
    r = size_risk_fraction(
        None, max_risk_per_trade=CEIL,
        kelly_fraction_setting=KF, fixed_research_risk=FIXED,
    )
    assert r.binding_constraint is BindingConstraint.UNVALIDATED_FALLBACK
    assert r.risk_fraction == FIXED
    assert r.f_star is None


def test_unvalidated_edge_falls_back_even_if_strong() -> None:
    edge = EdgeStats(p=0.9, b=3.0, sample_size=5, mode=OperatingMode.SHADOW, validated=False)
    r = size_risk_fraction(
        edge, max_risk_per_trade=CEIL,
        kelly_fraction_setting=KF, fixed_research_risk=FIXED,
    )
    # Kelly NEVER applied to an unproven estimate, however tempting the numbers.
    assert r.binding_constraint is BindingConstraint.UNVALIDATED_FALLBACK
    assert r.risk_fraction == FIXED


# --- mode independence -------------------------------------------------------------

def test_shadow_stats_do_not_size_live() -> None:
    edge = _validated(p=0.6, b=1.0, mode=OperatingMode.SHADOW)
    r = size_risk_fraction(
        edge, max_risk_per_trade=Decimal("0.10"),
        kelly_fraction_setting=KF, fixed_research_risk=FIXED,
        mode=OperatingMode.LIVE_LIMITED,  # sizing a LIVE trade with SHADOW stats
    )
    assert r.binding_constraint is BindingConstraint.UNVALIDATED_FALLBACK
    assert "mode independence" in r.note


# --- open-risk budget --------------------------------------------------------------

def test_open_risk_budget_reduces_size() -> None:
    edge = _validated(p=0.6, b=1.0)  # f_applied 0.05 with a high ceiling
    r = size_risk_fraction(
        edge, max_risk_per_trade=Decimal("0.10"),
        kelly_fraction_setting=KF, fixed_research_risk=FIXED,
        remaining_open_risk=Decimal("0.02"),  # only 2% budget left
        use_conservative_estimate=False,
    )
    assert r.binding_constraint is BindingConstraint.MAX_OPEN_RISK
    assert float(r.risk_fraction) == pytest.approx(0.02, abs=1e-9)


# --- estimation safety (conservative lower bound) ----------------------------------

def test_conservative_estimate_bets_less() -> None:
    edge = EdgeStats(
        p=0.60, b=1.0, sample_size=200, mode=OperatingMode.SHADOW,
        validated=True, p_lower=0.55,
    )
    point = size_risk_fraction(
        edge, max_risk_per_trade=Decimal("0.10"),
        kelly_fraction_setting=KF, fixed_research_risk=FIXED,
        use_conservative_estimate=False,
    )
    conservative = size_risk_fraction(
        edge, max_risk_per_trade=Decimal("0.10"),
        kelly_fraction_setting=KF, fixed_research_risk=FIXED,
        use_conservative_estimate=True,
    )
    # Lower p → smaller edge → smaller size. Error biases toward under-betting.
    assert conservative.risk_fraction < point.risk_fraction
    assert conservative.p_used == 0.55


def test_wilson_lower_bound_is_below_point_and_bounded() -> None:
    lb = wilson_lower_bound(60, 100)
    assert 0.0 <= lb < 0.60
    assert wilson_lower_bound(0, 0) == 0.0


# --- audit fields ------------------------------------------------------------------

def test_audit_fields_present() -> None:
    edge = _validated(p=0.6, b=1.0)
    r = size_risk_fraction(
        edge, max_risk_per_trade=Decimal("0.10"),
        kelly_fraction_setting=KF, fixed_research_risk=FIXED,
        use_conservative_estimate=False,
    )
    a = r.audit_fields()
    assert set(a) == {
        "p_used", "b_used", "sample_size", "kelly_fraction",
        "f_star", "f_applied", "binding_constraint", "mode",
    }
    assert a["binding_constraint"] == "kelly"
    assert a["mode"] == "SHADOW"
