"""Load the theme catalogue from config (§20 config-driven)."""

from __future__ import annotations

from pathlib import Path

import yaml

from tc_themes.engine import ThemeEngine


def load_themes_from_config(
    config_path: str | Path = "config/themes.yaml",
    *,
    graph: object | None = None,
) -> ThemeEngine:
    """Build a ThemeEngine pre-registered with the catalogue themes.

    ``graph`` (a RelationshipGraph) enables theme->instrument resolution (§22).
    """
    engine = ThemeEngine(graph=graph)
    p = Path(config_path)
    with p.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    for t in data.get("themes", []):
        engine.register(t["id"], t.get("name", t["id"]))
    return engine
