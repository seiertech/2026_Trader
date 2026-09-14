"""Trading Command CLI / operator console (TC-SPEC-001 v1.2 Control Plane, TC-ADR-039).

A lightweight engineering/operational interface. Phase 0 implements read-only,
safe commands: ``status``, ``health``, ``markets``, and ``config``. Dangerous/live
commands (pause, resume-shadow, etc.) are stubbed and MUST route through deterministic
policy controls before doing anything — they never bypass them (v1.2).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Phase 0: resolve sibling packages without an install step. A proper editable
# install replaces this once the workspace build is wired.
_ROOT = Path(__file__).resolve().parents[5]
for _pkg in ("domain", "config", "observability", "database"):
    sys.path.insert(0, str(_ROOT / "packages" / _pkg / "src"))

from tc_config import ConfigError, load_config  # noqa: E402


def _config_dir() -> Path:
    return _ROOT / "config"


def cmd_status(_: argparse.Namespace) -> int:
    try:
        cfg = load_config(_config_dir())
    except ConfigError as exc:
        print(f"CONFIG ERROR (fail closed): {exc}", file=sys.stderr)
        return 2
    print(f"mode                : {cfg.runtime.mode.value}")
    print(f"reference unit      : £{cfg.runtime.reference_unit_gbp:g} (risk/R only)")
    print(f"return target       : {cfg.runtime.return_target}  (none — Prime Directive §0)")
    print(f"market data provider: {cfg.runtime.market_data_provider}")
    print(f"execution provider  : {cfg.runtime.execution_provider}")
    print(f"golden path         : {cfg.runtime.golden_path_instrument}")
    return 0


def cmd_health(_: argparse.Namespace) -> int:
    # Phase 0: no live components. Report the static shell view honestly.
    print("system health: HEALTHY (Phase 0 shell — no live dependencies)")
    print("  MT5                : DEGRADED  (replay provider; no Windows host yet)")
    print("  Eightcap           : DEGRADED  (not connected in SHADOW)")
    print("  AI                 : HEALTHY   (deterministic-only until Phase 9)")
    print("  News/Intelligence  : HEALTHY   (not yet ingesting)")
    return 0


def cmd_markets(_: argparse.Namespace) -> int:
    try:
        cfg = load_config(_config_dir())
    except ConfigError as exc:
        print(f"CONFIG ERROR (fail closed): {exc}", file=sys.stderr)
        return 2
    print(f"{'CANONICAL':10} {'CLASS':10} PERMISSION")
    for inst in cfg.instruments:
        print(f"{inst.canonical_id:10} {inst.asset_class.value:10} {inst.permission.value}")
    return 0


def cmd_golden_path(args: argparse.Namespace) -> int:
    # Lazy import so the CLI's read-only commands don't pull the runtime/engines.
    for pkg in ("quant-engine", "market-data", "shadow-engine", "risk-engine",
                "database", "learning-engine", "decision-engine", "config"):
        sys.path.insert(0, str(_ROOT / "packages" / pkg / "src"))
    sys.path.insert(0, str(_ROOT / "strategies" / "src"))
    sys.path.insert(0, str(_ROOT / "apps" / "runtime" / "src"))
    from tc_runtime.golden_path import format_report, run_golden_path

    sample = _ROOT / "data" / "reference" / "XAUUSD_1m_sample.csv"
    if not sample.exists():
        print(f"sample data not found: {sample}", file=sys.stderr)
        return 2

    store = None
    persist_path = getattr(args, "persist", None)
    if persist_path:
        from tc_database import open_duckdb_store

        store = open_duckdb_store(persist_path)

    result = run_golden_path(sample, store=store)
    print(format_report(result))
    if store is not None:
        print(f"\n  persisted {len(result.trades)} trade(s) to {persist_path} "
              f"(store now holds {store.count()} experience record(s))")
        store.close()
    return 0


def cmd_attribution(args: argparse.Namespace) -> int:
    for pkg in ("database", "shadow-engine", "risk-engine", "learning-engine"):
        sys.path.insert(0, str(_ROOT / "packages" / pkg / "src"))
    from pathlib import Path as _Path

    from tc_database import load_trades, open_duckdb_store
    from tc_learning.attribution import attribute, format_attribution

    if not _Path(args.store).exists():
        print(f"store not found: {args.store}", file=sys.stderr)
        return 2
    store = open_duckdb_store(args.store)
    trades = load_trades(store)
    dims = tuple(d.strip() for d in args.by.split(",") if d.strip())
    print(f"── ATTRIBUTION · {args.store} · by {' / '.join(dims)} ──")
    print(f"  {len(trades)} persisted trade(s)\n")
    print(format_attribution(attribute(trades, dims)))
    store.close()
    return 0


def _stub(name: str) -> int:
    print(f"'{name}' is not implemented in Phase 0. It will route through "
          f"deterministic policy controls when built (never bypassing them).")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="tc", description="Trading Command operator console")
    sub = p.add_subparsers(dest="command", required=True)
    sub.add_parser("status", help="operating mode & runtime config").set_defaults(
        fn=cmd_status
    )
    sub.add_parser("health", help="system/dependency health").set_defaults(
        fn=cmd_health
    )
    sub.add_parser("markets", help="canonical instruments & permissions").set_defaults(
        fn=cmd_markets
    )
    gp = sub.add_parser(
        "golden-path", help="run the XAUUSD Shadow golden-path demo on sample data"
    )
    gp.add_argument(
        "--persist", metavar="PATH.duckdb", default=None,
        help="persist simulated trades to a DuckDB experience store at PATH",
    )
    gp.set_defaults(fn=cmd_golden_path)
    att = sub.add_parser(
        "attribution", help="per-cell performance attribution over a persisted store"
    )
    att.add_argument("store", metavar="PATH.duckdb", help="DuckDB experience store to read")
    att.add_argument(
        "--by", default="instrument,direction",
        help="comma-separated attribution dimensions (default: instrument,direction)",
    )
    att.set_defaults(fn=cmd_attribution)
    stubbed = (
        "opportunities", "positions", "performance", "risk",
        "events", "pause", "resume-shadow",
    )
    for name in stubbed:
        sub.add_parser(name, help=f"{name} (not implemented in Phase 0)").set_defaults(
            fn=lambda _a, _n=name: _stub(_n)
        )
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return int(args.fn(args))


if __name__ == "__main__":
    raise SystemExit(main())
