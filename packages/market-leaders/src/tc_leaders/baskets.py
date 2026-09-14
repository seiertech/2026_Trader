"""Baskets, the one-factor collapse (§148), and the convergence bridge.

basket_factor(): given the recent % moves of a basket's constituents, produce a single
derived factor:
  * magnitude  — mean absolute move (how much the basket moved), 0..100 strength
  * coherence  — how aligned the constituents were (all same sign = coherent). A move
    with high coherence is a real sector factor; a mixed move is noise and is
    down-weighted, because incoherent moves are NOT a single factor.
  * direction  — the sign of the mean move.

The factor is emitted as ONE CORPORATE_SECTOR DomainInput with a correlation_group set
to the basket id — so even if several baskets feed convergence, each basket is one
independent contribution and its own constituents never double-count (§148, §39).
"""

from __future__ import annotations

from dataclasses import dataclass
from statistics import fmean

from tc_domain.enums import ConvergenceDomain, ImpactDirection


@dataclass(frozen=True)
class Basket:
    """A configurable market-leader basket (§19)."""

    id: str
    name: str
    sector: str
    members: tuple[str, ...]


@dataclass(frozen=True)
class ConstituentMove:
    """One company's recent move, as a signed percentage (e.g. -2.5 = down 2.5%)."""

    company: str
    pct_move: float


@dataclass(frozen=True)
class BasketFactor:
    """The single derived factor for a basket (§148)."""

    basket_id: str
    sector: str
    strength: float           # 0..100
    coherence: float          # 0..1 (1 = all constituents moved the same way)
    direction: ImpactDirection
    mean_pct: float
    n: int
    detail: str = ""


# Research parameters (calibrate in Shadow).
FULL_STRENGTH_PCT = 3.0   # a ~3% mean absolute move reads as full strength


def basket_factor(basket: Basket, moves: list[ConstituentMove]) -> BasketFactor | None:
    """Collapse constituent moves into ONE factor (§148). None if no data."""
    relevant = [m for m in moves if m.company in basket.members]
    if not relevant:
        return None

    signs_up = sum(1 for m in relevant if m.pct_move > 0)
    signs_dn = sum(1 for m in relevant if m.pct_move < 0)
    n = len(relevant)
    mean_pct = fmean(m.pct_move for m in relevant)
    mean_abs = fmean(abs(m.pct_move) for m in relevant)

    # Coherence: dominance of the majority sign (0.5 balanced .. 1.0 unanimous).
    dominant = max(signs_up, signs_dn)
    coherence = dominant / n if n else 0.0

    # Magnitude strength (0..100), scaled so ~FULL_STRENGTH_PCT ≈ 100.
    magnitude = min(100.0, (mean_abs / FULL_STRENGTH_PCT) * 100.0)
    # Incoherent moves are not a single factor — down-weight by coherence.
    strength = round(magnitude * coherence, 2)

    if mean_pct > 0:
        direction = ImpactDirection.BULLISH
    elif mean_pct < 0:
        direction = ImpactDirection.BEARISH
    else:
        direction = ImpactDirection.UNCERTAIN

    return BasketFactor(
        basket_id=basket.id,
        sector=basket.sector,
        strength=strength,
        coherence=round(coherence, 3),
        direction=direction,
        mean_pct=round(mean_pct, 3),
        n=n,
        detail=f"{n} constituents, mean {mean_pct:+.2f}%, coherence {coherence:.2f}",
    )


def basket_convergence_input(factor: BasketFactor):
    """Adapt a BasketFactor to a Convergence DomainInput (§148 -> §36).

    Returns a DomainInput in the CORPORATE_SECTOR domain, tagged with the basket id as
    its correlation_group so the Convergence Engine treats the whole basket as ONE
    independent contribution and never lets its constituents double-count (§39, §148).
    """
    from tc_convergence import DomainInput  # local import: keep leaders dep-light

    return DomainInput(
        domain=ConvergenceDomain.CORPORATE_SECTOR,
        strength=factor.strength,
        direction=factor.direction,
        rationale=f"{factor.basket_id}: {factor.detail}",
        correlation_group=f"basket:{factor.basket_id}",
    )
