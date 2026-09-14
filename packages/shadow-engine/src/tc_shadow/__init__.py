"""tc_shadow — the Shadow execution simulator (Part XIX).

SHADOW is the mandatory initial mode (§79): real intelligence, real decisions,
SIMULATED execution, NO broker orders. This package simulates trades realistically —
spread, estimated slippage, commission — against a virtual £250 reference-unit account
(§74, §84, §85) and measures outcomes in R and expectancy (§86).

Money math is Decimal end-to-end. The £250 is a REFERENCE UNIT for expressing risk and
expectancy, not a capital base to compound and not a target (§74, §0, TC-ADR-016/017).
The simulator refuses trades a real £250 account could not execute (§85).
"""

from tc_shadow.account import ShadowAccount
from tc_shadow.costs import CostModel, TradingCosts
from tc_shadow.metrics import PerformanceMetrics, compute_metrics
from tc_shadow.simulator import ShadowSimulator, SimulatedTrade, TradeIntent
from tc_shadow.sizing import size_position

__all__ = [
    "ShadowAccount",
    "CostModel",
    "TradingCosts",
    "PerformanceMetrics",
    "compute_metrics",
    "ShadowSimulator",
    "SimulatedTrade",
    "TradeIntent",
    "size_position",
]
