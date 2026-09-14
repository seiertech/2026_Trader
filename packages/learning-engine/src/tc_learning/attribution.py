"""Per-cell performance attribution (§91) with small-sample honesty (§53).

Groups closed trades into cells along the dimensions known at decision time
(instrument, regime, strategy, direction, ... — a subset for the Phase-11 slice; the
full v1.2 attribution dimension list is added as those fields land) and reports, per
cell: sample size, win rate, expectancy in R, profit factor, average R.

The headline is EXPECTANCY, not win rate (§87). And crucially (§53): a cell below the
minimum sample is flagged **WEAK** — the system must never present "8/10 wins" as
strong evidence. Promotion gates (§75) require adequate sample; this is where that
adequacy first becomes visible.

Input is any iterable of trade-like objects exposing: instrument, direction,
r_multiple (Decimal), net_pnl (Decimal), plus optional regime/strategy attributes.
Reconstructed SimulatedTrades from the Experience Store satisfy this.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from decimal import Decimal
from enum import StrEnum

# Minimum trades before a cell's statistics are considered anything but weak (§53).
# A research parameter; the real promotion-gate minimum is per-strategy (§75).
MIN_SAMPLE = 30

_Q = Decimal("0.0001")


class EvidenceStrength(StrEnum):
    WEAK = "WEAK"          # below MIN_SAMPLE — do not act on this cell's numbers (§53)
    PROVISIONAL = "PROVISIONAL"  # >= MIN_SAMPLE but not yet gate-validated (§75)


@dataclass(frozen=True)
class CellStats:
    """Attribution statistics for one cell (§91)."""

    cell: tuple[str, ...]        # the grouping key values, e.g. ("XAUUSD","STRONG_TREND")
    dimensions: tuple[str, ...]  # the dimension names, e.g. ("instrument","regime")
    trades: int
    wins: int
    losses: int
    win_rate: Decimal
    expectancy_r: Decimal        # mean R — the headline (§87)
    avg_r: Decimal
    net_pnl: Decimal
    profit_factor: Decimal | None
    strength: EvidenceStrength

    @property
    def is_weak(self) -> bool:
        return self.strength is EvidenceStrength.WEAK


@dataclass
class _Acc:
    rs: list[Decimal] = field(default_factory=list)
    net: Decimal = Decimal(0)
    wins: int = 0
    losses: int = 0
    gross_profit: Decimal = Decimal(0)
    gross_loss: Decimal = Decimal(0)


def _cell_key(trade: object, dimensions: Sequence[str]) -> tuple[str, ...]:
    out: list[str] = []
    for dim in dimensions:
        val = getattr(trade, dim, None)
        out.append(str(val) if val is not None else "UNKNOWN")
    return tuple(out)


def attribute(
    trades: Iterable[object],
    dimensions: Sequence[str] = ("instrument", "direction"),
    *,
    min_sample: int = MIN_SAMPLE,
) -> list[CellStats]:
    """Group ``trades`` by ``dimensions`` and compute per-cell stats.

    ``dimensions`` are attribute names read off each trade (missing → "UNKNOWN").
    Returns cells sorted by expectancy_r descending, then sample size descending.
    """
    buckets: dict[tuple[str, ...], _Acc] = {}
    for t in trades:
        key = _cell_key(t, dimensions)
        acc = buckets.setdefault(key, _Acc())
        r = Decimal(str(t.r_multiple))
        net = Decimal(str(t.net_pnl))
        acc.rs.append(r)
        acc.net += net
        if net > 0:
            acc.wins += 1
            acc.gross_profit += net
        elif net < 0:
            acc.losses += 1
            acc.gross_loss += -net

    cells: list[CellStats] = []
    for key, acc in buckets.items():
        n = len(acc.rs)
        expectancy_r = (sum(acc.rs, Decimal(0)) / Decimal(n)) if n else Decimal(0)
        win_rate = Decimal(acc.wins) / Decimal(n) if n else Decimal(0)
        pf = (acc.gross_profit / acc.gross_loss) if acc.gross_loss > 0 else None
        strength = (
            EvidenceStrength.WEAK if n < min_sample else EvidenceStrength.PROVISIONAL
        )
        cells.append(
            CellStats(
                cell=key,
                dimensions=tuple(dimensions),
                trades=n,
                wins=acc.wins,
                losses=acc.losses,
                win_rate=win_rate.quantize(_Q),
                expectancy_r=expectancy_r.quantize(_Q),
                avg_r=expectancy_r.quantize(_Q),
                net_pnl=acc.net.quantize(_Q),
                profit_factor=pf.quantize(_Q) if pf is not None else None,
                strength=strength,
            )
        )

    cells.sort(key=lambda c: (c.expectancy_r, c.trades), reverse=True)
    return cells


def format_attribution(cells: Sequence[CellStats]) -> str:
    """Render an attribution table for the operator/CLI."""
    if not cells:
        return "  (no trades to attribute)"
    dims = " / ".join(cells[0].dimensions)
    lines = [
        f"  cell ({dims})".ljust(34)
        + "  n   win%    expR   PF     netPnL   evidence",
        "  " + "-" * 74,
    ]
    for c in cells:
        pf = "n/a" if c.profit_factor is None else f"{c.profit_factor}"
        flag = "⚠ WEAK" if c.is_weak else c.strength.value
        cell_label = ":".join(c.cell)
        lines.append(
            f"  {cell_label:32.32}"
            f"  {c.trades:<3} {c.win_rate!s:>6} {c.expectancy_r!s:>7} {pf:>6}"
            f"  £{c.net_pnl!s:>7}  {flag}"
        )
    lines.append("")
    lines.append(f"  cells below n={MIN_SAMPLE} are flagged WEAK — not evidence of edge (§53).")
    return "\n".join(lines)
