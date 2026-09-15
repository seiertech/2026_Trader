"""Cross-market propagation + cleanest-expression selection (§149, TC-ADR-030)."""

from __future__ import annotations

from dataclasses import dataclass

from tc_domain.enums import ConvergenceDomain, ImpactDirection, MarketPermission

# §149 propagation paths, as ordered chains of drivers ending in market expressions.
PROPAGATION_PATHS: dict[str, tuple[str, ...]] = {
    "BOND_YIELDS": ("BOND_YIELDS", "USD", "GOLD", "EQUITY_INDICES"),
    "OIL": ("OIL", "ENERGY_EQUITIES", "INFLATION_EXPECTATIONS", "FX", "EQUITY_INDICES"),
    "SEMICONDUCTORS": ("SEMICONDUCTORS", "NAS100", "GLOBAL_TECH"),
    "CHINA_DEMAND": ("CHINA_DEMAND", "COPPER", "MINERS", "UK100", "ASX200"),
    "EUROPEAN_ENERGY": ("EUROPEAN_ENERGY", "DAX", "EUR", "UK100", "US500"),
}


@dataclass(frozen=True)
class CrossMarketCandidate:
    """A candidate tradable expression of a driver, with what makes it clean or not."""

    instrument: str
    path_confidence: float          # 0..1 from graph propagation
    hops: int
    permission: MarketPermission
    # Execution quality proxies — a technically-correct expression you cannot trade
    # cleanly is not the cleanest expression (§149, EXECUTION_QUALITY domain).
    typical_spread: float = 0.0
    liquidity_score: float = 1.0    # 0..1

    @property
    def tradable(self) -> bool:
        return self.permission in (
            MarketPermission.SHADOW_TRADABLE, MarketPermission.LIVE_TRADABLE
        )

    @property
    def cleanliness(self) -> float:
        """Composite: confident, few hops, liquid, tradable.

        Hops are penalised because each additional link is another assumption (§143).
        """
        if not self.tradable:
            return 0.0
        hop_penalty = 1.0 / (1.0 + max(0, self.hops - 1) * 0.35)
        return round(self.path_confidence * hop_penalty * self.liquidity_score, 4)


def rank_expressions(
    candidates: list[CrossMarketCandidate],
) -> tuple[CrossMarketCandidate, ...]:
    """Rank candidates by cleanliness, best first. Untradable candidates rank last."""
    return tuple(sorted(candidates, key=lambda c: c.cleanliness, reverse=True))


def cleanest_expression(
    candidates: list[CrossMarketCandidate],
) -> CrossMarketCandidate | None:
    """The cleanest tradable expression, or None if nothing is tradable (TC-ADR-030)."""
    ranked = rank_expressions(candidates)
    return ranked[0] if ranked and ranked[0].cleanliness > 0 else None


def crossmarket_convergence_input(
    candidate: CrossMarketCandidate,
    direction: ImpactDirection,
    *,
    driver: str = "",
    freshness: float = 1.0,
):
    """Adapt a cross-market candidate to a CROSS_MARKET convergence input (§150)."""
    from tc_convergence import DomainInput

    return DomainInput(
        domain=ConvergenceDomain.CROSS_MARKET,
        strength=round(candidate.cleanliness * 100.0, 2),
        direction=direction,
        rationale=(
            f"cross-market via {driver or 'driver'} -> {candidate.instrument} "
            f"({candidate.hops} hop(s), path conf {candidate.path_confidence:.2f})"
        ),
        freshness=freshness,
        # One driver is one factor across all the markets it touches (§39).
        correlation_group=f"crossmarket:{driver or candidate.instrument}",
    )
