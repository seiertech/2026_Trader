"""Convergence Engine (§36-39, §150): independent agreement, correlated collapse."""

from __future__ import annotations

from tc_convergence import DomainInput, score_convergence
from tc_domain.enums import ConvergenceDomain as CD
from tc_domain.enums import ImpactDirection as D


def _in(domain, strength, direction, **kw) -> DomainInput:
    return DomainInput(domain=domain, strength=strength, direction=direction, **kw)


def test_empty_is_zero_uncertain() -> None:
    r = score_convergence([])
    assert r.score == 0.0
    assert r.direction is D.UNCERTAIN


def test_single_strong_domain_positive() -> None:
    r = score_convergence([_in(CD.MARKET_STRUCTURE, 90, D.BULLISH)])
    assert r.score > 0
    assert r.direction is D.BULLISH
    assert r.agreeing_domains == 1


def test_multiple_independent_agreeing_beats_single() -> None:
    one = score_convergence([_in(CD.MARKET_STRUCTURE, 80, D.BULLISH)])
    many = score_convergence([
        _in(CD.MARKET_STRUCTURE, 80, D.BULLISH),
        _in(CD.MOMENTUM_VOLATILITY, 80, D.BULLISH),
        _in(CD.MACRO_MONETARY, 80, D.BULLISH),
        _in(CD.CROSS_MARKET, 80, D.BULLISH),
    ])
    # Independent agreement across domains scores higher than a lone domain (§37).
    assert many.score > one.score
    assert many.agreeing_domains == 4


def test_conflicting_evidence_lowers_score() -> None:
    agree = score_convergence([
        _in(CD.MARKET_STRUCTURE, 80, D.BULLISH),
        _in(CD.MACRO_MONETARY, 80, D.BULLISH),
    ])
    conflict = score_convergence([
        _in(CD.MARKET_STRUCTURE, 80, D.BULLISH),
        _in(CD.MACRO_MONETARY, 80, D.BEARISH),
    ])
    assert conflict.score < agree.score
    assert conflict.conflicting_domains >= 1


def test_correlated_evidence_collapsed() -> None:
    # Three correlated "semiconductor" reads must NOT count as three independent (§39).
    correlated = score_convergence([
        _in(CD.CORPORATE_SECTOR, 80, D.BEARISH, correlation_group="semis"),
        _in(CD.CORPORATE_SECTOR, 80, D.BEARISH, correlation_group="semis"),
        _in(CD.CORPORATE_SECTOR, 80, D.BEARISH, correlation_group="semis"),
    ])
    independent = score_convergence([
        _in(CD.CORPORATE_SECTOR, 80, D.BEARISH),
        _in(CD.MACRO_MONETARY, 80, D.BEARISH),
        _in(CD.CROSS_MARKET, 80, D.BEARISH),
    ])
    assert "semis" in correlated.collapsed_groups
    # Genuinely independent agreement should out-score collapsed correlated evidence.
    assert independent.score > correlated.score


def test_freshness_and_confidence_downweight() -> None:
    fresh = score_convergence([_in(CD.NEWS_EVENT, 90, D.BULLISH, freshness=1.0)])
    stale = score_convergence([_in(CD.NEWS_EVENT, 90, D.BULLISH, freshness=0.2)])
    assert stale.score < fresh.score


def test_components_retained() -> None:
    r = score_convergence([
        _in(CD.MARKET_STRUCTURE, 70, D.BULLISH, rationale="higher highs"),
    ])
    # Score never replaces explainability (§38): components are kept.
    assert r.contributing
    assert r.contributing[0].domain is CD.MARKET_STRUCTURE
    assert r.detail


def test_score_bounded_0_100() -> None:
    r = score_convergence([_in(CD.MARKET_STRUCTURE, 100, D.BULLISH)] * 1)
    assert 0.0 <= r.score <= 100.0
