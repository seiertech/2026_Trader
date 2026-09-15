"""Historical Analogue engine (§51-53): matching, outcome stats, small-sample honesty."""

from __future__ import annotations

from tc_historical import AnalogueQuery, HistoricalCase, find_analogues
from tc_historical.analogue import EvidenceStrength


def _case(r: float, *, instrument="XAUUSD", regime="STRONG_TREND",
          direction="LONG", band="75-100") -> HistoricalCase:
    return HistoricalCase(instrument, regime, direction, band, r)


def test_no_analogues_is_weak_zero() -> None:
    r = find_analogues([], AnalogueQuery(instrument="XAUUSD"))
    assert r.sample_size == 0
    assert r.is_weak


def test_matching_filters_by_keys() -> None:
    cases = [
        _case(2.0, instrument="XAUUSD"),
        _case(1.0, instrument="EURUSD"),
        _case(-1.0, instrument="XAUUSD"),
    ]
    r = find_analogues(cases, AnalogueQuery(instrument="XAUUSD"))
    assert r.sample_size == 2  # only XAUUSD cases


def test_eight_of_ten_wins_is_weak_not_strong() -> None:
    # THE §53 point: 8/10 wins must NOT be presented as strong evidence.
    cases = [_case(2.0) for _ in range(8)] + [_case(-1.0) for _ in range(2)]
    r = find_analogues(cases, AnalogueQuery(regime="STRONG_TREND"))
    assert r.sample_size == 10
    assert r.win_rate == 0.8
    assert r.is_weak                       # below MIN_SAMPLE (30)
    assert r.win_rate_ci is not None       # and the CI is wide
    lo, hi = r.win_rate_ci
    assert hi - lo > 0.3                   # genuinely uncertain despite 80% point est.


def test_large_sample_is_provisional() -> None:
    cases = [_case(1.0) for _ in range(40)]
    r = find_analogues(cases, AnalogueQuery(regime="STRONG_TREND"), min_sample=30)
    assert not r.is_weak
    assert r.strength is EvidenceStrength.PROVISIONAL


def test_outcome_stats() -> None:
    cases = [_case(2.0), _case(2.0), _case(-1.0), _case(-1.0)]
    r = find_analogues(cases, AnalogueQuery())
    assert r.win_rate == 0.5
    assert r.avg_positive_return == 2.0
    assert r.avg_negative_return == -1.0
    assert r.avg_r == 0.5           # (2+2-1-1)/4
    assert r.expectancy == 0.5
    assert r.mfe == 2.0
    assert r.mae == -1.0


def test_max_drawdown_in_r() -> None:
    # Sequence +2, -1, -1, +2 → cumulative 2,1,0,2 → peak 2, trough 0 → dd 2.
    cases = [_case(2.0), _case(-1.0), _case(-1.0), _case(2.0)]
    r = find_analogues(cases, AnalogueQuery())
    assert r.max_drawdown == 2.0


def test_tiny_sample_no_ci() -> None:
    # Under 10 cases: no CI offered (not enough to bother, §53 discipline).
    r = find_analogues([_case(1.0), _case(-1.0)], AnalogueQuery())
    assert r.win_rate_ci is None
    assert r.is_weak
