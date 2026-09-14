"""Entities, temporal relationship edges, and event->instrument propagation.

Propagation (§22, §143): a breadth-first walk from a source entity along edges valid
at a given time. Each hop multiplies confidence by the edge strength × edge confidence
and a per-hop decay, so higher-order paths carry lower confidence (§143). The walk
stops at a max depth and returns the tradable INSTRUMENT nodes reached, with the best
(highest-confidence) path to each and the net direction implied along that path.

Directionality: an edge may be POSITIVE (same direction) or INVERSE (flips), letting
e.g. "USD strength -> gold bearish" propagate a sign. Instruments reached are the
"cleanest tradable expression" candidates (§149, TC-ADR-030) for whatever seeded the
walk.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from datetime import datetime

from tc_domain.enums import EntityType, RelationshipKind


@dataclass(frozen=True)
class Entity:
    """A typed node in the graph (§18)."""

    id: str
    entity_type: EntityType
    name: str
    # For INSTRUMENT nodes, the canonical tradable id (may equal id).
    canonical_instrument: str | None = None


@dataclass(frozen=True)
class Relationship:
    """A temporal, directional edge (§145, §146)."""

    source_id: str
    target_id: str
    kind: RelationshipKind
    strength: float = 1.0        # 0..1 how strong the coupling is
    confidence: float = 1.0      # 0..1 how sure we are the edge exists
    polarity: int = 1            # +1 same-direction, -1 inverse
    valid_from: datetime | None = None
    valid_to: datetime | None = None
    provenance: str = "seed"

    def active_at(self, when: datetime | None) -> bool:
        """Is this edge valid at ``when``? None => no time bound on that side (§146)."""
        if when is None:
            return True
        before_start = self.valid_from is not None and when < self.valid_from
        after_end = self.valid_to is not None and when > self.valid_to
        return not (before_start or after_end)


@dataclass(frozen=True)
class PropagationHit:
    """A tradable instrument reached by propagation, with the best path to it."""

    instrument: str
    confidence: float            # 0..1 confidence of the best path
    polarity: int                # net +1/-1 direction along that path
    hops: int
    path: tuple[str, ...]        # entity ids traversed (source .. instrument)


class RelationshipGraph:
    """Directed multigraph of entities + temporal edges with propagation (§22)."""

    def __init__(self) -> None:
        self._entities: dict[str, Entity] = {}
        self._out: dict[str, list[Relationship]] = {}

    # ---- construction ----

    def add_entity(self, entity: Entity) -> None:
        self._entities[entity.id] = entity
        self._out.setdefault(entity.id, [])

    def add_relationship(self, rel: Relationship) -> None:
        # Edges may reference entities added later; ensure adjacency buckets exist.
        self._out.setdefault(rel.source_id, []).append(rel)
        self._out.setdefault(rel.target_id, [])

    def entity(self, entity_id: str) -> Entity | None:
        return self._entities.get(entity_id)

    def __len__(self) -> int:
        return len(self._entities)

    # ---- propagation (§22, §143) ----

    def propagate(
        self,
        source_id: str,
        *,
        when: datetime | None = None,
        max_depth: int = 3,
        min_confidence: float = 0.05,
        hop_decay: float = 0.85,
    ) -> tuple[PropagationHit, ...]:
        """BFS from ``source_id`` to reachable tradable INSTRUMENT nodes.

        Confidence along a path = product over hops of (strength × confidence × decay).
        Only edges active at ``when`` are traversed (§146). Paths falling below
        ``min_confidence`` are pruned — a natural horizon on higher-order speculation
        (§143). Returns one hit per instrument, keyed to its best path.
        """
        if source_id not in self._out:
            return ()

        best: dict[str, PropagationHit] = {}
        # queue items: (entity_id, confidence, polarity, hops, path)
        start = (source_id, 1.0, 1, 0, (source_id,))
        q: deque[tuple[str, float, int, int, tuple[str, ...]]] = deque([start])

        while q:
            node_id, conf, pol, hops, path = q.popleft()
            if hops >= max_depth:
                continue
            for rel in self._out.get(node_id, []):
                if not rel.active_at(when):
                    continue
                nxt_conf = conf * rel.strength * rel.confidence * hop_decay
                if nxt_conf < min_confidence:
                    continue
                nxt_pol = pol * (1 if rel.polarity >= 0 else -1)
                nxt_hops = hops + 1
                nxt_path = (*path, rel.target_id)
                target = self._entities.get(rel.target_id)

                # Record instrument hits (best confidence wins).
                if target is not None and target.entity_type is EntityType.INSTRUMENT:
                    inst = target.canonical_instrument or target.id
                    prev = best.get(inst)
                    if prev is None or nxt_conf > prev.confidence:
                        best[inst] = PropagationHit(
                            instrument=inst, confidence=round(nxt_conf, 4),
                            polarity=nxt_pol, hops=nxt_hops, path=nxt_path,
                        )
                # Continue walking regardless (an instrument may also be a waypoint).
                q.append((rel.target_id, nxt_conf, nxt_pol, nxt_hops, nxt_path))

        return tuple(sorted(best.values(), key=lambda h: h.confidence, reverse=True))
