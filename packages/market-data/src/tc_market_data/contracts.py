"""Provider contracts (§96). Language-neutral spec interfaces, expressed as Python
Protocols (TC-ADR-031).

    interface ExecutionProvider {
      getAccount(); getPositions(); validateOrder();
      submitOrder(); modifyOrder(); closePosition();
    }

MarketDataProvider is the read side (§23/§94): account, symbols, quotes, bars, spread,
positions. ExecutionProvider is the write side (§94/§96) — defined here so the seam is
complete, but NOT implemented against a live broker in the Shadow slice (§79: no
broker orders).
"""

from __future__ import annotations

from datetime import datetime
from typing import Protocol, runtime_checkable

from tc_domain.enums import Timeframe
from tc_domain.market import AccountSnapshot, Bar, Quote


@runtime_checkable
class MarketDataProvider(Protocol):
    """Read-only market data (§23, §94, §109 Phase-1 capabilities)."""

    def symbols(self) -> tuple[str, ...]:
        """Canonical instrument ids this provider can serve."""
        ...

    def account(self) -> AccountSnapshot:
        """Current account snapshot."""
        ...

    def quote(self, instrument: str) -> Quote | None:
        """Latest quote for ``instrument`` as of the provider's current clock."""
        ...

    def bars(
        self,
        instrument: str,
        timeframe: Timeframe,
        *,
        since: datetime | None = None,
        limit: int | None = None,
    ) -> tuple[Bar, ...]:
        """Historical bars, oldest→newest.

        For replay/no-look-ahead providers this returns only bars whose interval has
        closed at or before the provider's current clock (§126).
        """
        ...


@runtime_checkable
class ExecutionProvider(Protocol):
    """Order/position side (§96). Not live-implemented in the Shadow slice.

    The concrete ``Mt5ExecutionProvider`` lives on the Windows edge (ADR-032). In
    SHADOW the ``ShadowExecutionProvider`` (shadow-engine) implements this against the
    simulator, placing NO broker orders (§79).
    """

    def get_account(self) -> AccountSnapshot: ...

    def get_positions(self) -> tuple[object, ...]: ...

    def validate_order(self, order: object) -> object: ...

    def submit_order(self, order: object) -> object: ...

    def modify_order(self, order_id: str, changes: object) -> object: ...

    def close_position(self, position_id: str) -> object: ...
