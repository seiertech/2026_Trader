"""tc_historical — the Historical Analogue Engine (Part XII, §51-53).

For a current Evidence Pack, find historically comparable conditions and determine
what subsequently occurred (§51). Reports the §52 outputs (sample size, win rate,
average positive/negative return, average R, expectancy, MFE, MAE, max drawdown,
confidence interval where appropriate).

§53 is MANDATORY and load-bearing: small samples are identified as WEAK evidence. The
engine SHALL NOT treat "8 / 10 historical wins" as strong without accounting for
sample size and selection. Every result carries an evidence-strength flag and, where
the sample allows, a confidence interval on the win rate.

Deterministic. No look-ahead: analogues are drawn only from cases whose outcome was
known before the query's timestamp (§89) — the caller supplies as-of-filtered cases.
"""

from tc_historical.analogue import (
    AnalogueQuery,
    AnalogueResult,
    HistoricalCase,
    find_analogues,
)

__all__ = [
    "HistoricalCase",
    "AnalogueQuery",
    "AnalogueResult",
    "find_analogues",
]
