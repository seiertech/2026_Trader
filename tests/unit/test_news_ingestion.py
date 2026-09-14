"""News ingestion (§27, §28-32): adapter, dedup, cluster, velocity, novelty."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from tc_news import FixtureProvider, IntelligenceProvider, RawIntelligenceItem, ingest
from tc_news.events import Novelty

T0 = datetime(2026, 1, 5, 10, 0, tzinfo=UTC)


def _item(source: str, title: str, minutes: int, oid: str | None = None) -> RawIntelligenceItem:
    return RawIntelligenceItem(
        provider="fixture", source=source, original_id=oid or f"{source}-{minutes}",
        title=title, published_at=T0 + timedelta(minutes=minutes),
    )


def test_fixture_provider_is_a_provider() -> None:
    p = FixtureProvider("fixture", [_item("BBC", "x", 0)])
    assert isinstance(p, IntelligenceProvider)
    assert len(p.fetch(T0)) == 1
    assert len(p.fetch(T0 + timedelta(minutes=1))) == 0  # since filter


def test_five_orgs_one_event_sourcecount_five() -> None:
    # §29: five orgs reporting the same event => ONE event, source_count = 5.
    title = "Middle East escalation sparks oil price surge"
    items = [
        _item("BBC", title, 0), _item("Guardian", title, 3),
        _item("NPR", "Oil prices surge amid Middle East escalation", 5),
        _item("DW", "Middle East escalation drives oil surge", 7),
        _item("France24", "Oil surges as Middle East escalation intensifies", 10),
    ]
    events = ingest(items)
    assert len(events) == 1
    e = events[0]
    assert e.source_count == 5
    assert set(e.sources) == {"BBC", "Guardian", "NPR", "DW", "France24"}


def test_distinct_events_stay_separate() -> None:
    items = [
        _item("BBC", "Middle East escalation sparks oil surge", 0),
        _item("BBC", "Federal Reserve holds interest rates steady", 2),
    ]
    events = ingest(items)
    assert len(events) == 2


def test_velocity_measured() -> None:
    # §30: velocity = distinct sources per hour across the cluster's span.
    title = "Middle East escalation sparks oil surge"
    items = [_item(f"src{i}", title, i * 6) for i in range(5)]  # 5 sources over 24 min
    e = ingest(items)[0]
    assert e.velocity > 0  # sources per hour (§30)


def test_confidence_rises_with_sources_not_market_evidence() -> None:
    title = "Bank stress deepens as lender shares fall"
    one = ingest([_item("BBC", title, 0)])[0]
    many = ingest([_item(f"s{i}", title, i) for i in range(5)])[0]
    assert many.confidence > one.confidence  # confidence-of-existence (§29)
    assert many.confidence <= 1.0


def test_classification() -> None:
    e = ingest([_item("BBC", "Nvidia chip demand drives semiconductor rally", 0)])[0]
    assert e.category in ("Semiconductors", "AI")
    e2 = ingest([_item("BBC", "OPEC cuts oil output, crude prices jump", 0)])[0]
    assert e2.category == "Energy"


def test_novelty_new_then_repeated() -> None:
    title = "Middle East escalation sparks oil surge"
    first_run = ingest([_item("BBC", title, 0)])
    assert first_run[0].novelty == Novelty.NEW
    # Same event, same sources, later run → REPEATED (must not re-trigger, §31).
    second_run = ingest([_item("BBC", title, 0)], known_events=first_run)
    assert second_run[0].novelty == Novelty.REPEATED


def test_novelty_update_on_new_sources() -> None:
    title = "Middle East escalation sparks oil surge"
    first = ingest([_item("BBC", title, 0)])
    later = ingest(
        [_item("BBC", title, 0), _item("Guardian", title, 5), _item("NPR", title, 8)],
        known_events=first,
    )
    assert later[0].novelty == Novelty.UPDATE  # new corroborating sources (§31)


def test_empty_input() -> None:
    assert ingest([]) == []
