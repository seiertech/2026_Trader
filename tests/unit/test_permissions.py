"""Permission state machine (§133, §153, §75, TC-ADR-026)."""

from __future__ import annotations

import pytest
from tc_domain.enums import MarketPermission as P
from tc_domain.policy import PolicyViolation
from tc_permissions import PermissionEngine, PromotionRequest

E = PermissionEngine()


def _req(**kw) -> PromotionRequest:
    base = dict(canonical_id="XAUUSD", current=P.INTELLIGENCE_ONLY,
                target=P.SHADOW_TRADABLE, adr_reference="TC-ADR-050",
                edge_validated_oos=False, sample_size=0, regimes_covered=0)
    base.update(kw)
    return PromotionRequest(**base)


def test_intelligence_to_shadow_with_adr() -> None:
    d = E.evaluate(_req())
    assert d.allowed and d.resulting is P.SHADOW_TRADABLE


def test_promotion_without_adr_refused() -> None:
    d = E.evaluate(_req(adr_reference=""))
    assert not d.allowed
    assert "ADR_REQUIRED" in d.reasons


def test_cannot_skip_straight_to_live() -> None:
    d = E.evaluate(_req(current=P.INTELLIGENCE_ONLY, target=P.LIVE_TRADABLE))
    assert not d.allowed
    assert "ILLEGAL_TRANSITION" in d.reasons


def test_live_requires_proof_of_edge() -> None:
    d = E.evaluate(_req(current=P.SHADOW_TRADABLE, target=P.LIVE_TRADABLE))
    assert not d.allowed
    assert "EDGE_NOT_VALIDATED_OOS" in d.reasons
    assert "INSUFFICIENT_SAMPLE" in d.reasons
    assert "INSUFFICIENT_REGIME_COVERAGE" in d.reasons


def test_live_allowed_when_all_gates_met() -> None:
    d = E.evaluate(_req(current=P.SHADOW_TRADABLE, target=P.LIVE_TRADABLE,
                        edge_validated_oos=True, sample_size=50, regimes_covered=3))
    assert d.allowed and d.resulting is P.LIVE_TRADABLE


def test_crypto_never_promotable() -> None:
    d = E.evaluate(_req(canonical_id="BTCUSD"))
    assert not d.allowed
    assert d.resulting is P.PROHIBITED
    assert "ASSET_CLASS_PROHIBITED" in d.reasons


def test_prohibited_is_terminal() -> None:
    d = E.evaluate(_req(current=P.PROHIBITED, target=P.SHADOW_TRADABLE))
    assert not d.allowed


def test_demotion_always_allowed() -> None:
    d = E.evaluate(_req(current=P.LIVE_TRADABLE, target=P.SHADOW_TRADABLE,
                        adr_reference=""))
    assert d.allowed  # safe direction needs no gate


def test_assert_tradable_shadow_ok_live_refused() -> None:
    E.assert_tradable("XAUUSD", P.SHADOW_TRADABLE, live=False)  # fine
    with pytest.raises(PolicyViolation):
        E.assert_tradable("XAUUSD", P.SHADOW_TRADABLE, live=True)


def test_assert_tradable_intelligence_only_refused() -> None:
    with pytest.raises(PolicyViolation):
        E.assert_tradable("EURGBP", P.INTELLIGENCE_ONLY, live=False)


def test_assert_tradable_crypto_refused() -> None:
    with pytest.raises(PolicyViolation):
        E.assert_tradable("BTCUSD", P.LIVE_TRADABLE, live=False)
