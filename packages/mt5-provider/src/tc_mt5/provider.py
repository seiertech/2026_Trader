"""MT5 adapter: terminal binding, symbol discovery, market-data + execution providers.

Design notes (why it looks like this):

  * ``Mt5Terminal`` is a thin seam over the ``MetaTrader5`` module. Tests inject a fake
    terminal; on the Windows host the real module is bound. This is what makes the
    adapter developable on Linux (ADR-032) without pretending MT5 runs here.
  * Every method that would touch the broker raises :class:`Mt5ConnectionError` when no
    terminal is bound — FAIL CLOSED (§104), never silently return empty/zero data that
    downstream code could mistake for real market state.
  * Canonical ids stay decoupled from broker symbols (§5, §135). ``discover_symbols``
    resolves broker symbol + contract size + tick size + volume limits BEFORE anything
    is considered tradable.
  * The execution side validates before submitting (§94 "order checking") and refuses
    to act unless the caller is in a live-capable mode — it holds no opinion on risk,
    which remains the Risk Engine's job (§73, TC-ADR-012).
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from tc_domain.enums import OperatingMode, Timeframe
from tc_domain.market import AccountSnapshot, Bar, Quote
from tc_domain.policy import assert_not_crypto
from tc_domain.time import ensure_utc


class Mt5ConnectionError(RuntimeError):
    """Raised when no MT5 terminal is bound/reachable. Fail closed (§104)."""


@dataclass(frozen=True)
class Mt5Settings:
    """Connection settings. Secrets come from env on the Windows host (§128-129)."""

    login: int | None = None
    password: str | None = None
    server: str | None = None
    # When the terminal runs on a separate machine, a bridge fronts it (ADR-032).
    bridge_host: str = "127.0.0.1"
    bridge_port: int = 18812
    timeout_ms: int = 10_000


@dataclass(frozen=True)
class SymbolInfo:
    """Broker symbol metadata required before an instrument may be traded (§5, §135)."""

    broker_symbol: str
    canonical_id: str
    contract_size: Decimal
    tick_size: Decimal
    volume_min: Decimal
    volume_step: Decimal
    trade_allowed: bool = False


# MT5 timeframe constants, referenced by name so we never import the module at
# definition time. The real values are read off the terminal when bound.
_TF_ATTR: dict[Timeframe, str] = {
    Timeframe.M1: "TIMEFRAME_M1",
    Timeframe.M5: "TIMEFRAME_M5",
    Timeframe.M15: "TIMEFRAME_M15",
    Timeframe.H1: "TIMEFRAME_H1",
    Timeframe.H4: "TIMEFRAME_H4",
    Timeframe.D1: "TIMEFRAME_D1",
}


class Mt5Terminal:
    """Seam over the ``MetaTrader5`` module (or a test double).

    ``bind_real()`` imports the Windows-only package on demand. Anything else stays
    injectable so the adapter is developable and testable off-Windows.
    """

    def __init__(self, module: Any | None = None) -> None:
        self._mod = module
        self._connected = False

    # ---- binding ----

    @classmethod
    def bind_real(cls) -> Mt5Terminal:
        """Import the real MetaTrader5 package (Windows only)."""
        try:
            import MetaTrader5 as mt5  # noqa: N813  (vendor module name)
        except Exception as exc:  # pragma: no cover - not importable off-Windows
            raise Mt5ConnectionError(
                "MetaTrader5 is a Windows-only package and is not importable here. "
                "Run this adapter on the dedicated Windows host (ADR-032)."
            ) from exc
        return cls(mt5)

    @property
    def bound(self) -> bool:
        return self._mod is not None

    @property
    def connected(self) -> bool:
        return self._connected

    def _require(self) -> Any:
        if self._mod is None:
            raise Mt5ConnectionError(
                "no MT5 terminal bound — this adapter must run on the Windows host "
                "with the Eightcap terminal running (ADR-032)."
            )
        return self._mod

    # ---- lifecycle ----

    def connect(self, settings: Mt5Settings) -> bool:
        mod = self._require()
        kwargs: dict[str, Any] = {}
        if settings.login is not None:
            kwargs["login"] = settings.login
        if settings.password:
            kwargs["password"] = settings.password
        if settings.server:
            kwargs["server"] = settings.server
        ok = bool(mod.initialize(**kwargs)) if kwargs else bool(mod.initialize())
        self._connected = ok
        if not ok:
            raise Mt5ConnectionError(f"MT5 initialize() failed: {self.last_error()}")
        return ok

    def shutdown(self) -> None:
        if self._mod is not None and self._connected:
            self._mod.shutdown()
        self._connected = False

    def last_error(self) -> Any:
        mod = self._mod
        return mod.last_error() if mod is not None and hasattr(mod, "last_error") else None

    # ---- reads ----

    def account_info(self) -> Any:
        return self._require().account_info()

    def symbols_get(self) -> Sequence[Any]:
        return self._require().symbols_get() or ()

    def symbol_info(self, broker_symbol: str) -> Any:
        return self._require().symbol_info(broker_symbol)

    def symbol_info_tick(self, broker_symbol: str) -> Any:
        return self._require().symbol_info_tick(broker_symbol)

    def copy_rates_from_pos(self, broker_symbol: str, timeframe: Any, start: int, count: int) -> Any:
        return self._require().copy_rates_from_pos(broker_symbol, timeframe, start, count)

    def positions_get(self) -> Sequence[Any]:
        return self._require().positions_get() or ()

    def timeframe_constant(self, tf: Timeframe) -> Any:
        mod = self._require()
        return getattr(mod, _TF_ATTR[tf])

    # ---- writes ----

    def order_check(self, request: dict[str, Any]) -> Any:
        return self._require().order_check(request)

    def order_send(self, request: dict[str, Any]) -> Any:
        return self._require().order_send(request)


def discover_symbols(
    terminal: Mt5Terminal,
    canonical_map: dict[str, str],
) -> dict[str, SymbolInfo]:
    """Resolve broker symbols to canonical ids with their trading constraints.

    ``canonical_map`` maps canonical id -> broker symbol (config-driven; §5/§135).
    Crypto is refused outright, whatever the broker offers (§7, TC-ADR-006).
    Returns canonical_id -> SymbolInfo. Symbols the terminal does not know are omitted
    rather than guessed.
    """
    out: dict[str, SymbolInfo] = {}
    for canonical, broker in canonical_map.items():
        assert_not_crypto(canonical)
        assert_not_crypto(broker)
        info = terminal.symbol_info(broker)
        if info is None:
            continue
        out[canonical] = SymbolInfo(
            broker_symbol=broker,
            canonical_id=canonical,
            contract_size=Decimal(str(getattr(info, "trade_contract_size", 1) or 1)),
            tick_size=Decimal(str(getattr(info, "trade_tick_size", 0) or 0)),
            volume_min=Decimal(str(getattr(info, "volume_min", 0) or 0)),
            volume_step=Decimal(str(getattr(info, "volume_step", 0) or 0)),
            trade_allowed=bool(getattr(info, "visible", False)),
        )
    return out


class Mt5MarketDataProvider:
    """Live market data from MT5 (§23, §94, §109 Phase 1). Implements MarketDataProvider."""

    def __init__(
        self,
        terminal: Mt5Terminal,
        symbols: dict[str, SymbolInfo],
        *,
        account_currency: str = "GBP",
    ) -> None:
        self._t = terminal
        self._symbols = symbols
        self._currency = account_currency

    def _broker(self, canonical: str) -> str:
        info = self._symbols.get(canonical)
        if info is None:
            raise Mt5ConnectionError(
                f"instrument '{canonical}' has not been discovered on this terminal; "
                "run discover_symbols() first (§5/§135)."
            )
        return info.broker_symbol

    # ---- MarketDataProvider protocol ----

    def symbols(self) -> tuple[str, ...]:
        return tuple(self._symbols)

    def account(self) -> AccountSnapshot:
        info = self._t.account_info()
        if info is None:
            raise Mt5ConnectionError("MT5 account_info() returned None")
        return AccountSnapshot(
            time=datetime.now(UTC),
            currency=getattr(info, "currency", self._currency),
            balance=Decimal(str(getattr(info, "balance", 0))),
            equity=Decimal(str(getattr(info, "equity", 0))),
            margin_used=Decimal(str(getattr(info, "margin", 0) or 0)),
        )

    def quote(self, instrument: str) -> Quote | None:
        tick = self._t.symbol_info_tick(self._broker(instrument))
        if tick is None:
            return None
        return Quote(
            instrument=instrument,
            time=_tick_time(tick),
            bid=Decimal(str(tick.bid)),
            ask=Decimal(str(tick.ask)),
        )

    def bars(
        self,
        instrument: str,
        timeframe: Timeframe,
        *,
        since: datetime | None = None,
        limit: int | None = None,
    ) -> tuple[Bar, ...]:
        """Closed bars, oldest→newest.

        The most recent MT5 rate is the *forming* bar; it is dropped so callers only
        ever see CLOSED bars — preserving the same no-look-ahead contract the replay
        provider guarantees (§126).
        """
        count = (limit or 500) + 1  # +1 so we can discard the forming bar
        rates = self._t.copy_rates_from_pos(
            self._broker(instrument), self._t.timeframe_constant(timeframe), 0, count
        )
        if rates is None:
            return ()
        rows = list(rates)
        if rows:
            rows = rows[:-1]  # drop the in-progress bar
        bars = [_row_to_bar(instrument, timeframe, r) for r in rows]
        if since is not None:
            since = ensure_utc(since)
            bars = [b for b in bars if b.open_time >= since]
        if limit is not None:
            bars = bars[-limit:]
        return tuple(bars)

    def positions(self) -> tuple[Any, ...]:
        return tuple(self._t.positions_get())


class Mt5ExecutionProvider:
    """Order/position side (§94, §96). Refuses to act outside live-capable modes.

    It validates before submitting (§94 order checking) and holds NO risk opinion —
    sizing/limits are the Risk Engine's job (§73, TC-ADR-012). In SHADOW it raises,
    because SHADOW places no broker orders (§79).
    """

    def __init__(
        self,
        terminal: Mt5Terminal,
        symbols: dict[str, SymbolInfo],
        *,
        mode: OperatingMode = OperatingMode.SHADOW,
    ) -> None:
        self._t = terminal
        self._symbols = symbols
        self._mode = mode

    def _require_live(self) -> None:
        if self._mode in (OperatingMode.OFF, OperatingMode.SHADOW):
            raise Mt5ConnectionError(
                f"mode is {self._mode.value}: no broker orders are permitted "
                "(§79 SHADOW places no orders). Live execution requires an explicit "
                "approved build unit (Part XXXI)."
            )

    def get_account(self) -> AccountSnapshot:
        return Mt5MarketDataProvider(self._t, self._symbols).account()

    def get_positions(self) -> tuple[Any, ...]:
        return tuple(self._t.positions_get())

    def validate_order(self, order: dict[str, Any]) -> Any:
        """Pre-trade check via MT5 order_check (§94). Allowed in any mode — read-only."""
        return self._t.order_check(dict(order))

    def submit_order(self, order: dict[str, Any]) -> Any:
        self._require_live()
        checked = self._t.order_check(dict(order))
        retcode = getattr(checked, "retcode", None)
        if checked is None or (retcode is not None and int(retcode) not in _OK_CHECK_CODES):
            raise Mt5ConnectionError(f"order_check rejected the request: {checked}")
        return self._t.order_send(dict(order))

    def modify_order(self, order_id: str, changes: dict[str, Any]) -> Any:
        self._require_live()
        req = {"order": order_id, **changes}
        return self._t.order_send(req)

    def close_position(self, position_id: str) -> Any:
        self._require_live()
        return self._t.order_send({"position": position_id, "action": "CLOSE"})


# MT5 returns 0 for a valid check in most builds; treat these as acceptable.
_OK_CHECK_CODES = frozenset({0})


def _tick_time(tick: Any) -> datetime:
    raw = getattr(tick, "time", None)
    if raw is None:
        return datetime.now(UTC)
    return datetime.fromtimestamp(int(raw), UTC)


def _row_to_bar(instrument: str, timeframe: Timeframe, row: Any) -> Bar:
    """Convert an MT5 rate row (tuple-like or mapping) to a canonical Bar."""
    def get(key: str, idx: int) -> Any:
        if hasattr(row, key):
            return getattr(row, key)
        try:
            return row[key]  # numpy structured / dict
        except Exception:
            return row[idx]  # plain tuple

    return Bar(
        instrument=instrument,
        timeframe=timeframe,
        open_time=datetime.fromtimestamp(int(get("time", 0)), UTC),
        open=Decimal(str(get("open", 1))),
        high=Decimal(str(get("high", 2))),
        low=Decimal(str(get("low", 3))),
        close=Decimal(str(get("close", 4))),
        volume=Decimal(str(get("tick_volume", 5) or 0)),
    )
