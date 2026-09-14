"""Fractional Kelly position sizing (§77a, TC-CR-001, TC-ADR-042).

Deterministic policy code. Given a *validated* edge estimate (p, b, sample size) it
computes the risk fraction, then clamps it under the §77 ceilings. Given an unproven
or non-positive edge it returns the fixed §76 research risk or zero. It NEVER raises
risk above a ceiling, and AI cannot override any of it.

Kelly runs AFTER the Decision Engine has proposed a direction and BEFORE order
construction — it sets *size*, not direction.

Money math elsewhere is Decimal; the Kelly fractions here are Decimal too so the
audit record is exact.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum

from tc_domain.enums import OperatingMode


class BindingConstraint(StrEnum):
    """Which rule actually set (or zeroed) the risk fraction — for the audit record."""

    KELLY = "kelly"
    MAX_RISK_PER_TRADE = "MAX_RISK_PER_TRADE"
    MAX_OPEN_RISK = "MAX_OPEN_RISK"
    CORRELATED = "correlated"
    NO_POSITIVE_EDGE = "NO_POSITIVE_EDGE"
    UNVALIDATED_FALLBACK = "unvalidated_fallback"
    OTHER = "other"


@dataclass(frozen=True)
class EdgeStats:
    """A strategy/cell's edge estimate, per mode.

    ``validated`` means the stats satisfy §75 promotion gates + §87 Shadow validation
    (incl. minimum sample size). Kelly is applied ONLY when validated is True. ``mode``
    ties the stats to the mode they were measured in (mode independence, §77a).
    """

    p: float                 # probability of a win (point estimate)
    b: float                 # payoff ratio = avg win / avg loss, in R
    sample_size: int
    mode: OperatingMode
    validated: bool = False
    # Optional lower-confidence-bound on p for conservative sizing (estimation safety).
    p_lower: float | None = None


@dataclass(frozen=True)
class SizingResult:
    """Result of a sizing decision, with the full audit record (§77a auditability)."""

    risk_fraction: Decimal          # final risk-per-trade fraction actually used
    f_star: Decimal | None          # raw Kelly fraction (None if not computed)
    f_applied: Decimal | None       # KELLY_FRACTION × f_star (None if not computed)
    kelly_fraction: Decimal
    p_used: float | None
    b_used: float | None
    sample_size: int | None
    binding_constraint: BindingConstraint
    mode: OperatingMode
    note: str = ""

    def audit_fields(self) -> dict[str, object]:
        """Exactly the fields §77a requires recording in the Evidence Pack."""
        return {
            "p_used": self.p_used,
            "b_used": self.b_used,
            "sample_size": self.sample_size,
            "kelly_fraction": str(self.kelly_fraction),
            "f_star": None if self.f_star is None else str(self.f_star),
            "f_applied": None if self.f_applied is None else str(self.f_applied),
            "binding_constraint": self.binding_constraint.value,
            "mode": self.mode.value,
        }


def kelly_fraction(p: float, b: float) -> float:
    """Raw Kelly fraction f* = (b·p − q) / b, with q = 1 − p.

    Returns f* which may be <= 0 (meaning no positive edge). Raises on b <= 0, which is
    a degenerate/invalid payoff ratio (fail closed rather than divide nonsensically).
    """
    if b <= 0:
        raise ValueError("payoff ratio b must be > 0")
    if not (0.0 <= p <= 1.0):
        raise ValueError("win probability p must be in [0, 1]")
    q = 1.0 - p
    return (b * p - q) / b


def size_risk_fraction(
    edge: EdgeStats | None,
    *,
    max_risk_per_trade: Decimal,
    kelly_fraction_setting: Decimal,
    fixed_research_risk: Decimal,
    remaining_open_risk: Decimal | None = None,
    use_conservative_estimate: bool = True,
    mode: OperatingMode = OperatingMode.SHADOW,
) -> SizingResult:
    """Compute the risk-per-trade fraction under §77a rules.

    Order of the deterministic policy checks:
      1. No edge stats, or unvalidated stats  -> fixed research risk (fallback).
      2. Mode mismatch (stats from another mode) -> fallback (mode independence).
      3. Compute f*; if f* <= 0 -> NO_POSITIVE_EDGE -> size 0.
      4. f_applied = KELLY_FRACTION × f*; risk = min(f_applied, MAX_RISK_PER_TRADE).
      5. Clamp to remaining MAX_OPEN_RISK if provided. Never raise above a ceiling.
    """
    kf = kelly_fraction_setting

    # 1 & 2: unproven / missing / wrong-mode edge -> fixed minimal research risk.
    if edge is None or not edge.validated or edge.mode is not mode:
        reason = (
            "no edge stats" if edge is None
            else "edge not validated (§75/§87)" if not edge.validated
            else f"edge measured in {edge.mode.value}, sizing {mode.value} (mode independence)"
        )
        risk = min(fixed_research_risk, max_risk_per_trade)
        return SizingResult(
            risk_fraction=risk,
            f_star=None,
            f_applied=None,
            kelly_fraction=kf,
            p_used=None if edge is None else edge.p,
            b_used=None if edge is None else edge.b,
            sample_size=None if edge is None else edge.sample_size,
            binding_constraint=BindingConstraint.UNVALIDATED_FALLBACK,
            mode=mode,
            note=f"fallback to fixed research risk: {reason}",
        )

    # Estimation safety: prefer a conservative lower-bound on p when available.
    p_for_sizing = (
        edge.p_lower if (use_conservative_estimate and edge.p_lower is not None) else edge.p
    )
    f_star_f = kelly_fraction(p_for_sizing, edge.b)
    f_star = Decimal(str(f_star_f))

    # 3: positive-edge gate — deterministic, un-overridable.
    if f_star_f <= 0.0:
        return SizingResult(
            risk_fraction=Decimal(0),
            f_star=f_star,
            f_applied=Decimal(0),
            kelly_fraction=kf,
            p_used=p_for_sizing,
            b_used=edge.b,
            sample_size=edge.sample_size,
            binding_constraint=BindingConstraint.NO_POSITIVE_EDGE,
            mode=mode,
            note="f* <= 0: no positive edge, no trade",
        )

    # 4: fractional Kelly, then cap by MAX_RISK_PER_TRADE.
    f_applied = kf * f_star
    binding = BindingConstraint.KELLY
    risk = f_applied
    if risk > max_risk_per_trade:
        risk = max_risk_per_trade
        binding = BindingConstraint.MAX_RISK_PER_TRADE

    # 5: respect remaining open-risk budget (never raise; only reduce).
    if remaining_open_risk is not None and risk > remaining_open_risk:
        risk = max(Decimal(0), remaining_open_risk)
        binding = BindingConstraint.MAX_OPEN_RISK

    return SizingResult(
        risk_fraction=risk,
        f_star=f_star,
        f_applied=f_applied,
        kelly_fraction=kf,
        p_used=p_for_sizing,
        b_used=edge.b,
        sample_size=edge.sample_size,
        binding_constraint=binding,
        mode=mode,
        note="",
    )


def wilson_lower_bound(wins: int, n: int, z: float = 1.96) -> float:
    """Wilson score lower bound for a win probability — a conservative p estimate.

    Used for the 'size against a lower-confidence-bound' discipline (§77a estimation
    safety). z=1.96 ≈ 95%. Returns 0.0 for n == 0.
    """
    if n <= 0:
        return 0.0
    phat = wins / n
    denom = 1.0 + z * z / n
    centre = phat + z * z / (2 * n)
    margin = z * math.sqrt((phat * (1 - phat) + z * z / (4 * n)) / n)
    return max(0.0, (centre - margin) / denom)
