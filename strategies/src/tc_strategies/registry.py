"""Strategy registry (§71, §72).

A configuration-driven catalogue of the available strategies. The runtime asks the
registry which strategies are eligible for the current regime (§72) and evaluates
each. Adding a strategy is a matter of registering it here — no pipeline changes.
"""

from __future__ import annotations

from tc_domain.enums import RegimeType

from tc_strategies.base import Strategy, regime_ok
from tc_strategies.families import (
    MeanReversion,
    MomentumContinuation,
    TrendFollowing,
    VolatilityExpansion,
)

# The initial V1 research families (§71). Order is stable for deterministic iteration.
REGISTRY: tuple[Strategy, ...] = (
    TrendFollowing(),
    MomentumContinuation(),
    MeanReversion(),
    VolatilityExpansion(),
)

_BY_NAME: dict[str, Strategy] = {s.name: s for s in REGISTRY}


def get_strategy(name: str) -> Strategy | None:
    return _BY_NAME.get(name)


def eligible_strategies(regime: RegimeType) -> tuple[Strategy, ...]:
    """Strategies eligible to trade in ``regime`` (§72)."""
    return tuple(s for s in REGISTRY if regime_ok(s, regime))
