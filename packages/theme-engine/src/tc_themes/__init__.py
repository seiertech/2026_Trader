"""tc_themes — the Global Theme Engine (§20, §147, TC-ADR-029).

Themes are DURABLE objects with a lifecycle (§147, TC-ADR-029) — not transient tags.
A theme's strength is a function of independent evidence, persistence, velocity and
market confirmation (§147). Themes participate in the relationship graph (they are
THEME entities), so a theme resolves to potentially affected tradable instruments via
graph propagation (§21 THEME→INSTRUMENT, §22).

Deterministic: lifecycle transitions are driven by observable inputs, not opinion.
"""

from tc_themes.engine import Theme, ThemeEngine, ThemeEvidence
from tc_themes.seed import load_themes_from_config

__all__ = ["Theme", "ThemeEvidence", "ThemeEngine", "load_themes_from_config"]
