"""Shadow simulator + sizing + costs + metrics (§84–§87). Hand-verified numbers."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from tc_domain.enums import Timeframe
from tc_domain.market import Bar
from tc_shadow.account import ShadowAccount
from tc_shadow.costs import CostModel
from tc_shadow.metrics import compute_metrics
from tc_shadow.simulator import ShadowSimulator, TradeIntent
from tc_shadow.sizing import size_position


def _bar(i: int, o: str, h: str, low: str, c: str) -> Bar:
    return Bar(
        instrument="XAUUSD",
        timeframe=Timeframe.M1,
        open_time=datetime(2026, 1, 5, 0, 0, tzinfo=UTC) + timedelta(minutes=i),
        open=Decimal(o),
        high=Decimal(h),
        low=Decimal(low),
        close=Decimal(c),
        volume=Decimal("1"),
    )


def test_sizing_risk_budget() -> None:
    # £250 * 1% = £2.50 risk; stop distance 5.0; value_per_unit 1 → 0.50 units.
    size = size_position(
        reference_unit=Decimal("250"),
        risk_fraction=Decimal("0.01"),
        entry_price=Decimal("2650"),
        stop_price=Decimal("2645"),
    )
    assert size == Decimal("0.50")


def test_sizing_zero_when_no_stop_distance() -> None:
    assert size_position(
        reference_unit=Decimal("250"),
        risk_fraction=Decimal("0.01"),
        entry_price=Decimal("2650"),
        stop_price=Decimal("2650"),
    ) == Decimal(0)


def test_costs_are_never_zero_for_a_real_size() -> None:
    cm = CostModel()
    c = cm.estimate(Decimal("0.50"))
    assert c.total > 0
    assert c.spread_cost > 0 and c.slippage_cost > 0 and c.commission > 0


def test_target_hit_is_a_net_win() -> None:
    acct = ShadowAccount(Decimal("250"))
    sim = ShadowSimulator(acct, CostModel())
    intent = TradeIntent(
        instrument="XAUUSD",
        direction="LONG",
        entry_price=Decimal("2650"),
        stop_price=Decimal("2645"),      # risk 5.0
        target_price=Decimal("2660"),    # reward 10.0 => 2R
        decided_at=datetime(2026, 1, 5, tzinfo=UTC),
    )
    bars = [
        _bar(1, "2650", "2655", "2649", "2654"),  # drifting up, no hit
        _bar(2, "2654", "2661", "2653", "2660"),  # target 2660 hit
    ]
    t = sim.simulate(intent, bars)
    assert t is not None
    assert t.exit_reason == "TARGET"
    assert t.r_multiple == Decimal("2")  # +10 / 5
    assert t.net_pnl > 0
    assert acct.balance > Decimal("250")  # equity increased


def test_stop_hit_is_a_net_loss_of_about_minus_one_r() -> None:
    acct = ShadowAccount(Decimal("250"))
    sim = ShadowSimulator(acct, CostModel())
    intent = TradeIntent(
        instrument="XAUUSD",
        direction="LONG",
        entry_price=Decimal("2650"),
        stop_price=Decimal("2645"),
        target_price=Decimal("2660"),
        decided_at=datetime(2026, 1, 5, tzinfo=UTC),
    )
    bars = [_bar(1, "2650", "2651", "2644", "2646")]  # low 2644 <= stop 2645 → stop
    t = sim.simulate(intent, bars)
    assert t is not None
    assert t.exit_reason == "STOP"
    assert t.r_multiple == Decimal("-1")
    assert t.net_pnl < 0  # loss plus costs


def test_both_hit_same_bar_assumes_stop_first() -> None:
    acct = ShadowAccount(Decimal("250"))
    sim = ShadowSimulator(acct, CostModel())
    intent = TradeIntent(
        instrument="XAUUSD", direction="LONG",
        entry_price=Decimal("2650"), stop_price=Decimal("2645"),
        target_price=Decimal("2660"),
        decided_at=datetime(2026, 1, 5, tzinfo=UTC),
    )
    bars = [_bar(1, "2650", "2661", "2644", "2655")]  # both stop & target in range
    t = sim.simulate(intent, bars)
    assert t is not None
    assert t.exit_reason == "STOP"  # conservative worst-case


def test_metrics_expectancy_and_profit_factor() -> None:
    acct = ShadowAccount(Decimal("250"))
    sim = ShadowSimulator(acct, CostModel())

    def run(direction: str, entry: str, stop: str, target: str, bars: list[Bar]):
        return sim.simulate(
            TradeIntent(
                instrument="XAUUSD", direction=direction,
                entry_price=Decimal(entry), stop_price=Decimal(stop),
                target_price=Decimal(target),
                decided_at=datetime(2026, 1, 5, tzinfo=UTC),
            ),
            bars,
        )

    trades = []
    trades.append(run("LONG", "2650", "2645", "2660",
                       [_bar(1, "2650", "2661", "2649", "2660")]))  # win 2R
    trades.append(run("LONG", "2650", "2645", "2660",
                       [_bar(1, "2650", "2651", "2644", "2646")]))  # loss -1R
    trades = [t for t in trades if t is not None]
    m = compute_metrics(trades)
    assert m.trades == 2
    assert m.wins == 1 and m.losses == 1
    assert m.win_rate == Decimal("0.5000")
    assert m.profit_factor is not None
    # R measures the price outcome (pre-cost): (2R win + -1R loss) / 2 = 0.5R.
    assert m.expectancy_r == Decimal("0.5000")
    # Costs live in the CASH ledger: net expectancy per trade is dragged by fees,
    # and total costs are strictly positive (§87 — expectancy AFTER costs).
    assert m.total_costs > 0
    assert m.expectancy_cash < m.net_pnl / Decimal(2) + m.total_costs  # cost drag present
    assert m.max_drawdown >= 0


def test_empty_metrics_are_zeroed() -> None:
    m = compute_metrics([])
    assert m.trades == 0
    assert m.profit_factor is None
