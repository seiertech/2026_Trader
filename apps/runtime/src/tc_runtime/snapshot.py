"""Cockpit snapshot serialiser (§98-§102).

Turns a golden-path run into the JSON shape the Human Control Plane renders: the main
cockpit fields (§98), active/recent decisions, the rejection view (§102, mandatory),
and performance (§86, v1.2). Display-only — the snapshot carries no controls that could
alter state; it is a read of what the runtime decided.

Kept in the runtime (not the dashboard) so the single source of truth for the shape is
Python; the dashboard's TS types mirror it (TC-ADR-031).
"""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path
from typing import Any

from tc_domain.time import utc_now

from tc_runtime.golden_path import GoldenPathResult


def _d(x: Decimal) -> float:
    return float(x)


def build_snapshot(result: GoldenPathResult) -> dict[str, Any]:
    """Serialise a GoldenPathResult into the cockpit JSON shape (§98-102)."""
    m = result.metrics
    recent = [
        {
            "instrument": t.instrument,
            "direction": t.direction,
            "strategy": t.strategy,
            "regime": t.regime,
            "entry": str(t.entry_price),
            "exit": str(t.exit_price),
            "exit_reason": t.exit_reason,
            "r": _d(t.r_multiple),
            "net_pnl": _d(t.net_pnl),
            "evidence_pack_id": t.evidence_pack_id,
        }
        for t in result.trades[-10:]  # RECENT CLOSED TRADES (§98)
    ]

    return {
        "generated_at": utc_now().isoformat(),
        # --- main cockpit (§98) ---
        "mode": result.mode.value,
        "system_health": "HEALTHY",  # Phase-0 shell; live health when wired
        "reference_unit_gbp": _d(result.starting_balance),
        "return_target": None,  # §0/§75 — none, ever
        "shadow_equity": _d(result.ending_balance),
        "realized_pnl": _d(m.net_pnl),
        "total_return_pct": _d(
            (result.ending_balance - result.starting_balance)
            / result.starting_balance * Decimal(100)
        ),
        "max_drawdown": _d(m.max_drawdown),
        "kill_switch": False,
        # --- opportunity / decision funnel (§100) + rejection view (§102) ---
        "opportunities": result.opportunities,
        "decisions": result.decisions,
        "rejected": result.rejected,
        # --- performance (§86, v1.2) ---
        "performance": {
            "trades": m.trades,
            "wins": m.wins,
            "losses": m.losses,
            "win_rate": _d(m.win_rate),
            "profit_factor": None if m.profit_factor is None else _d(m.profit_factor),
            "expectancy_r": _d(m.expectancy_r),
            "expectancy_cash": _d(m.expectancy_cash),
            "avg_mfe_r": _d(m.avg_mfe_r),
            "avg_mae_r": _d(m.avg_mae_r),
            "total_costs": _d(m.total_costs),
        },
        "recent_trades": recent,
    }


def write_snapshot(result: GoldenPathResult, out_path: str | Path) -> Path:
    """Write the snapshot JSON to ``out_path`` (creates parent dirs)."""
    p = Path(out_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(build_snapshot(result), indent=2), encoding="utf-8")
    return p
