"""tc_strategies — strategy families (§71, §72).

Each strategy declares the regimes it is eligible for (§72) and, given the visible
(no-look-ahead) bars and the classified regime, either proposes a Setup or returns
None (NO OPPORTUNITY is valid, §3). No strategy is presumed profitable (TC-ADR-020) —
the learning/attribution engine decides which, if any, actually has edge.

Initial families (§71): trend-following, breakout, momentum-continuation,
mean-reversion, volatility-expansion. Event-reaction and event+price convergence
arrive with the intelligence engines (Phase 4+).
"""

from tc_strategies.base import Setup, Strategy
from tc_strategies.registry import REGISTRY, eligible_strategies, get_strategy

__all__ = [
    "Setup",
    "Strategy",
    "REGISTRY",
    "get_strategy",
    "eligible_strategies",
]
