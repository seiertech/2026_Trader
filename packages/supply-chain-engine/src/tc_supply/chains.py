"""Supply chains as graph relationships (§144)."""

from __future__ import annotations

from dataclasses import dataclass

from tc_domain.enums import EntityType, RelationshipKind

# The §144 required relationship types (all present in RelationshipKind).
SUPPLY_RELATIONSHIP_TYPES: tuple[RelationshipKind, ...] = (
    RelationshipKind.SUPPLIES,
    RelationshipKind.CONSUMES,
    RelationshipKind.PRODUCES,
    RelationshipKind.DEPENDS_ON,
    RelationshipKind.SUBSTITUTES_FOR,
    RelationshipKind.COMPETES_WITH,
    RelationshipKind.REGULATES,
    RelationshipKind.FINANCES,
    RelationshipKind.INSURES,
    RelationshipKind.TRANSPORTS,
    RelationshipKind.INDEX_MEMBER_OF,
    RelationshipKind.EXPOSED_TO_COUNTRY,
    RelationshipKind.EXPOSED_TO_COMMODITY,
    RelationshipKind.EXPOSED_TO_THEME,
)


@dataclass(frozen=True)
class SupplyChain:
    """An ordered chain of nodes, raw material → … → tradable instrument (§144).

    ``strength``/``confidence`` apply per hop; ``terminal_instrument`` marks the final
    node as the tradable expression so graph propagation can find it.
    """

    id: str
    nodes: tuple[str, ...]
    strength: float = 0.8
    confidence: float = 0.7
    terminal_instrument: str | None = None


def chain_edges(chain: SupplyChain) -> tuple[tuple[str, str, RelationshipKind], ...]:
    """Consecutive SUPPLIES edges along the chain (§144).

    Direction follows the flow of goods: upstream SUPPLIES downstream. A disruption
    therefore propagates the way the real dependency runs.
    """
    return tuple(
        (chain.nodes[i], chain.nodes[i + 1], RelationshipKind.SUPPLIES)
        for i in range(len(chain.nodes) - 1)
    )


def add_chain_to_graph(chain: SupplyChain, graph: object) -> int:
    """Add the chain's nodes + edges to a RelationshipGraph. Returns edges added.

    Nodes are added as INDUSTRY entities by default; the terminal node (if declared) is
    added as an INSTRUMENT so propagation resolves it as a tradable expression (§22).
    Existing nodes are not clobbered — an already-typed entity keeps its type.
    """
    from tc_graph.graph import Entity, Relationship

    if not hasattr(graph, "add_entity") or not hasattr(graph, "add_relationship"):
        raise TypeError("graph must be a RelationshipGraph")

    for node in chain.nodes:
        if graph.entity(node) is not None:
            continue  # respect existing typing
        is_terminal = node == chain.terminal_instrument
        graph.add_entity(
            Entity(
                id=node,
                entity_type=EntityType.INSTRUMENT if is_terminal else EntityType.INDUSTRY,
                name=node.replace("_", " ").title(),
                canonical_instrument=node if is_terminal else None,
            )
        )

    added = 0
    for src, dst, kind in chain_edges(chain):
        graph.add_relationship(
            Relationship(
                source_id=src, target_id=dst, kind=kind,
                strength=chain.strength, confidence=chain.confidence,
                provenance=f"supply_chain:{chain.id}",
            )
        )
        added += 1
    return added
