"""Theme objects + lifecycle state machine (§147, TC-ADR-029).

Strength model (§147): a theme's strength (0..100) blends
  * independent evidence   — count of distinct corroborating sources (breadth)
  * persistence            — how long it has been observed (age)
  * velocity               — how fast corroboration is arriving
  * market confirmation    — whether affected instruments actually moved as implied

Lifecycle transitions are a deterministic function of strength + velocity + age:
  EMERGING     — just appeared, low breadth
  ACCELERATING — strength rising fast (high velocity)
  ESTABLISHED  — high strength, broad, confirmed
  DECELERATING — strength falling / velocity negative
  DORMANT      — low velocity for a while but not resolved
  RESOLVED     — explicitly closed out

The engine never fabricates strength: with no evidence a theme stays EMERGING at low
strength. Themes resolve to instruments via the injected relationship graph (§22).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from tc_domain.enums import ThemeLifecycle
from tc_domain.time import utc_now


@dataclass(frozen=True)
class ThemeEvidence:
    """One corroborating observation for a theme (§147 independent evidence)."""

    source: str            # distinct source id (dedup by this for breadth)
    at: datetime           # when observed (UTC)
    weight: float = 1.0    # 0..1 strength of this corroboration
    market_confirmed: bool = False  # did the market move as the theme implies?


@dataclass
class Theme:
    """A durable theme with lifecycle (§147)."""

    id: str
    name: str
    lifecycle: ThemeLifecycle = ThemeLifecycle.EMERGING
    strength: float = 0.0
    first_seen: datetime | None = None
    last_updated: datetime | None = None
    evidence: list[ThemeEvidence] = field(default_factory=list)
    resolved: bool = False

    @property
    def independent_sources(self) -> int:
        return len({e.source for e in self.evidence})

    @property
    def confirmed_sources(self) -> int:
        return len({e.source for e in self.evidence if e.market_confirmed})


# --- Tunable lifecycle thresholds (research params; calibrate in Shadow, §147) ---
STRENGTH_ESTABLISHED = 65.0
STRENGTH_EMERGING_MAX = 25.0
VELOCITY_ACCELERATING = 1.5   # sources/day above this => accelerating
VELOCITY_DORMANT = 0.05       # below this => decelerating/dormant


class ThemeEngine:
    """Manages a set of themes and their lifecycle. Optional graph for instrument links."""

    def __init__(self, graph: object | None = None) -> None:
        self._themes: dict[str, Theme] = {}
        self._graph = graph  # RelationshipGraph or None

    def register(self, theme_id: str, name: str) -> Theme:
        t = self._themes.get(theme_id)
        if t is None:
            t = Theme(id=theme_id, name=name)
            self._themes[theme_id] = t
        return t

    def get(self, theme_id: str) -> Theme | None:
        return self._themes.get(theme_id)

    def all(self) -> tuple[Theme, ...]:
        return tuple(self._themes.values())

    def observe(
        self, theme_id: str, evidence: ThemeEvidence, *, name: str | None = None
    ) -> Theme:
        """Add evidence to a theme and recompute its strength + lifecycle."""
        t = self.register(theme_id, name or theme_id)
        if t.first_seen is None:
            t.first_seen = evidence.at
        t.last_updated = evidence.at
        t.evidence.append(evidence)
        self._recompute(t, now=evidence.at)
        return t

    def resolve(self, theme_id: str, when: datetime | None = None) -> Theme | None:
        t = self._themes.get(theme_id)
        if t is None:
            return None
        t.resolved = True
        t.lifecycle = ThemeLifecycle.RESOLVED
        t.last_updated = when or utc_now()
        return t

    def affected_instruments(self, theme_id: str, when: datetime | None = None):
        """Instruments this theme could affect, via graph propagation (§22)."""
        if self._graph is None or not hasattr(self._graph, "propagate"):
            return ()
        return self._graph.propagate(theme_id, when=when)

    # ---- internals ----

    def _recompute(self, t: Theme, *, now: datetime) -> None:
        if t.resolved:
            t.lifecycle = ThemeLifecycle.RESOLVED
            return

        breadth = t.independent_sources
        confirmed = t.confirmed_sources
        # Mean evidence weight (0..1).
        mean_w = (sum(e.weight for e in t.evidence) / len(t.evidence)) if t.evidence else 0.0

        # Velocity: sources per day over the observed window.
        velocity = _velocity(t, now)

        # Strength (0..100): breadth (saturating) × weight, boosted by confirmation.
        breadth_factor = min(1.0, breadth / 4.0)
        confirm_boost = 1.0 + 0.5 * min(1.0, confirmed / 3.0)
        t.strength = round(min(100.0, 100.0 * breadth_factor * mean_w * confirm_boost), 2)

        t.lifecycle = _lifecycle(t.strength, velocity)


def _velocity(t: Theme, now: datetime) -> float:
    if t.first_seen is None or not t.evidence:
        return 0.0
    span_days = max((now - t.first_seen).total_seconds() / 86400.0, 1e-6)
    if span_days < 1.0:
        # Fresh burst within a day reads as high velocity.
        return float(len(t.evidence))
    return len(t.evidence) / span_days


def _lifecycle(strength: float, velocity: float) -> ThemeLifecycle:
    if strength >= STRENGTH_ESTABLISHED:
        return ThemeLifecycle.ESTABLISHED
    if velocity >= VELOCITY_ACCELERATING and strength > STRENGTH_EMERGING_MAX:
        return ThemeLifecycle.ACCELERATING
    if strength <= STRENGTH_EMERGING_MAX:
        return ThemeLifecycle.EMERGING
    if velocity <= VELOCITY_DORMANT:
        return ThemeLifecycle.DORMANT
    return ThemeLifecycle.DECELERATING
