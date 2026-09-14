"""tc_market_data — market-data provider contracts and implementations.

The provider interface (§96) is the seam between the Trading Command "brain" and the
broker "edge" (TC-ADR-004, TC-ADR-010, TC-ADR-032). Engines depend ONLY on the
abstract protocols here — never on MetaTrader5 or any concrete broker.

Phase 1 (Shadow) ships the deterministic :class:`ReplayMarketDataProvider`. The live
``Mt5MarketDataProvider`` implements the same protocol on the dedicated Windows
machine (ADR-032) and drops in unchanged.
"""

from tc_market_data.aggregation import aggregate, bucket_start, can_aggregate
from tc_market_data.contracts import MarketDataProvider
from tc_market_data.replay import ReplayMarketDataProvider

__all__ = [
    "MarketDataProvider",
    "ReplayMarketDataProvider",
    "aggregate",
    "bucket_start",
    "can_aggregate",
]
