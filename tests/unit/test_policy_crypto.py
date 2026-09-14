"""Crypto prohibition is deterministic and un-overridable (§7, TC-ADR-006)."""

from __future__ import annotations

import pytest
from tc_domain.enums import AssetClass
from tc_domain.policy import (
    ASSET_CLASS_PROHIBITED,
    PolicyViolation,
    assert_not_crypto,
    is_crypto_symbol,
)


@pytest.mark.parametrize(
    "symbol",
    ["BTCUSD", "ETHUSD", "btcusd", "XBTUSD", "SOLUSDT", "DOGEUSD", "bitcoin-perp"],
)
def test_crypto_symbols_are_rejected(symbol: str) -> None:
    assert is_crypto_symbol(symbol) is True
    with pytest.raises(PolicyViolation) as exc:
        assert_not_crypto(symbol)
    assert exc.value.code == ASSET_CLASS_PROHIBITED


@pytest.mark.parametrize("symbol", ["XAUUSD", "GBPUSD", "EURUSD", "NAS100", "USOIL", "UK100"])
def test_canonical_universe_symbols_pass(symbol: str) -> None:
    assert is_crypto_symbol(symbol) is False
    assert_not_crypto(symbol)  # does not raise


def test_asset_class_enum_has_no_crypto_member() -> None:
    # Crypto is unrepresentable by construction — the strongest form of the rule.
    assert "CRYPTO" not in AssetClass.__members__
    assert {a.value for a in AssetClass} == {"FOREX", "INDEX", "COMMODITY"}
