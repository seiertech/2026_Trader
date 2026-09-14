"""tc_graph — the market relationship graph (§18, §21-22, §144-146).

Explicit typed entities (§18) connected by explicit, TEMPORAL relationship edges
(§145: type/direction/strength/confidence/validFrom/validTo/provenance; §146 the graph
does not assume a relationship is permanent). Intelligence propagates from an observed
event/entity to potentially affected TRADABLE instruments (§22), with confidence
DECAYING per hop so first-order links are trusted more than third-order ones (§143).

The graph is the backbone the news, theme and market-leader engines plug into: they
add entities/edges; the convergence engine consumes the propagated impact. Seeded from
config/relationships.yaml (config-driven, §19/§21).
"""

from tc_graph.graph import Entity, PropagationHit, Relationship, RelationshipGraph
from tc_graph.seed import load_graph_from_config, seed_graph

__all__ = [
    "Entity",
    "Relationship",
    "RelationshipGraph",
    "PropagationHit",
    "seed_graph",
    "load_graph_from_config",
]
