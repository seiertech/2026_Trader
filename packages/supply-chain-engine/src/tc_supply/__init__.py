"""tc_supply — Supply-chain intelligence (§144, TC-ADR-024).

Supply chain is a first-class RELATIONSHIP domain (§144): raw material → component →
manufacturer → industry → market leader → index → tradable instrument. It is expressed
as graph edges (the §144 relationship types already exist in RelationshipKind), so a
disruption anywhere on a chain propagates through the same machinery as any other event
(§22) — no parallel pipeline.

This module builds chain edges into the relationship graph and walks a chain to its
tradable expressions.
"""

from tc_supply.chains import (
    SUPPLY_RELATIONSHIP_TYPES,
    SupplyChain,
    add_chain_to_graph,
    chain_edges,
)

__all__ = [
    "SupplyChain",
    "chain_edges",
    "add_chain_to_graph",
    "SUPPLY_RELATIONSHIP_TYPES",
]
