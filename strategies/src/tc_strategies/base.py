"""Strategy base: the Setup value object and the Strategy protocol (§71, §72)."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol, runtime_checkable

from tc_domain.enums import RegimeType
from tc_domain.market import Bar
from tc_quant.regime import RegimeAssessment


@dataclass(frozen=True)
class Setup:
    """A proposed entry from a strategy. Direction + entry/stop/target + rationale."""

    strategy: str
    direction: str  # "LONG" | "SHORT"
    entry_price: Decimal
    stop_price: Decimal
    target_price: Decimal
    rationale: str

    @property
    def reward_risk(self) -> Decimal:
        risk = abs(self.entry_price - self.stop_price)
        if risk == 0:
            return Decimal(0)
        return abs(self.target_price - self.entry_price) / risk


@runtime_checkable
class Strategy(Protocol):
    """A trading strategy (§71). Regime-aware (§72), stateless, deterministic."""

    name: str
    eligible_regimes: frozenset[RegimeType]

    def find_setup(
        self, bars: Sequence[Bar], regime: RegimeAssessment
    ) -> Setup | None: ...


def regime_ok(strategy: Strategy, regime: RegimeType) -> bool:
    """Whether ``strategy`` is eligible in ``regime`` (§72)."""
    return regime in strategy.eligible_regimes
