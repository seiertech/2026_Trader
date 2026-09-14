"""End-to-end XAUUSD golden path (§123), Shadow mode, on the replay provider.

Flow (the spec's golden path, minus the not-yet-built intelligence/AI stages):

    MT5 price (replay)  ->  quant + regime  ->  strategy setup (opportunity)
      ->  risk-sized shadow trade  ->  simulated outcome  ->  metrics

No-look-ahead is preserved throughout: at each decision point the strategy sees only
bars already closed at the replay clock, and the trade is simulated over the bars that
come AFTER the decision (which is what would have happened, revealed forward).

Operating mode is asserted SHADOW (§79): simulated execution, no broker orders. AI and
the news/convergence stages are intentionally absent here — this proves the mechanical
pipeline before breadth (§161).
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

from tc_domain.enums import OperatingMode, Timeframe
from tc_quant.regime import classify_regime
from tc_quant.series import closes, highs, lows
from tc_shadow.account import ShadowAccount
from tc_shadow.costs import CostModel
from tc_shadow.metrics import PerformanceMetrics, compute_metrics
from tc_shadow.simulator import ShadowSimulator, SimulatedTrade, TradeIntent

from tc_runtime.strategy import find_setup


@dataclass(frozen=True)
class GoldenPathResult:
    instrument: str
    mode: OperatingMode
    bars_processed: int
    opportunities: int
    trades: list[SimulatedTrade]
    metrics: PerformanceMetrics
    starting_balance: Decimal
    ending_balance: Decimal


def run_golden_path(
    csv_path: str | Path,
    *,
    instrument: str = "XAUUSD",
    decision_timeframe: Timeframe = Timeframe.H1,
    forward_bars: int = 24,          # how many decision-TF bars a trade may run
    reentry_cooldown_bars: int = 6,  # avoid stacking overlapping trades on one signal
    starting_balance: Decimal = Decimal("250"),
) -> GoldenPathResult:
    """Run the golden path over a replay CSV and return trades + metrics.

    Imports the provider lazily so the runtime has no hard import-time coupling to a
    concrete provider (the Windows Mt5 provider swaps in here later, ADR-032).
    """
    from tc_market_data.replay import interval_delta, provider_from_csv

    mode = OperatingMode.SHADOW  # asserted: no broker orders (§79)

    provider = provider_from_csv(csv_path, instrument, Timeframe.M1)
    account = ShadowAccount(starting_balance)
    sim = ShadowSimulator(account, CostModel(), risk_fraction=Decimal("0.01"))

    # Walk the whole 1m series to build the full set of decision-TF bars.
    while provider.step() is not None:
        pass
    tf_bars = provider.aggregated_bars(instrument, decision_timeframe)

    tf_delta = interval_delta(decision_timeframe)
    trades: list[SimulatedTrade] = []
    opportunities = 0
    cooldown_until = -1

    # At decision index i, the strategy sees bars[:i+1] (all closed) and the trade is
    # simulated over bars[i+1 : i+1+forward_bars] (the future, revealed forward).
    for i in range(len(tf_bars)):
        if i <= cooldown_until:
            continue
        window = tf_bars[: i + 1]
        regime = classify_regime(highs(window), lows(window), closes(window))
        setup = find_setup(window, regime)
        if setup is None:
            continue
        opportunities += 1

        future = tf_bars[i + 1 : i + 1 + forward_bars]
        if not future:
            break
        intent = TradeIntent(
            instrument=instrument,
            direction=setup.direction,
            entry_price=setup.entry_price,
            stop_price=setup.stop_price,
            target_price=setup.target_price,
            decided_at=tf_bars[i].open_time + tf_delta,
        )
        trade = sim.simulate(intent, future)
        if trade is not None:
            trades.append(trade)
            cooldown_until = i + reentry_cooldown_bars

    return GoldenPathResult(
        instrument=instrument,
        mode=mode,
        bars_processed=len(tf_bars),
        opportunities=opportunities,
        trades=trades,
        metrics=compute_metrics(trades),
        starting_balance=starting_balance,
        ending_balance=account.balance,
    )


def format_report(result: GoldenPathResult) -> str:
    """Human-readable summary for the operator / CLI."""
    m = result.metrics
    pf = "n/a" if m.profit_factor is None else f"{m.profit_factor}"
    lines = [
        "── TRADING COMMAND · XAUUSD GOLDEN PATH (SHADOW) ─────────────────",
        f"  mode              : {result.mode.value}   (simulated execution, no broker orders)",
        f"  instrument        : {result.instrument}",
        f"  decision bars     : {result.bars_processed}",
        f"  opportunities     : {result.opportunities}",
        f"  trades simulated  : {m.trades}",
        "",
        f"  wins / losses     : {m.wins} / {m.losses}   (win rate {m.win_rate})",
        f"  profit factor     : {pf}",
        f"  expectancy (R)    : {m.expectancy_r}   ← headline; success ≠ win rate (§87)",
        f"  expectancy (cash) : £{m.expectancy_cash} per trade (AFTER costs)",
        f"  avg MFE / MAE (R) : {m.avg_mfe_r} / {m.avg_mae_r}",
        f"  total costs       : £{m.total_costs}",
        f"  max drawdown      : £{m.max_drawdown}",
        "",
        f"  reference unit    : £{result.starting_balance}  (risk/R unit — NOT a target, §74/§0)",
        f"  ledger balance    : £{result.ending_balance}   (Shadow equity; no return target)",
        "──────────────────────────────────────────────────────────────────",
    ]
    if m.trades > 0 and m.expectancy_r <= 0:
        lines.append("  NOTE: non-positive expectancy — a valid, honest result (§0/§130).")
    return "\n".join(lines)


def _default_sample() -> Path:
    return Path(__file__).resolve().parents[4] / "data" / "reference" / "XAUUSD_1m_sample.csv"


def main() -> int:
    result = run_golden_path(_default_sample())
    print(format_report(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
