"""Event families/status/blackout (§15-17,§77), entity extraction (§18), macro (§46,§63)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from tc_domain.enums import EntityType, EventStatus, ImpactDirection
from tc_entities import extract_entities, resolve_to_graph
from tc_events import BlackoutWindow, EventFamily, classify_event_type, in_blackout, next_status
from tc_graph import load_graph_from_config
from tc_macro import MacroRelease, SurpriseDirection, macro_convergence_input, surprise_score

T0 = datetime(2026, 1, 5, 13, 30, tzinfo=UTC)


# --- event families (§15) ---

def test_event_families() -> None:
    assert classify_event_type("CPI") is EventFamily.SCHEDULED
    assert classify_event_type("MILITARY_ESCALATION") is EventFamily.BREAKING
    assert classify_event_type("BANKING_STRESS") is EventFamily.DEVELOPING
    assert classify_event_type("something_else") is EventFamily.UNKNOWN


# --- status lifecycle (§16) ---

def test_status_emerging_single_source() -> None:
    s = next_status(current=EventStatus.EMERGING, source_count=1,
                    age=timedelta(hours=1), since_last_update=timedelta(minutes=5))
    assert s is EventStatus.EMERGING


def test_status_developing_then_confirmed() -> None:
    dev = next_status(current=EventStatus.EMERGING, source_count=2,
                      age=timedelta(hours=1), since_last_update=timedelta(minutes=5))
    assert dev is EventStatus.DEVELOPING
    conf = next_status(current=dev, source_count=4,
                       age=timedelta(hours=1), since_last_update=timedelta(minutes=5))
    assert conf is EventStatus.CONFIRMED


def test_status_stable_when_quiet() -> None:
    s = next_status(current=EventStatus.CONFIRMED, source_count=5,
                    age=timedelta(days=1), since_last_update=timedelta(hours=8))
    assert s is EventStatus.STABLE


def test_status_resolved_is_terminal() -> None:
    s = next_status(current=EventStatus.CONFIRMED, source_count=9,
                    age=timedelta(days=1), since_last_update=timedelta(minutes=1),
                    resolved=True)
    assert s is EventStatus.RESOLVED
    assert next_status(current=s, source_count=99, age=timedelta(days=9),
                       since_last_update=timedelta(minutes=1)) is EventStatus.RESOLVED


# --- blackout (§77) ---

def test_high_impact_creates_blackout() -> None:
    w = [BlackoutWindow("CPI", T0)]
    assert in_blackout(T0 - timedelta(minutes=10), w)   # inside the before-window
    assert in_blackout(T0 + timedelta(minutes=10), w)   # inside the after-window
    assert not in_blackout(T0 - timedelta(hours=2), w)  # well clear


def test_low_impact_scheduled_does_not_blackout() -> None:
    # EARNINGS is scheduled but not high-impact for the tradable universe → context only.
    assert not in_blackout(T0, [BlackoutWindow("EARNINGS", T0)])


# --- entity extraction (§18) ---

def test_extracts_typed_entities() -> None:
    m = extract_entities("Bank of England holds rates as gold climbs")
    ids = {x.node_id for x in m}
    assert "BOE" in ids and "GOLD" in ids
    boe = next(x for x in m if x.node_id == "BOE")
    assert boe.entity_type is EntityType.CENTRAL_BANK


def test_multiword_preferred_over_substring() -> None:
    m = extract_entities("Middle East tensions rise")
    assert "MIDDLE_EAST" in {x.node_id for x in m}


def test_word_boundary_respected() -> None:
    # "fed" must not match inside "federated"
    assert extract_entities("federated learning research") == ()


def test_resolve_to_graph_drops_unknown() -> None:
    g = load_graph_from_config("config/relationships.yaml")
    m = extract_entities("Bank of England and Nvidia and gold")
    resolved = resolve_to_graph(m, g)
    assert "BOE" in resolved and "GOLD" in resolved
    assert "NVIDIA" not in resolved  # not a node in the seed graph → dropped, not invented


# --- macro (§46, §63) ---

def test_surprise_and_score() -> None:
    r = MacroRelease("CPI", "US", actual=3.4, forecast=3.0, previous=3.1, typical_surprise=0.2)
    assert abs(r.surprise - 0.4) < 1e-9
    assert abs(r.normalised_surprise - 2.0) < 1e-9
    assert surprise_score(r) > 50


def test_cpi_beat_is_bullish() -> None:
    r = MacroRelease("CPI", "US", actual=3.4, forecast=3.0, previous=3.1)
    di = macro_convergence_input(r)
    assert di.direction is ImpactDirection.BULLISH


def test_unemployment_beat_is_bearish() -> None:
    # Higher unemployment than forecast => weak economy => bearish (DOVISH_BEARISH).
    r = MacroRelease("UNEMPLOYMENT", "US", actual=4.5, forecast=4.1, previous=4.0)
    di = macro_convergence_input(r, polarity=SurpriseDirection.DOVISH_BEARISH)
    assert di.direction is ImpactDirection.BEARISH


def test_inline_print_is_uncertain() -> None:
    r = MacroRelease("CPI", "US", actual=3.0, forecast=3.0, previous=3.0)
    di = macro_convergence_input(r)
    assert di.direction is ImpactDirection.UNCERTAIN  # no directional information


def test_macro_input_is_correlation_grouped() -> None:
    r = MacroRelease("CPI", "US", actual=3.4, forecast=3.0, previous=3.1)
    di = macro_convergence_input(r)
    assert di.correlation_group == "macro:US:CPI"  # same release can't double-count
