"""Deterministic, un-overridable policy checks.

Two rules sit in the highest tier of TC-SPEC-001 — the tier that neither AI nor human
urgency may override (§0, §7). They are implemented here as pure functions with no
dependencies, so they cannot be silently bypassed and are trivially testable.

  1. CRYPTO PROHIBITION (§7, TC-ADR-006): any crypto instrument entering the trading
     pipeline yields ``ASSET_CLASS_PROHIBITED``.
  2. NO RETURN TARGET (§0, §75, TC-ADR-017): V1 has no capital return target and
     nothing may set, display or act upon one.

These functions raise :class:`PolicyViolation` (a hard stop) rather than returning
soft flags — a violated prime-directive rule is a defect, not a warning (§0).
"""

from __future__ import annotations

import re


class PolicyViolation(Exception):
    """Raised when an un-overridable policy rule is breached. Reason code attached."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(f"[{code}] {message}")


# --- 1. Crypto prohibition ---------------------------------------------------------

# Substrings that mark a symbol/name as crypto. Deliberately broad and case-insensitive;
# a false positive is a monitoring gap, a false negative is a spec breach — so we bias
# toward rejecting. Expanding the ALLOWED universe is an ADR change, not an edit here.
_CRYPTO_MARKERS: tuple[str, ...] = (
    "BTC", "XBT", "ETH", "BITCOIN", "ETHEREUM", "CRYPTO", "USDT", "USDC",
    "SOL", "SOLANA", "XRP", "RIPPLE", "DOGE", "ADA", "CARDANO", "LTC",
    "LITECOIN", "BNB", "DOT", "POLKADOT", "AVAX", "SHIB", "MATIC", "TON",
    "STABLECOIN", "ALTCOIN", "DEFI", "TOKEN",
)

_CRYPTO_RE = re.compile("|".join(re.escape(m) for m in _CRYPTO_MARKERS), re.IGNORECASE)

ASSET_CLASS_PROHIBITED = "ASSET_CLASS_PROHIBITED"


def is_crypto_symbol(symbol: str) -> bool:
    """Return True if ``symbol`` looks like a crypto instrument."""
    return bool(_CRYPTO_RE.search(symbol or ""))


def assert_not_crypto(symbol: str) -> None:
    """Hard-stop if ``symbol`` is crypto (§7, TC-ADR-006).

    Raises :class:`PolicyViolation` with code ``ASSET_CLASS_PROHIBITED``. AI cannot
    override this; it is deterministic policy code by design.
    """
    if is_crypto_symbol(symbol):
        raise PolicyViolation(
            ASSET_CLASS_PROHIBITED,
            f"instrument '{symbol}' is crypto; crypto is prohibited in V1 (TC-SPEC §7).",
        )


# --- 2. No return target (Prime Directive) -----------------------------------------

RETURN_TARGET_FORBIDDEN = "RETURN_TARGET_FORBIDDEN"


def assert_no_return_target(value: object) -> None:
    """Hard-stop if code attempts to set a capital return/growth target.

    V1 has NO return target (§0, §75, TC-ADR-017). Progression is gated by proof of
    edge, never profit or schedule. Any non-empty target is a defect.
    """
    if value not in (None, "", 0, 0.0, False):
        raise PolicyViolation(
            RETURN_TARGET_FORBIDDEN,
            "V1 has no capital return target; promotion is gated by proof of edge, "
            "not profit or schedule (Prime Directive §0, §75, TC-ADR-017).",
        )
