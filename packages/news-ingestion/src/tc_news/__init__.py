"""tc_news — News & Event intelligence ingestion (Part VI, §24, §27, §28-32).

The pipeline (§28): SOURCE -> INGEST -> NORMALISE -> DEDUPLICATE -> CLUSTER ->
CLASSIFY -> ENTITY/THEME extraction -> RELEVANCE/SEVERITY/NOVELTY/VELOCITY.

Providers are ADAPTERS, never core dependencies (§24, §27, TC-ADR-010): no business
logic depends on a specific news provider. The offline FixtureProvider ships for
deterministic tests + demos; real RSS/GDELT adapters implement the same protocol and
drop in without touching the pipeline.

Key spec rules enforced here:
  * Deduplication (§29): five orgs reporting one event => ONE event, sourceCount=5;
    source count strengthens confidence-of-existence, NOT market evidence.
  * Velocity (§30): the rate at which sources corroborate.
  * Novelty (§31): NEW / REPEATED / UPDATE / MATERIAL_UPDATE — a repeated headline
    does not re-trigger analysis.
"""

from tc_news.events import Event, Novelty
from tc_news.pipeline import ingest
from tc_news.providers import (
    FixtureProvider,
    IntelligenceProvider,
    RawIntelligenceItem,
)

__all__ = [
    "IntelligenceProvider",
    "RawIntelligenceItem",
    "FixtureProvider",
    "ingest",
    "Event",
    "Novelty",
]
