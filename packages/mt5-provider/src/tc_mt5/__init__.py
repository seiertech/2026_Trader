"""tc_mt5 — MetaTrader 5 provider adapter (§94-96, TC-ADR-004/005, ADR-032).

This is the EDGE adapter: it runs on the dedicated Windows machine where the MT5
terminal lives, and implements the same ``MarketDataProvider`` / ``ExecutionProvider``
contracts the engines already depend on (§96). Nothing in the brain changes when this
is swapped in for the replay provider.

IMPORTANT — platform: the official ``MetaTrader5`` package is a Windows-only binary
that talks to a locally running terminal. This module therefore imports it LAZILY and
guards the import, so:
  * on Linux/CI the module imports fine and every call raises a clear, typed error;
  * on the Windows host it binds to the real terminal.

That keeps the adapter testable here (against a fake bridge) while being genuinely
runnable there. Symbol discovery (§5, §135) maps broker symbols to canonical ids
before anything is marked tradable.
"""

from tc_mt5.provider import (
    Mt5ConnectionError,
    Mt5ExecutionProvider,
    Mt5MarketDataProvider,
    Mt5Settings,
    Mt5Terminal,
    SymbolInfo,
    discover_symbols,
)

__all__ = [
    "Mt5Settings",
    "Mt5Terminal",
    "Mt5ConnectionError",
    "Mt5MarketDataProvider",
    "Mt5ExecutionProvider",
    "SymbolInfo",
    "discover_symbols",
]
