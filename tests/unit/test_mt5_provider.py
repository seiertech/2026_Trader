"""MT5 adapter (§94-96, ADR-032): contract conformance, fail-closed, no-look-ahead.

Tested against a FAKE terminal so the adapter is verifiable off-Windows. The real
terminal binding is exercised on the Windows host.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from tc_domain.enums import OperatingMode, Timeframe
from tc_market_data.contracts import MarketDataProvider
from tc_mt5 import (
    Mt5ConnectionError,
    Mt5ExecutionProvider,
    Mt5MarketDataProvider,
    Mt5Settings,
    Mt5Terminal,
    discover_symbols,
)
from tc_mt5.provider import SymbolInfo


class _Info:
    currency = "GBP"
    balance = 250.0
    equity = 251.5
    margin = 10.0


class _SymInfo:
    trade_contract_size = 100
    trade_tick_size = 0.01
    volume_min = 0.01
    volume_step = 0.01
    visible = True


class _Tick:
    time = int(datetime(2026, 1, 5, 12, 0, tzinfo=UTC).timestamp())
    bid = 2650.10
    ask = 2650.40


class _Checked:
    retcode = 0


class FakeMt5:
    """Minimal stand-in for the MetaTrader5 module."""

    TIMEFRAME_M1 = 1
    TIMEFRAME_M5 = 5
    TIMEFRAME_M15 = 15
    TIMEFRAME_H1 = 60
    TIMEFRAME_H4 = 240
    TIMEFRAME_D1 = 1440

    def __init__(self) -> None:
        self.sent: list[dict] = []

    def initialize(self, **kw) -> bool:
        return True

    def shutdown(self) -> None:
        pass

    def last_error(self):
        return (0, "ok")

    def account_info(self):
        return _Info()

    def symbol_info(self, s):
        return _SymInfo() if s in ("XAUUSD", "GOLD") else None

    def symbol_info_tick(self, s):
        return _Tick()

    def copy_rates_from_pos(self, s, tf, start, count):
        base = int(datetime(2026, 1, 5, 10, 0, tzinfo=UTC).timestamp())
        # 4 rows; the LAST is the still-forming bar and must be dropped by the adapter.
        return [
            (base + i * 60, 2650 + i, 2651 + i, 2649 + i, 2650.5 + i, 100 + i)
            for i in range(4)
        ]

    def positions_get(self):
        return ()

    def order_check(self, req):
        return _Checked()

    def order_send(self, req):
        self.sent.append(req)
        return {"retcode": 0, "order": 1}


def _provider() -> tuple[Mt5MarketDataProvider, FakeMt5]:
    fake = FakeMt5()
    t = Mt5Terminal(fake)
    t.connect(Mt5Settings(login=1, password="x", server="Eightcap-Demo"))
    syms = discover_symbols(t, {"XAUUSD": "XAUUSD"})
    return Mt5MarketDataProvider(t, syms), fake


# --- contract conformance ---

def test_satisfies_marketdataprovider_contract() -> None:
    p, _ = _provider()
    assert isinstance(p, MarketDataProvider)  # same seam as the replay provider (§96)


def test_symbol_discovery_resolves_metadata() -> None:
    t = Mt5Terminal(FakeMt5())
    syms = discover_symbols(t, {"XAUUSD": "XAUUSD"})
    assert "XAUUSD" in syms
    info: SymbolInfo = syms["XAUUSD"]
    assert info.contract_size == Decimal("100")
    assert info.volume_min == Decimal("0.01")


def test_unknown_broker_symbol_omitted_not_guessed() -> None:
    t = Mt5Terminal(FakeMt5())
    syms = discover_symbols(t, {"NAS100": "NOPE"})
    assert syms == {}  # omitted, never fabricated


def test_crypto_refused_even_if_broker_offers_it() -> None:
    t = Mt5Terminal(FakeMt5())
    with pytest.raises(Exception) as exc:  # PolicyViolation (§7, TC-ADR-006)
        discover_symbols(t, {"BTCUSD": "BTCUSD"})
    assert "crypto" in str(exc.value).lower()


# --- reads ---

def test_account_snapshot() -> None:
    p, _ = _provider()
    a = p.account()
    assert a.currency == "GBP"
    assert a.balance == Decimal("250.0")


def test_quote_maps_bid_ask() -> None:
    p, _ = _provider()
    q = p.quote("XAUUSD")
    assert q is not None
    assert q.bid == Decimal("2650.10") and q.ask == Decimal("2650.40")
    assert q.spread > 0


def test_bars_drop_the_forming_bar() -> None:
    """§126: callers must only ever see CLOSED bars."""
    p, _ = _provider()
    bars = p.bars("XAUUSD", Timeframe.M1)
    assert len(bars) == 3  # 4 rates - 1 forming
    assert bars[0].open_time < bars[-1].open_time
    assert all(b.timeframe is Timeframe.M1 for b in bars)


def test_undiscovered_instrument_fails_closed() -> None:
    p, _ = _provider()
    with pytest.raises(Mt5ConnectionError):
        p.quote("EURUSD")  # never discovered → refuse, don't return None silently


# --- fail closed when unbound ---

def test_unbound_terminal_raises() -> None:
    t = Mt5Terminal(None)
    with pytest.raises(Mt5ConnectionError):
        t.account_info()


# --- execution guards ---

def test_shadow_mode_refuses_to_submit_orders() -> None:
    fake = FakeMt5()
    t = Mt5Terminal(fake)
    ex = Mt5ExecutionProvider(t, {"XAUUSD": SymbolInfo("XAUUSD", "XAUUSD", Decimal(100),
                              Decimal("0.01"), Decimal("0.01"), Decimal("0.01"), True)},
                              mode=OperatingMode.SHADOW)
    with pytest.raises(Mt5ConnectionError):
        ex.submit_order({"symbol": "XAUUSD", "volume": 0.1})
    assert fake.sent == []  # §79: SHADOW places NO broker orders


def test_validate_order_allowed_in_shadow() -> None:
    # Pre-trade checking is read-only, so it is permitted in any mode (§94).
    t = Mt5Terminal(FakeMt5())
    ex = Mt5ExecutionProvider(t, {}, mode=OperatingMode.SHADOW)
    assert ex.validate_order({"symbol": "XAUUSD"}) is not None


def test_live_limited_can_submit_after_check() -> None:
    fake = FakeMt5()
    ex = Mt5ExecutionProvider(Mt5Terminal(fake), {}, mode=OperatingMode.LIVE_LIMITED)
    ex.submit_order({"symbol": "XAUUSD", "volume": 0.01})
    assert len(fake.sent) == 1  # checked, then sent
