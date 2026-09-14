"""Load market-leader baskets from config (§19 config-driven)."""

from __future__ import annotations

from pathlib import Path

import yaml

from tc_leaders.baskets import Basket


def load_baskets_from_config(
    config_path: str | Path = "config/companies.yaml",
) -> dict[str, Basket]:
    """Return baskets keyed by id."""
    p = Path(config_path)
    with p.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    out: dict[str, Basket] = {}
    for b in data.get("baskets", []):
        out[b["id"]] = Basket(
            id=b["id"],
            name=b.get("name", b["id"]),
            sector=b["sector"],
            members=tuple(b.get("members", [])),
        )
    return out
