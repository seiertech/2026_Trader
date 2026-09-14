"""Instrument entity and the canonical V1 universe (§5, §11, TC-ADR-007).

Canonical Trading Command identifiers are decoupled from broker symbols (§5, §135).
Broker symbol / contract size / tick size / etc. are discovered at integration time
and attached later; the canonical identity is stable and provider-independent
(TC-ADR-010, Part XXXI §3).

Crypto cannot be represented: :class:`AssetClass` has no CRYPTO member (TC-ADR-006).
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from tc_domain.enums import AssetClass, MarketPermission


class Instrument(BaseModel):
    """A tradable or monitored instrument in canonical form."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    canonical_id: str = Field(..., description="Stable TC identifier, e.g. 'XAUUSD'.")
    display_name: str
    asset_class: AssetClass
    # Broker specifics are optional until symbol discovery (Phase 1, §5/§135).
    broker_symbol: str | None = None
    # Default permission is the most restrictive that still allows monitoring.
    # Observation never implies trade authority (§133, TC-ADR-026).
    permission: MarketPermission = MarketPermission.INTELLIGENCE_ONLY


# The eight primary V1 instruments (§5). TC-ADR-007 fixes this count; expanding it is
# a spec change requiring an ADR (Part XXXI). These start SHADOW_TRADABLE because
# Shadow is the mandatory initial mode and carries no broker risk (§79, §154) — but
# NONE are LIVE_TRADABLE, honouring the no-live-without-approval guardrail.
CANONICAL_UNIVERSE: tuple[Instrument, ...] = (
    # Foreign Exchange
    Instrument(
        canonical_id="GBPUSD",
        display_name="Pound / US Dollar",
        asset_class=AssetClass.FOREX,
        permission=MarketPermission.SHADOW_TRADABLE,
    ),
    Instrument(
        canonical_id="EURUSD",
        display_name="Euro / US Dollar",
        asset_class=AssetClass.FOREX,
        permission=MarketPermission.SHADOW_TRADABLE,
    ),
    Instrument(
        canonical_id="USDJPY",
        display_name="US Dollar / Japanese Yen",
        asset_class=AssetClass.FOREX,
        permission=MarketPermission.SHADOW_TRADABLE,
    ),
    # Equity Indices
    Instrument(
        canonical_id="NAS100",
        display_name="US Tech 100 Index",
        asset_class=AssetClass.INDEX,
        permission=MarketPermission.SHADOW_TRADABLE,
    ),
    Instrument(
        canonical_id="US500",
        display_name="US 500 Index",
        asset_class=AssetClass.INDEX,
        permission=MarketPermission.SHADOW_TRADABLE,
    ),
    Instrument(
        canonical_id="UK100",
        display_name="UK 100 Index",
        asset_class=AssetClass.INDEX,
        permission=MarketPermission.SHADOW_TRADABLE,
    ),
    # Commodities
    Instrument(
        canonical_id="XAUUSD",
        display_name="Gold / US Dollar",
        asset_class=AssetClass.COMMODITY,
        permission=MarketPermission.SHADOW_TRADABLE,  # golden-path instrument (§123)
    ),
    Instrument(
        canonical_id="USOIL",
        display_name="US Crude Oil",
        asset_class=AssetClass.COMMODITY,
        permission=MarketPermission.SHADOW_TRADABLE,
    ),
)

UNIVERSE_BY_ID: dict[str, Instrument] = {i.canonical_id: i for i in CANONICAL_UNIVERSE}
