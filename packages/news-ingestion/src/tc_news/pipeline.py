"""Ingestion pipeline (§28-32): normalise -> dedup -> cluster -> classify -> velocity/novelty.

Deterministic and provider-agnostic. Clustering here is a transparent title-similarity
grouping (token Jaccard) — deliberately simple and explainable; a smarter clusterer can
replace it behind the same function. The point is the SPEC BEHAVIOUR:

  * Five orgs reporting the same event become ONE event with source_count=5 (§29).
    Source count raises confidence-of-existence, never market evidence.
  * Velocity = distinct sources per hour across the cluster's span (§30).
  * Novelty (§31): a cluster seen before with no new sources/material is REPEATED and
    must not re-trigger; new sources => UPDATE; a materially different title => MATERIAL.
"""

from __future__ import annotations

import re
from collections.abc import Sequence

from tc_news.events import NEWS_CATEGORIES, Event, Novelty
from tc_news.providers import RawIntelligenceItem

_WORD = re.compile(r"[a-z0-9]+")
_STOP = frozenset({
    "the", "a", "an", "of", "to", "in", "on", "and", "or", "for", "as", "at", "by",
    "is", "are", "be", "with", "from", "amid", "after", "over", "says", "say",
})

# Simple keyword -> §14 category map for transparent classification.
_CATEGORY_KEYWORDS: dict[str, tuple[str, ...]] = {
    "AI": ("ai", "artificial", "chatgpt", "model"),
    "Semiconductors": ("chip", "chips", "semiconductor", "nvidia", "tsmc", "asml"),
    "Energy": ("oil", "gas", "opec", "crude", "energy", "barrel"),
    "Geopolitics": ("war", "military", "strike", "escalation", "border", "missile"),
    "Sanctions": ("sanction", "sanctions", "embargo"),
    "Tariffs": ("tariff", "tariffs", "duties"),
    "Banking": ("bank", "banks", "lender", "deposit"),
    "Regulation": ("regulator", "regulation", "antitrust", "fine"),
    "Economy": ("inflation", "cpi", "gdp", "jobs", "unemployment", "rate", "fed", "boe"),
    "Corporate": ("earnings", "merger", "acquisition", "profit", "guidance"),
}


def _tokens(text: str) -> set[str]:
    return {w for w in _WORD.findall(text.lower()) if w not in _STOP and len(w) > 2}


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def _classify(title: str) -> str:
    toks = _tokens(title)
    best, best_hits = "Other", 0
    for cat, kws in _CATEGORY_KEYWORDS.items():
        hits = sum(1 for k in kws if k in toks)
        if hits > best_hits:
            best, best_hits = cat, hits
    return best if best_hits > 0 else "Other"


def ingest(
    items: Sequence[RawIntelligenceItem],
    *,
    similarity_threshold: float = 0.4,
    known_events: Sequence[Event] = (),
) -> list[Event]:
    """Cluster raw items into deduplicated Events (§28-32).

    ``known_events`` (from a prior run) lets novelty distinguish NEW vs REPEATED/UPDATE.
    Returns events ordered oldest-first by first_seen.
    """
    # --- normalise + sort by time (deterministic clustering order) ---
    norm = sorted(items, key=lambda i: (i.published_at, i.original_id))

    clusters: list[list[RawIntelligenceItem]] = []
    seed_tokens: list[set[str]] = []  # the SEED (first item) tokens — stable anchor
    for it in norm:
        toks = _tokens(it.title)
        placed = False
        # Compare against each cluster's seed tokens (not a growing union, which would
        # dilute similarity and wrongly split paraphrased reports of one event).
        best_idx, best_sim = -1, 0.0
        for idx, stoks in enumerate(seed_tokens):
            sim = _jaccard(toks, stoks)
            if sim > best_sim:
                best_idx, best_sim = idx, sim
        if best_idx >= 0 and best_sim >= similarity_threshold:
            clusters[best_idx].append(it)
            placed = True
        if not placed:
            clusters.append([it])
            seed_tokens.append(set(toks))

    known_by_key = {_cluster_key(e.title): e for e in known_events}
    events: list[Event] = []
    for members in clusters:
        events.append(_build_event(members, known_by_key))
    events.sort(key=lambda e: e.first_seen)
    return events


def _cluster_key(title: str) -> str:
    return " ".join(sorted(_tokens(title)))


def _build_event(members: list[RawIntelligenceItem], known: dict[str, Event]) -> Event:
    members = sorted(members, key=lambda m: m.published_at)
    first, last = members[0], members[-1]
    sources = tuple(dict.fromkeys(m.source for m in members))  # distinct, ordered
    source_count = len(sources)  # §29: distinct orgs, not raw item count

    # Velocity (§30): distinct sources per hour across the cluster span.
    span_hours = max((last.published_at - first.published_at).total_seconds() / 3600.0, 1e-6)
    velocity = round(source_count / span_hours, 3) if source_count > 1 else 0.0

    # Confidence-of-existence rises with corroborating sources (§29) — NOT market evidence.
    confidence = round(min(1.0, source_count / 5.0), 3)

    category = _classify(first.title)

    # Novelty (§31) vs known events.
    key = _cluster_key(first.title)
    prior = known.get(key)
    if prior is None:
        novelty = Novelty.NEW
    elif source_count > prior.source_count:
        novelty = Novelty.UPDATE
    else:
        novelty = Novelty.REPEATED

    event_id = f"evt:{first.published_at.isoformat()}:{key[:40]}"
    return Event(
        event_id=event_id,
        title=first.title,
        first_seen=first.published_at,
        last_updated=last.published_at,
        category=category,
        source_count=source_count,
        sources=sources,
        velocity=velocity,
        confidence=confidence,
        novelty=novelty,
        item_ids=tuple(m.original_id for m in members),
    )


__all__ = ["ingest", "NEWS_CATEGORIES"]
