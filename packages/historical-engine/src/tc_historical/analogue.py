"""Historical analogue matching + outcome statistics (§51-53).

A HistoricalCase is a past decision context (instrument, regime, direction,
convergence band) plus the realised outcome (R multiple). find_analogues() selects
cases matching the query's discrete key dimensions and computes the §52 statistics
over their outcomes.

Statistical discipline (§53): the result carries an EvidenceStrength — WEAK below a
minimum sample, else PROVISIONAL — and a Wilson confidence interval on the win rate
where the sample supports one. "8/10 wins" surfaces as WEAK with a wide interval, not
as a strong signal.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum

# Below this, historical evidence is WEAK regardless of how good it looks (§53).
MIN_SAMPLE = 30


class EvidenceStrength(StrEnum):
    WEAK = "WEAK"
    PROVISIONAL = "PROVISIONAL"


@dataclass(frozen=True)
class HistoricalCase:
    """A past decision context + its realised outcome."""

    instrument: str
    regime: str
    direction: str            # LONG | SHORT
    convergence_band: str     # e.g. "0-25","25-50","50-75","75-100"
    r_multiple: float         # realised R (pre-cost outcome)


@dataclass(frozen=True)
class AnalogueQuery:
    """The current context to find analogues for (discrete match keys)."""

    instrument: str | None = None
    regime: str | None = None
    direction: str | None = None
    convergence_band: str | None = None


@dataclass(frozen=True)
class AnalogueResult:
    """§52 outputs over the matched analogues, with §53 honesty."""

    sample_size: int
    win_rate: float
    avg_positive_return: float   # mean R of winners
    avg_negative_return: float   # mean R of losers (negative)
    avg_r: float
    expectancy: float            # == avg_r (mean R per case)
    mfe: float                   # best R observed
    mae: float                   # worst R observed
    max_drawdown: float          # deepest cumulative-R trough (positive magnitude)
    win_rate_ci: tuple[float, float] | None  # Wilson 95% CI, if sample allows
    strength: EvidenceStrength
    detail: str = ""

    @property
    def is_weak(self) -> bool:
        return self.strength is EvidenceStrength.WEAK


def _matches(case: HistoricalCase, q: AnalogueQuery) -> bool:
    return (
        (q.instrument is None or case.instrument == q.instrument)
        and (q.regime is None or case.regime == q.regime)
        and (q.direction is None or case.direction == q.direction)
        and (q.convergence_band is None or case.convergence_band == q.convergence_band)
    )


def _wilson_ci(wins: int, n: int, z: float = 1.96) -> tuple[float, float]:
    phat = wins / n
    denom = 1.0 + z * z / n
    centre = phat + z * z / (2 * n)
    half = z * math.sqrt((phat * (1 - phat) + z * z / (4 * n)) / n)
    return (max(0.0, (centre - half) / denom), min(1.0, (centre + half) / denom))


def _max_drawdown_r(rs: Sequence[float]) -> float:
    peak = 0.0
    cum = 0.0
    dd = 0.0
    for r in rs:
        cum += r
        peak = max(peak, cum)
        dd = max(dd, peak - cum)
    return dd


def find_analogues(
    cases: Sequence[HistoricalCase],
    query: AnalogueQuery,
    *,
    min_sample: int = MIN_SAMPLE,
) -> AnalogueResult:
    """Match ``cases`` to ``query`` and compute §52 outcome stats with §53 honesty."""
    matched = [c for c in cases if _matches(c, query)]
    n = len(matched)
    if n == 0:
        return AnalogueResult(
            0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, None,
            EvidenceStrength.WEAK, "no analogues",
        )

    rs = [c.r_multiple for c in matched]
    winners = [r for r in rs if r > 0]
    losers = [r for r in rs if r < 0]
    wins = len(winners)

    win_rate = wins / n
    avg_pos = sum(winners) / len(winners) if winners else 0.0
    avg_neg = sum(losers) / len(losers) if losers else 0.0
    avg_r = sum(rs) / n
    strength = EvidenceStrength.WEAK if n < min_sample else EvidenceStrength.PROVISIONAL
    # CI only when the sample is meaningful enough to bother (§53 discipline).
    ci = _wilson_ci(wins, n) if n >= 10 else None

    detail = (
        f"n={n} win_rate={win_rate:.2f} avg_r={avg_r:.3f} "
        f"strength={strength.value}"
        + ("" if n >= min_sample else f" (below min_sample={min_sample})")
    )
    return AnalogueResult(
        sample_size=n,
        win_rate=round(win_rate, 4),
        avg_positive_return=round(avg_pos, 4),
        avg_negative_return=round(avg_neg, 4),
        avg_r=round(avg_r, 4),
        expectancy=round(avg_r, 4),
        mfe=round(max(rs), 4),
        mae=round(min(rs), 4),
        max_drawdown=round(_max_drawdown_r(rs), 4),
        win_rate_ci=(round(ci[0], 4), round(ci[1], 4)) if ci else None,
        strength=strength,
        detail=detail,
    )
