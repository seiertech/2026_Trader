"""Open positions, exposure aggregation and correlated clusters (§66, §77)."""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal

# Correlated risk clusters (§77 MAX_CORRELATED_EXPOSURE). Instruments in the same
# cluster share a dominant driver, so their risk ADDS toward one limit rather than
# counting as independent bets. Config-extendable.
CORRELATION_CLUSTERS: dict[str, str] = {
    # USD-quoted majors move together on dollar direction.
    "EURUSD": "USD_MAJORS",
    "GBPUSD": "USD_MAJORS",
    # Yen crosses behave differently enough to separate.
    "USDJPY": "JPY",
    # Equity indices share the risk-on/risk-off factor.
    "NAS100": "EQUITY_INDICES",
    "US500": "EQUITY_INDICES",
    "UK100": "EQUITY_INDICES",
    # Metals / energy.
    "XAUUSD": "METALS",
    "USOIL": "ENERGY",
}


def cluster_of(instrument: str) -> str:
    """The correlation cluster for an instrument (its own name if unclustered)."""
    return CORRELATION_CLUSTERS.get(instrument, instrument)


@dataclass(frozen=True)
class OpenPosition:
    """An open position and the risk it currently has at stop."""

    instrument: str
    direction: str                 # LONG | SHORT
    size: Decimal
    entry_price: Decimal
    stop_price: Decimal
    # Risk at stop as a fraction of the reference unit (what §77 limits are expressed in).
    risk_fraction: Decimal

    @property
    def nominal_exposure(self) -> Decimal:
        """Nominal (notional) exposure — distinct from risk-at-stop (v1.2)."""
        return abs(self.size * self.entry_price)

    @property
    def signed_risk(self) -> Decimal:
        """Risk signed by direction, so opposing positions partially net."""
        return self.risk_fraction if self.direction == "LONG" else -self.risk_fraction


@dataclass(frozen=True)
class ExposureSummary:
    """Aggregated exposure for the risk gate + the operator view (§77, v1.2)."""

    open_positions: int
    total_risk_fraction: Decimal
    nominal_exposure: Decimal
    by_instrument: dict[str, Decimal] = field(default_factory=dict)
    by_cluster: dict[str, Decimal] = field(default_factory=dict)
    by_direction: dict[str, int] = field(default_factory=dict)


class Portfolio:
    """Holds open positions and answers exposure questions (§66)."""

    def __init__(self) -> None:
        self._positions: dict[str, OpenPosition] = {}

    # ---- mutation ----

    def open(self, position_id: str, position: OpenPosition) -> None:
        if position_id in self._positions:
            raise ValueError(f"position '{position_id}' already open")
        self._positions[position_id] = position

    def close(self, position_id: str) -> OpenPosition | None:
        return self._positions.pop(position_id, None)

    # ---- queries ----

    def positions(self) -> tuple[OpenPosition, ...]:
        return tuple(self._positions.values())

    def exposure(self) -> ExposureSummary:
        by_inst: dict[str, Decimal] = {}
        by_cluster: dict[str, Decimal] = {}
        by_dir: dict[str, int] = {"LONG": 0, "SHORT": 0}
        total = Decimal(0)
        nominal = Decimal(0)

        for p in self._positions.values():
            by_inst[p.instrument] = by_inst.get(p.instrument, Decimal(0)) + p.risk_fraction
            c = cluster_of(p.instrument)
            by_cluster[c] = by_cluster.get(c, Decimal(0)) + p.risk_fraction
            by_dir[p.direction] = by_dir.get(p.direction, 0) + 1
            total += p.risk_fraction
            nominal += p.nominal_exposure

        return ExposureSummary(
            open_positions=len(self._positions),
            total_risk_fraction=total,
            nominal_exposure=nominal,
            by_instrument=by_inst,
            by_cluster=by_cluster,
            by_direction=by_dir,
        )

    def instrument_risk(self, instrument: str) -> Decimal:
        return self.exposure().by_instrument.get(instrument, Decimal(0))

    def cluster_risk(self, instrument: str) -> Decimal:
        """Risk already committed to this instrument's correlated cluster (§77)."""
        return self.exposure().by_cluster.get(cluster_of(instrument), Decimal(0))

    # ---- §66 portfolio-fit question ----

    def would_breach_cluster_limit(
        self, instrument: str, additional_risk: Decimal, max_correlated: Decimal
    ) -> bool:
        """Would adding ``additional_risk`` exceed the correlated-exposure cap (§77)?"""
        return (self.cluster_risk(instrument) + additional_risk) > max_correlated

    def has_opposing_position(self, instrument: str, direction: str) -> bool:
        """True if we already hold the opposite side of this instrument.

        Worth surfacing to the Portfolio Specialist (§66): opening an opposing position
        in the same instrument is usually an accident, not a strategy.
        """
        opposite = "SHORT" if direction == "LONG" else "LONG"
        return any(
            p.instrument == instrument and p.direction == opposite
            for p in self._positions.values()
        )
