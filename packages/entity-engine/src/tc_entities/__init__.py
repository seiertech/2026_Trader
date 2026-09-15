"""tc_entities — entity extraction & resolution (§18, §28 entity-extraction stage).

Turns free text (news titles/bodies) into typed graph entities (§18) using a
configurable gazetteer — deterministic and explainable, no model required. Extracted
entities are resolved to canonical graph node ids so the relationship graph can
propagate from them to affected instruments (§22).

Deliberately dictionary-based rather than statistical: the spec favours deterministic
computation where it suffices (Part XXXI §2), and a gazetteer is auditable — you can
always answer "why was this tagged?".
"""

from tc_entities.extract import (
    DEFAULT_GAZETTEER,
    EntityMention,
    extract_entities,
    resolve_to_graph,
)

__all__ = [
    "EntityMention",
    "extract_entities",
    "resolve_to_graph",
    "DEFAULT_GAZETTEER",
]
