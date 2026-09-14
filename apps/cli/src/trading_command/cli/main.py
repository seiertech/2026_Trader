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


def cmd_golden_path(_: argparse.Namespace) -> int:
    # Lazy import so the CLI's read-only commands don't pull the runtime/engines.
    sys.path.insert(0, str(_ROOT / "packages" / "quant-engine" / "src"))
    sys.path.insert(0, str(_ROOT / "packages" / "market-data" / "src"))
    sys.path.insert(0, str(_ROOT / "packages" / "shadow-engine" / "src"))
    sys.path.insert(0, str(_ROOT / "apps" / "runtime" / "src"))
    from tc_runtime.golden_path import format_report, run_golden_path

    sample = _ROOT / "data" / "reference" / "XAUUSD_1m_sample.csv"
    if not sample.exists():
        print(f"sample data not found: {sample}", file=sys.stderr)
        return 2
    print(format_report(run_golden_path(sample)))
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
    sub.add_parser(
        "golden-path", help="run the XAUUSD Shadow golden-path demo on sample data"
    ).set_defaults(fn=cmd_golden_path)
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
