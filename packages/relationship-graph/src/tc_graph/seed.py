"""Load the relationship graph from config (§19, §21 config-driven)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from tc_domain.enums import EntityType, RelationshipKind

from tc_graph.graph import Entity, Relationship, RelationshipGraph


def seed_graph(
    entities: list[dict[str, Any]], relationships: list[dict[str, Any]]
) -> RelationshipGraph:
    """Build a graph from parsed entity/relationship dicts."""
    g = RelationshipGraph()
    for e in entities:
        g.add_entity(
            Entity(
                id=e["id"],
                entity_type=EntityType(e["type"]),
                name=e.get("name", e["id"]),
                canonical_instrument=e.get("canonical"),
            )
        )
    for r in relationships:
        g.add_relationship(
            Relationship(
                source_id=r["source"],
                target_id=r["target"],
                kind=RelationshipKind(r["kind"]),
                strength=float(r.get("strength", 1.0)),
                confidence=float(r.get("confidence", 1.0)),
                polarity=int(r.get("polarity", 1)),
                provenance=r.get("provenance", "seed"),
            )
        )
    return g


def load_graph_from_config(
    config_path: str | Path = "config/relationships.yaml",
) -> RelationshipGraph:
    """Load and build the graph from a YAML config file."""
    p = Path(config_path)
    with p.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    return seed_graph(data.get("entities", []), data.get("relationships", []))
