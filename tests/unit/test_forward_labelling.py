"""Forward-outcome labelling (§49, §50): per-horizon returns, oriented to bias."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from tc_domain.enums import Timeframe
from tc_domain.market import Bar
from tc_learning.labelling import HORIZONS, label_forward_outcomes


def _bars(prices: list[str], step_min: int = 5) -> list[Bar]:
    base = datetime(2026, 1, 5, 0, 0, tzinfo=UTC)
    out = []
    for i, px in enumerate(prices):
        p = Decimal(px)
        out.append(
            Bar(
                instrument="XAUUSD", timeframe=Timeframe.M5,
                open_time=base + timedelta(minutes=i * step_min),
                open=p, high=p + Decimal("1"), low=p - Decimal("1"),
                close=p, volume=Decimal("1"),
            )
        )
    return out


def test_horizons_match_spec() -> None:
    assert set(HORIZONS) == {"5m", "15m", "30m", "1h", "4h", "1d"}


def test_long_bias_directional_equals_price_move() -> None:
    # Price rises 2650 -> 2652 over the first 5m bar (at +5m).
    bars = _bars(["2650", "2652", "2654"])
    label = label_forward_outcomes(bars[0].open_time, Decimal("2650"), "LONG", bars)
    assert label.price_return["5m"] == Decimal("2")
    assert label.directional_return["5m"] == Decimal("2")  # LONG: same sign


def test_short_bias_flips_sign() -> None:
    bars = _bars(["2650", "2652"])  # price went UP
    label = label_forward_outcomes(bars[0].open_time, Decimal("2650"), "SHORT", bars)
    # Market moved AGAINST a short → directional return negative.
    assert label.price_return["5m"] == Decimal("2")
    assert label.directional_return["5m"] == Decimal("-2")


def test_missing_horizon_is_none_not_fabricated() -> None:
    # Only 3 x 5m bars → 15m data at most; 4h/1d horizons run out.
    bars = _bars(["2650", "2651", "2652"])
    label = label_forward_outcomes(bars[0].open_time, Decimal("2650"), "LONG", bars)
    assert label.price_return["4h"] is None
    assert label.directional_return["1d"] is None
    assert label.outcome_known("5m") is True
    assert label.outcome_known("4h") is False


def test_bad_bias_rejected() -> None:
    bars = _bars(["2650", "2651"])
    with pytest.raises(ValueError):
        label_forward_outcomes(bars[0].open_time, Decimal("2650"), "FLAT", bars)


def test_label_is_keyed_to_decision_time() -> None:
    bars = _bars(["2650", "2651"])
    t = bars[0].open_time
    label = label_forward_outcomes(t, Decimal("2650"), "LONG", bars)
    assert label.decided_at == t  # keyed to decision instant (no leak-back, §89)
