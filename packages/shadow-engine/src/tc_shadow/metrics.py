"""Performance metrics for the Shadow ledger (§86, §87, v1.2 performance domain).

Deterministic statistics over a set of closed trades. Success is NOT win rate (§87):
the headline is EXPECTANCY AFTER COSTS. Metrics are reported in both cash (net P&L)
and R, so results are comparable across instruments and position sizes (§74).

All cash math is Decimal. Ratios are Decimal too, guarded against division by zero.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal

from tc_shadow.simulator import SimulatedTrade

_Q = Decimal("0.0001")


@dataclass(frozen=True)
class PerformanceMetrics:
    trades: int
    wins: int
    losses: int
    breakeven: int
    win_rate: Decimal          # 0..1
    gross_profit: Decimal
    gross_loss: Decimal        # positive magnitude of losing trades
    net_pnl: Decimal
    profit_factor: Decimal | None   # None when there are no losses
    expectancy_cash: Decimal   # mean net P&L per trade
    expectancy_r: Decimal      # mean R per trade — the headline (§87)
    avg_r: Decimal
    avg_winner: Decimal
    avg_loser: Decimal
    largest_winner: Decimal
    largest_loser: Decimal
    max_drawdown: Decimal      # on the net-P&L equity curve, positive magnitude
    total_costs: Decimal
    avg_mfe_r: Decimal
    avg_mae_r: Decimal


def _mean(xs: Sequence[Decimal]) -> Decimal:
    return (sum(xs, Decimal(0)) / Decimal(len(xs))) if xs else Decimal(0)


def compute_metrics(trades: Sequence[SimulatedTrade]) -> PerformanceMetrics:
    n = len(trades)
    if n == 0:
        z = Decimal(0)
        return PerformanceMetrics(
            0, 0, 0, 0, z, z, z, z, None, z, z, z, z, z, z, z, z, z, z, z
        )

    wins = [t for t in trades if t.net_pnl > 0]
    losses = [t for t in trades if t.net_pnl < 0]
    breakeven = [t for t in trades if t.net_pnl == 0]

    gross_profit = sum((t.net_pnl for t in wins), Decimal(0))
    gross_loss = -sum((t.net_pnl for t in losses), Decimal(0))  # positive magnitude
    net_pnl = sum((t.net_pnl for t in trades), Decimal(0))
    total_costs = sum((t.costs for t in trades), Decimal(0))

    profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else None
    win_rate = Decimal(len(wins)) / Decimal(n)

    r_values = [t.r_multiple for t in trades]
    expectancy_r = _mean(r_values)
    expectancy_cash = net_pnl / Decimal(n)

    max_dd = _max_drawdown([t.net_pnl for t in trades])

    return PerformanceMetrics(
        trades=n,
        wins=len(wins),
        losses=len(losses),
        breakeven=len(breakeven),
        win_rate=win_rate.quantize(_Q),
        gross_profit=gross_profit.quantize(_Q),
        gross_loss=gross_loss.quantize(_Q),
        net_pnl=net_pnl.quantize(_Q),
        profit_factor=profit_factor.quantize(_Q) if profit_factor is not None else None,
        expectancy_cash=expectancy_cash.quantize(_Q),
        expectancy_r=expectancy_r.quantize(_Q),
        avg_r=expectancy_r.quantize(_Q),
        avg_winner=(_mean([t.net_pnl for t in wins])).quantize(_Q),
        avg_loser=(_mean([t.net_pnl for t in losses])).quantize(_Q),
        largest_winner=(max((t.net_pnl for t in wins), default=Decimal(0))).quantize(_Q),
        largest_loser=(min((t.net_pnl for t in losses), default=Decimal(0))).quantize(_Q),
        max_drawdown=max_dd.quantize(_Q),
        total_costs=total_costs.quantize(_Q),
        avg_mfe_r=(_mean([t.mfe_r for t in trades])).quantize(_Q),
        avg_mae_r=(_mean([t.mae_r for t in trades])).quantize(_Q),
    )


def _max_drawdown(pnls: Sequence[Decimal]) -> Decimal:
    """Max peak-to-trough drop on the cumulative net-P&L curve (positive magnitude)."""
    peak = Decimal(0)
    cum = Decimal(0)
    max_dd = Decimal(0)
    for p in pnls:
        cum += p
        peak = max(peak, cum)
        max_dd = max(max_dd, peak - cum)
    return max_dd
