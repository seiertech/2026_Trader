"""tc_domain — the Trading Command core domain model.

This package is the single source of truth for the taxonomy and entities defined by
TC-SPEC-001 v1.3 (Part IV taxonomy; §41, §43, §152, §153 entities). It contains NO
business logic, NO I/O, NO provider dependencies — only typed vocabulary and value
objects that every other package speaks (separation of concerns, Part XXXI §1).

Guardrails that live at the domain level:
  * ``AssetClass.CRYPTO`` does not exist — crypto is prohibited (TC-ADR-006, §7).
    A canonical instrument can never be crypto by construction.
  * Immutable records (Evidence Pack, thesis) are frozen models (TC-ADR-018, §90).
  * All timestamps are UTC-aware (§125).
"""

from tc_domain.enums import (
    AssetClass,
    ConvergenceDomain,
    DecisionOutcome,
    EventStatus,
    HealthState,
    MarketPermission,
    OperatingMode,
    RegimeType,
    SignalType,
    Timeframe,
)
from tc_domain.instrument import CANONICAL_UNIVERSE, Instrument
from tc_domain.time import utc_now

__all__ = [
    "AssetClass",
    "ConvergenceDomain",
    "DecisionOutcome",
    "EventStatus",
    "HealthState",
    "MarketPermission",
    "OperatingMode",
    "RegimeType",
    "SignalType",
    "Timeframe",
    "Instrument",
    "CANONICAL_UNIVERSE",
    "utc_now",
]
