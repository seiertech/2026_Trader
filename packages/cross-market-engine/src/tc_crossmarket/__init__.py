"""tc_crossmarket — Cross-market propagation (§149, TC-ADR-030).

Monitors how moves propagate BETWEEN markets (§149) — bond yields → USD → gold →
equities, oil → energy equities → inflation expectations → FX, and so on.

The doctrinal point (TC-ADR-030): the system searches for the CLEANEST TRADABLE
EXPRESSION of an event rather than reflexively trading the market geographically or
sectorally closest to it. Given a driver, this module ranks the candidate instruments by
path confidence and liquidity/permission, so "European energy shock" can conclude that
the cleanest expression is DAX or EUR rather than a thinly-traded local proxy.
"""

from tc_crossmarket.propagation import (
    PROPAGATION_PATHS,
    CrossMarketCandidate,
    cleanest_expression,
    crossmarket_convergence_input,
    rank_expressions,
)

__all__ = [
    "PROPAGATION_PATHS",
    "CrossMarketCandidate",
    "rank_expressions",
    "cleanest_expression",
    "crossmarket_convergence_input",
]
