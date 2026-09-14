"""End-to-end XAUUSD golden path (§123), Shadow mode, on the replay provider.

Full pipeline (the spec's golden path, minus the not-yet-built intelligence/AI stages):

    MT5 price (replay) -> quant + regime -> eligible strategies (opportunity)
      -> adversarial critic (§67) -> risk gate (§77) -> decision engine (§68-70)
      -> risk-sized shadow trade -> simulated outcome -> forward labels -> metrics

Every opportunity now flows through the full OODA middle before execution — critic,
risk gate and decision engine, not the old strategy->shadow shortcut. WAIT and REJECT
are real outcomes; only LONG/SHORT reaches the simulator.

No-look-ahead is preserved throughout: at each decision point strategies see only bars
already closed at the replay clock, and the trade is simulated over the bars AFTER the
decision. Operating mode is asserted SHADOW (§79): simulated execution, no broker
orders. AI stages are intentionally absent — this proves the mechanical pipeline
before breadth (§161).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path

from tc_convergence import DomainInput, score_convergence
from tc_decision import CriticInputs, DecisionInputs, criticise, decide
from tc_domain.enums import (
    ConvergenceDomain,
    DecisionOutcome,
    ImpactDirection,
    OperatingMode,
    Timeframe,
)
from tc_quant.regime import classify_regime
from tc_quant.series import closes, highs, lows
from tc_risk.gate import PortfolioState, ProposedTrade, evaluate
from tc_shadow.account import ShadowAccount
from tc_shadow.costs import CostModel
from tc_shadow.metrics import PerformanceMetrics, compute_metrics
from tc_shadow.simulator import ShadowSimulator, SimulatedTrade, TradeIntent
from tc_strategies import eligible_strategies


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
    rejected: int = 0  # opportunities detected but not taken (§50) — still labelled
    # Decision-outcome tally across the run (§69): how the pipeline resolved each
    # opportunity before/at execution.
    decisions: dict[str, int] = field(
        default_factory=lambda: {"LONG": 0, "SHORT": 0, "WAIT": 0, "REJECT": 0}
    )


def run_golden_path(
    csv_path: str | Path,
    *,
    instrument: str = "XAUUSD",
    decision_timeframe: Timeframe = Timeframe.H1,
    forward_bars: int = 24,          # how many decision-TF bars a trade may run
    reentry_cooldown_bars: int = 6,  # avoid stacking overlapping trades on one signal
    starting_balance: Decimal = Decimal("250"),
    store: object | None = None,     # optional ExperienceStore to persist trades into
) -> GoldenPathResult:
    """Run the golden path over a replay CSV and return trades + metrics.

    If ``store`` (an ExperienceStore) is given, each simulated trade is appended to it
    as an immutable experience record (§88) — this is how a run's results survive for
    later learning/attribution.

    Imports the provider lazily so the runtime has no hard import-time coupling to a
    concrete provider (the Windows Mt5 provider swaps in here later, ADR-032).
    """
    from tc_market_data.replay import interval_delta, provider_from_csv

    persist = None
    persist_label = None
    if store is not None:
        from tc_database.labels import persist_opportunity_label as persist_label
        from tc_database.trades import persist_trade as persist

    # Forward-outcome labeller is always used (traded AND rejected, §49/§50); it only
    # persists when a store is given.
    from tc_learning.labelling import label_forward_outcomes

    mode = OperatingMode.SHADOW  # asserted: no broker orders (§79)

    provider = provider_from_csv(csv_path, instrument, Timeframe.M1)
    account = ShadowAccount(starting_balance)
    # §77a: fractional Kelly is wired in, but the demo strategy is UNVALIDATED (no
    # out-of-sample stats exist yet), so sizing falls back to the fixed §76 research
    # risk — exactly as TC-CR-001 mandates. Kelly activates only once a strategy
    # passes the §75/§87 gates and a validated EdgeStats is supplied to simulate().
    sim = ShadowSimulator(
        account,
        CostModel(),
        risk_fraction=Decimal("0.01"),       # §76 fixed research default
        kelly_fraction=Decimal("0.25"),      # §77a quarter-Kelly
        max_risk_per_trade=Decimal("0.01"),  # §77 ceiling
        mode=mode,
    )

    # Walk the whole 1m series to build the full set of decision-TF bars.
    while provider.step() is not None:
        pass
    tf_bars = provider.aggregated_bars(instrument, decision_timeframe)

    controls = _risk_controls()

    tf_delta = interval_delta(decision_timeframe)
    trades: list[SimulatedTrade] = []
    opportunities = 0
    rejected = 0
    decisions = {"LONG": 0, "SHORT": 0, "WAIT": 0, "REJECT": 0}
    cooldown_until = -1
    seq = 0  # unique suffix so ids stay distinct when several strategies fire on one bar

    # Portfolio/session state threaded through the run for the risk gate + critic.
    consecutive_losses = 0

    # At decision index i, strategies see bars[:i+1] (all closed) and the trade is
    # simulated over bars[i+1 : i+1+forward_bars] (the future, revealed forward).
    for i in range(len(tf_bars)):
        if i <= cooldown_until:
            continue
        window = tf_bars[: i + 1]
        regime = classify_regime(highs(window), lows(window), closes(window))

        future = tf_bars[i + 1 : i + 1 + forward_bars]
        if not future:
            break
        decided_at = tf_bars[i].open_time + tf_delta

        took_trade_this_bar = False
        # Every eligible strategy for the current regime gets to propose (§72).
        for strat in eligible_strategies(regime.regime):
            setup = strat.find_setup(window, regime)
            if setup is None:
                continue
            opportunities += 1
            seq += 1
            opp_id = f"{instrument}:{decided_at.isoformat()}:{strat.name}"

            # Forward-label EVERY opportunity — whatever the decision (§49/§50).
            label = label_forward_outcomes(
                decided_at=decided_at,
                reference_price=setup.entry_price,
                bias=setup.direction,
                future_bars=future,
            )
            cell = {"instrument": instrument, "regime": regime.regime.value,
                    "direction": setup.direction, "strategy": strat.name}

            # --- Convergence (§36-39): real evidence-domain score (no more ADX proxy) ---
            conv = score_convergence(
                _convergence_inputs(regime, setup.direction)
            )

            # --- OODA middle: critic (§67) -> risk gate (§77) -> decision (§68-70) ---
            critic = criticise(
                CriticInputs(
                    reward_risk=setup.reward_risk,
                    has_stop=True,
                    convergence_score=conv.score,
                    min_reward_risk=_control_decimal(controls, "MIN_REWARD_RISK"),
                    regime_eligible=True,  # strategy was selected by regime already
                )
            )
            gate = evaluate(
                ProposedTrade(
                    instrument=instrument, direction=setup.direction,
                    requested_risk_fraction=_control_decimal(controls, "MAX_RISK_PER_TRADE"),
                    reward_risk=setup.reward_risk, has_stop=True,
                ),
                PortfolioState(
                    open_positions=len(trades) if False else 0,  # single-position slice
                    consecutive_losses=consecutive_losses,
                    kill_switch=bool(controls.get("KILL_SWITCH")),
                ),
                controls,
            )
            decision = decide(
                DecisionInputs(
                    opportunity_id=opp_id, evidence_pack_id="", instrument=instrument,
                    bias=setup.direction, regime=regime.regime,
                    convergence_score=conv.score, decided_at=decided_at,
                    critic=critic, gate_verdict=gate.verdict.value,
                    gate_reasons=gate.reasons,
                ),
                decision_id=f"d:{opp_id}",
            )
            decisions[decision.outcome.value] += 1

            if decision.outcome not in (DecisionOutcome.LONG, DecisionOutcome.SHORT):
                # WAIT/REJECT: not traded, but still measured (§50).
                rejected += 1
                if persist_label is not None:
                    persist_label(store, instrument=instrument, outcome="REJECTED",
                                  reject_reason=decision.outcome.value, label=label, cell=cell)
                continue

            # Decision says trade → simulate it (§79 shadow).
            intent = TradeIntent(
                instrument=instrument, direction=setup.direction,
                entry_price=setup.entry_price, stop_price=setup.stop_price,
                target_price=setup.target_price, decided_at=decided_at,
                strategy=strat.name, regime=regime.regime.value,
            )
            trade = sim.simulate(intent, future)
            if trade is None:
                # Sizing/affordability rejected post-decision (§85) — still measured.
                rejected += 1
                if persist_label is not None:
                    persist_label(store, instrument=instrument, outcome="REJECTED",
                                  reject_reason="not_sized_or_afforded", label=label, cell=cell)
                continue

            trades.append(trade)
            if trade.net_pnl < 0:
                consecutive_losses += 1
            else:
                consecutive_losses = 0
            if persist is not None:
                persist(store, trade)
            if persist_label is not None:
                persist_label(store, instrument=instrument, outcome="TRADED",
                              reject_reason="", label=label, cell=cell)
            took_trade_this_bar = True
            break  # one position at a time in this slice

        if took_trade_this_bar:
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
        rejected=rejected,
        decisions=decisions,
    )


def _convergence_inputs(regime, bias: str) -> list[DomainInput]:
    """Build convergence domain inputs from the quant/regime read (§36, §150).

    Only the price-derived domains are available in this slice; macro / news /
    cross-market / historical domains attach as those engines feed in. Each domain
    points in the strategy's proposed direction with a strength derived from the
    regime's own signals — so the convergence score reflects how strongly the price
    structure and momentum actually support the bias, not a raw indicator count.
    """
    direction = ImpactDirection.BULLISH if bias == "LONG" else ImpactDirection.BEARISH
    inputs: list[DomainInput] = []

    # MARKET_STRUCTURE — trend strength via ADX (0..100-ish), regime relevance high.
    adx = regime.adx or 0.0
    inputs.append(
        DomainInput(
            domain=ConvergenceDomain.MARKET_STRUCTURE,
            strength=min(100.0, adx * 2.0),  # ADX ~25 => strength ~50 (research param)
            direction=direction,
            rationale=f"ADX {adx:.1f}, regime {regime.regime.value}",
            regime_relevance=1.0,
        )
    )
    # MOMENTUM_VOLATILITY — from the regime's volatility ratio if present.
    vol_ratio = regime.vol_ratio
    if vol_ratio is not None:
        # Expansion in the trade direction is supportive; contraction less so.
        strength = min(100.0, max(0.0, (vol_ratio - 0.5) * 80.0))
        inputs.append(
            DomainInput(
                domain=ConvergenceDomain.MOMENTUM_VOLATILITY,
                strength=strength,
                direction=direction,
                rationale=f"vol ratio {vol_ratio:.2f}",
            )
        )
    return inputs


def _risk_controls() -> dict[str, object]:
    """Load the §77 risk controls from config, falling back to safe defaults.

    Kept local + defensive so the runtime never hard-fails if config paths shift; the
    values only tune the deterministic gate/critic, never bypass them.
    """
    try:
        import sys

        cfg_src = Path(__file__).resolve().parents[4] / "packages" / "config" / "src"
        if str(cfg_src) not in sys.path:
            sys.path.insert(0, str(cfg_src))
        from tc_config import load_config

        cfg_dir = Path(__file__).resolve().parents[4] / "config"
        return dict(load_config(cfg_dir).risk.risk_controls)
    except Exception:
        # Defensive defaults mirror config/risk.yaml (§76/§77).
        return {
            "MAX_RISK_PER_TRADE": 0.01, "MIN_REWARD_RISK": 1.5, "MAX_OPEN_RISK": 0.04,
            "MAX_INSTRUMENT_EXPOSURE": 0.02, "MAX_POSITIONS": 3,
            "MAX_CONSECUTIVE_LOSSES": 5, "MAX_DAILY_LOSS": 0.03,
            "MANDATORY_STOP": True, "STALE_DATA_BLOCK": True, "KILL_SWITCH": False,
            "MAX_SPREAD": None,
        }


def _control_decimal(controls: dict[str, object], key: str) -> Decimal:
    v = controls.get(key)
    try:
        return Decimal(str(v)) if v is not None and not isinstance(v, bool) else Decimal(0)
    except Exception:
        return Decimal(0)


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
        f"  decisions         : LONG {result.decisions['LONG']}  SHORT "
        f"{result.decisions['SHORT']}  WAIT {result.decisions['WAIT']}  "
        f"REJECT {result.decisions['REJECT']}   (§69)",
        f"  trades simulated  : {m.trades}",
        f"  rejected (labelled): {result.rejected}   (measured anyway, §50)",
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
