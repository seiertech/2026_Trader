"""Relationship graph (§18, §21-22, §143-146): typed nodes, temporal edges, propagation."""

from __future__ import annotations

from datetime import UTC, datetime

from tc_domain.enums import EntityType, RelationshipKind
from tc_graph import Entity, Relationship, RelationshipGraph, load_graph_from_config
from tc_graph.graph import PropagationHit

CONFIG = "config/relationships.yaml"


def test_seed_loads_from_config() -> None:
    g = load_graph_from_config(CONFIG)
    assert len(g) > 0
    assert g.entity("XAUUSD") is not None
    assert g.entity("XAUUSD").entity_type is EntityType.INSTRUMENT


def test_middle_east_escalation_reaches_oil_and_gold() -> None:
    g = load_graph_from_config(CONFIG)
    hits = g.propagate("MIDDLE_EAST_ESCALATION")
    reached = {h.instrument for h in hits}
    # §22: escalation -> energy risk -> oil/gold -> USOIL/XAUUSD.
    assert "USOIL" in reached
    assert "XAUUSD" in reached
    # Both bullish (polarity +1 along the path).
    for h in hits:
        if h.instrument in ("USOIL", "XAUUSD"):
            assert h.polarity == 1


def test_boe_reaches_gbpusd() -> None:
    g = load_graph_from_config(CONFIG)
    hits = {h.instrument: h for h in g.propagate("BOE")}
    assert "GBPUSD" in hits
    assert hits["GBPUSD"].hops >= 2  # BOE -> GBP -> GBPUSD


def test_inverse_polarity_propagates_sign() -> None:
    g = load_graph_from_config(CONFIG)
    hits = {h.instrument: h for h in g.propagate("USD_STRENGTH")}
    # USD strength -> USD -> gold (inverse) => bearish gold.
    assert "XAUUSD" in hits
    assert hits["XAUUSD"].polarity == -1


def test_confidence_decays_with_hops() -> None:
    g = load_graph_from_config(CONFIG)
    hits = {h.instrument: h for h in g.propagate("MIDDLE_EAST_ESCALATION")}
    # Deeper path (escalation..XAUUSD is 4 nodes) has confidence < 1.
    assert 0.0 < hits["XAUUSD"].confidence < 1.0


def test_max_depth_prunes() -> None:
    g = load_graph_from_config(CONFIG)
    shallow = g.propagate("MIDDLE_EAST_ESCALATION", max_depth=1)
    deep = g.propagate("MIDDLE_EAST_ESCALATION", max_depth=4)
    assert len(deep) >= len(shallow)


def test_temporal_edge_respected() -> None:
    g = RelationshipGraph()
    g.add_entity(Entity("A", EntityType.THEME, "A"))
    g.add_entity(Entity("X", EntityType.INSTRUMENT, "X", canonical_instrument="X"))
    g.add_relationship(
        Relationship("A", "X", RelationshipKind.EXPOSED_TO_THEME,
                     valid_from=datetime(2026, 1, 1, tzinfo=UTC),
                     valid_to=datetime(2026, 6, 1, tzinfo=UTC))
    )
    # Inside the window: reachable.
    assert g.propagate("A", when=datetime(2026, 3, 1, tzinfo=UTC))
    # After validTo: edge inactive (§146).
    assert g.propagate("A", when=datetime(2026, 9, 1, tzinfo=UTC)) == ()


def test_unknown_source_returns_empty() -> None:
    g = load_graph_from_config(CONFIG)
    assert g.propagate("NOPE") == ()


def test_propagation_hit_shape() -> None:
    g = load_graph_from_config(CONFIG)
    hits = g.propagate("MIDDLE_EAST_ESCALATION")
    assert all(isinstance(h, PropagationHit) for h in hits)
    assert all(h.path[0] == "MIDDLE_EAST_ESCALATION" for h in hits)
