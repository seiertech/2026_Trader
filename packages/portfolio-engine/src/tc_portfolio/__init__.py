"""tc_portfolio — Portfolio & exposure management (§66, §77, v1.2 exposure view).

Tracks open positions and aggregates exposure the way the Risk Engine needs it (§77):
open risk, per-instrument risk, and CORRELATED-CLUSTER risk — because three long
positions in correlated instruments is one bet, not three (§77 MAX_CORRELATED_EXPOSURE,
same principle as §39/§148).

Also answers the Portfolio Specialist question (§66): is this candidate appropriate
given what we already hold? Exposure is reported both nominal and risk-at-stop (v1.2).
"""

from tc_portfolio.portfolio import (
    CORRELATION_CLUSTERS,
    ExposureSummary,
    OpenPosition,
    Portfolio,
    cluster_of,
)

__all__ = [
    "OpenPosition",
    "Portfolio",
    "ExposureSummary",
    "cluster_of",
    "CORRELATION_CLUSTERS",
]
