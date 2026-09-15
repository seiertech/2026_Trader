"""Gazetteer-based entity extraction (§18, §28).

Each gazetteer entry maps surface forms -> (graph node id, EntityType). Matching is
case-insensitive on word boundaries, so "Fed" matches "the Fed said" but not "federated".
Extraction returns mentions with their matched surface form so provenance is auditable
(§124).
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from tc_domain.enums import EntityType

# Surface form -> (node id, type). Config-extendable; seeded with the §18/§19 entities
# that the relationship graph already knows about.
DEFAULT_GAZETTEER: dict[str, tuple[str, EntityType]] = {
    # Central banks / institutions
    "bank of england": ("BOE", EntityType.CENTRAL_BANK),
    "boe": ("BOE", EntityType.CENTRAL_BANK),
    "federal reserve": ("FED", EntityType.CENTRAL_BANK),
    "fed": ("FED", EntityType.CENTRAL_BANK),
    "ecb": ("ECB", EntityType.CENTRAL_BANK),
    # Currencies
    "pound": ("GBP", EntityType.CURRENCY),
    "sterling": ("GBP", EntityType.CURRENCY),
    "dollar": ("USD", EntityType.CURRENCY),
    "euro": ("EUR", EntityType.CURRENCY),
    # Commodities
    "gold": ("GOLD", EntityType.COMMODITY),
    "oil": ("OIL", EntityType.COMMODITY),
    "crude": ("OIL", EntityType.COMMODITY),
    "copper": ("COPPER", EntityType.COMMODITY),
    "silver": ("SILVER", EntityType.COMMODITY),
    # Sectors / themes
    "semiconductor": ("SEMICONDUCTORS", EntityType.SECTOR),
    "semiconductors": ("SEMICONDUCTORS", EntityType.SECTOR),
    "chipmaker": ("SEMICONDUCTORS", EntityType.SECTOR),
    "technology": ("TECHNOLOGY", EntityType.SECTOR),
    "banking": ("BANKING", EntityType.SECTOR),
    # Companies (intelligence inputs only, §6/TC-ADR-008)
    "nvidia": ("NVIDIA", EntityType.COMPANY),
    "microsoft": ("MICROSOFT", EntityType.COMPANY),
    "apple": ("APPLE", EntityType.COMPANY),
    "tsmc": ("TSMC", EntityType.COMPANY),
    "asml": ("ASML", EntityType.COMPANY),
    "shell": ("SHELL", EntityType.COMPANY),
    "bp": ("BP", EntityType.COMPANY),
    # Countries / regions
    "china": ("CHINA", EntityType.COUNTRY),
    "united states": ("US", EntityType.COUNTRY),
    "uk": ("UK", EntityType.COUNTRY),
    "middle east": ("MIDDLE_EAST", EntityType.REGION),
}


@dataclass(frozen=True)
class EntityMention:
    """One extracted entity, with the surface form that matched (provenance, §124)."""

    node_id: str
    entity_type: EntityType
    surface: str


def extract_entities(
    text: str, gazetteer: dict[str, tuple[str, EntityType]] | None = None
) -> tuple[EntityMention, ...]:
    """Extract typed entity mentions from ``text``. Deduplicated by node id.

    Longer surface forms win, so "bank of england" is preferred over "england" and
    "middle east" over a bare "east" — avoids fragmenting a multi-word entity.
    """
    gaz = gazetteer or DEFAULT_GAZETTEER
    low = (text or "").lower()
    found: dict[str, EntityMention] = {}

    # Longest-first so multi-word forms take precedence.
    for surface in sorted(gaz, key=len, reverse=True):
        if re.search(rf"\b{re.escape(surface)}\b", low):
            node_id, etype = gaz[surface]
            found.setdefault(node_id, EntityMention(node_id, etype, surface))
    return tuple(found.values())


def resolve_to_graph(
    mentions: tuple[EntityMention, ...], graph: object
) -> tuple[str, ...]:
    """Return the mention node ids that exist in ``graph``.

    Entities the graph does not know are dropped rather than invented — an unknown
    entity cannot propagate anywhere meaningful, and fabricating a node would create
    phantom relationships (§44 spirit: never invent facts).
    """
    if not hasattr(graph, "entity"):
        return ()
    return tuple(m.node_id for m in mentions if graph.entity(m.node_id) is not None)
