"""Virtual Shadow account (§85).

A £250 reference-unit account with realistic capital constraints. The simulator MUST
NOT permit a trade the equivalent live £250 account could not execute (§85) — this
account exposes the available balance the sizing/affordability check uses.

The balance is NOT a growth target; it is the reference unit for R and expectancy
(§74, TC-ADR-016). Equity moves as trades close; there is no compounding mandate.
"""

from __future__ import annotations

from decimal import Decimal


class ShadowAccount:
    """Mutable virtual account: starting balance, realised equity, open-risk tracking."""

    def __init__(self, starting_balance: Decimal = Decimal(250), currency: str = "GBP") -> None:
        self._start = starting_balance
        self._balance = starting_balance
        self._currency = currency

    @property
    def currency(self) -> str:
        return self._currency

    @property
    def starting_balance(self) -> Decimal:
        return self._start

    @property
    def balance(self) -> Decimal:
        return self._balance

    def apply_realised(self, pnl: Decimal) -> None:
        """Apply a closed trade's net P&L to the balance."""
        self._balance += pnl

    def can_afford(self, notional: Decimal, max_leverage: Decimal = Decimal("10")) -> bool:
        """§85 affordability guard.

        These are leveraged CFDs (Eightcap/MT5), so the constraint is MARGIN, not full
        notional: the required margin = notional / max_leverage must not exceed the
        balance. ``max_leverage`` is a risk control (MAX_LEVERAGE, §77); the conservative
        default keeps the Phase-0 slice honest until real broker margins are discovered.
        A real £250 account genuinely could not hold a position whose margin exceeds
        £250 — that is the trade we refuse (§85)."""
        if max_leverage <= 0:
            return False
        required_margin = notional / max_leverage
        return required_margin <= self._balance
