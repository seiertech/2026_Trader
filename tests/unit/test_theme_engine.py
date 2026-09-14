"""Theme engine (§20, §147, TC-ADR-029): durable themes, lifecycle, instrument links."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from tc_domain.enums import ThemeLifecycle
from tc_graph import load_graph_from_config
from tc_themes import ThemeEngine, ThemeEvidence, load_themes_from_config

T0 = datetime(2026, 1, 5, tzinfo=UTC)


def _ev(source: str, at: datetime, weight: float = 1.0, confirmed: bool = False) -> ThemeEvidence:
    return ThemeEvidence(source=source, at=at, weight=weight, market_confirmed=confirmed)


def test_catalogue_loads() -> None:
    eng = load_themes_from_config("config/themes.yaml")
    assert eng.get("AI") is not None
    assert eng.get("MIDDLE_EAST_ESCALATION") is not None


def test_new_theme_starts_emerging_low_strength() -> None:
    eng = ThemeEngine()
    t = eng.register("AI", "AI")
    assert t.lifecycle is ThemeLifecycle.EMERGING
    assert t.strength == 0.0


def test_broad_confirmed_evidence_becomes_established() -> None:
    eng = ThemeEngine()
    # 5 distinct sources over several days, market-confirmed → strong, established.
    for i, src in enumerate(["a", "b", "c", "d", "e"]):
        eng.observe("ENERGY", _ev(src, T0 + timedelta(days=i), weight=1.0, confirmed=True),
                    name="Energy")
    t = eng.get("ENERGY")
    assert t.independent_sources == 5
    assert t.strength >= 65.0
    assert t.lifecycle is ThemeLifecycle.ESTABLISHED


def test_rapid_burst_accelerating() -> None:
    eng = ThemeEngine()
    # Several sources within the same day → high velocity, mid strength → accelerating.
    for src in ["a", "b", "c"]:
        eng.observe("AI", _ev(src, T0, weight=0.7), name="AI")
    t = eng.get("AI")
    assert t.lifecycle in (ThemeLifecycle.ACCELERATING, ThemeLifecycle.ESTABLISHED)


def test_single_weak_source_stays_emerging() -> None:
    eng = ThemeEngine()
    eng.observe("CHINA", _ev("a", T0, weight=0.3), name="China")
    t = eng.get("CHINA")
    assert t.lifecycle is ThemeLifecycle.EMERGING
    assert t.strength <= 25.0


def test_resolve_sets_resolved() -> None:
    eng = ThemeEngine()
    eng.observe("MIDDLE_EAST", _ev("a", T0), name="Middle East")
    eng.resolve("MIDDLE_EAST")
    assert eng.get("MIDDLE_EAST").lifecycle is ThemeLifecycle.RESOLVED
    assert eng.get("MIDDLE_EAST").resolved is True


def test_theme_resolves_to_instruments_via_graph() -> None:
    graph = load_graph_from_config("config/relationships.yaml")
    eng = load_themes_from_config("config/themes.yaml", graph=graph)
    hits = eng.affected_instruments("MIDDLE_EAST_ESCALATION")
    reached = {h.instrument for h in hits}
    assert "USOIL" in reached and "XAUUSD" in reached


def test_no_graph_returns_no_instruments() -> None:
    eng = ThemeEngine()
    eng.register("AI", "AI")
    assert eng.affected_instruments("AI") == ()
