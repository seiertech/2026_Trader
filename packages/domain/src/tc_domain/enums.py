"""Taxonomy enumerations — the controlled vocabulary of TC-SPEC-001.

These enums are deliberately closed sets. The spec's Part XXXI forbids silently
altering the taxonomy, so adding a member is a spec-level change requiring an ADR.

Note especially :class:`AssetClass`: there is NO ``CRYPTO`` member. Crypto is
prohibited (TC-ADR-006, §7), and the cleanest enforcement is to make it
*unrepresentable* in the canonical model rather than representable-but-blocked.
A separate policy check (in the config/policy layer) rejects any external symbol that
maps to crypto, producing ``ASSET_CLASS_PROHIBITED``.
"""

from __future__ import annotations

from enum import StrEnum


class AssetClass(StrEnum):
    """V1 canonical asset classes (§5, §11).

    CRYPTO is intentionally absent — see module docstring and TC-ADR-006.
    """

    FOREX = "FOREX"
    INDEX = "INDEX"
    COMMODITY = "COMMODITY"


class OperatingMode(StrEnum):
    """Operating modes (Part XVIII). Order is the promotion path (§75)."""

    OFF = "OFF"
    SHADOW = "SHADOW"  # mandatory initial mode (§79, TC-ADR-015)
    PAPER = "PAPER"
    LIVE_LIMITED = "LIVE_LIMITED"
    LIVE_AUTO = "LIVE_AUTO"


# Explicit promotion ordering (§75). Progression is gated by PROOF, never profit or
# schedule — that gate lives in the risk/decision layer; this only names the order.
MODE_PROMOTION_ORDER: tuple[OperatingMode, ...] = (
    OperatingMode.SHADOW,
    OperatingMode.PAPER,
    OperatingMode.LIVE_LIMITED,
    OperatingMode.LIVE_AUTO,
)


class MarketPermission(StrEnum):
    """Per-instrument permission state (§133, §153, TC-ADR-026).

    Observation NEVER implies authority to trade. Promotion between states requires
    configuration change, evidence and an ADR.
    """

    INTELLIGENCE_ONLY = "INTELLIGENCE_ONLY"
    SHADOW_TRADABLE = "SHADOW_TRADABLE"
    LIVE_TRADABLE = "LIVE_TRADABLE"
    PROHIBITED = "PROHIBITED"


class Timeframe(StrEnum):
    """Multi-timeframe model (§35)."""

    M1 = "1m"
    M5 = "5m"
    M15 = "15m"
    H1 = "1h"
    H4 = "4h"
    D1 = "1d"


# Forward outcome-labelling horizons (§49) — mandatory for every detected opportunity.
OUTCOME_HORIZONS: tuple[str, ...] = ("5m", "15m", "30m", "1h", "4h", "1d")


class RegimeType(StrEnum):
    """Market regime taxonomy (§34). Strategies SHALL be regime-aware."""

    STRONG_TREND = "STRONG_TREND"
    WEAK_TREND = "WEAK_TREND"
    RANGE = "RANGE"
    BREAKOUT = "BREAKOUT"
    VOLATILITY_EXPANSION = "VOLATILITY_EXPANSION"
    VOLATILITY_CONTRACTION = "VOLATILITY_CONTRACTION"
    EVENT_DRIVEN = "EVENT_DRIVEN"
    DISORDERLY = "DISORDERLY"
    UNKNOWN = "UNKNOWN"


class SignalType(StrEnum):
    """Signal taxonomy (§13). Signals are derived from observations."""

    TECHNICAL = "TECHNICAL"
    MACRO = "MACRO"
    NEWS = "NEWS"
    POLITICAL = "POLITICAL"
    GEOPOLITICAL = "GEOPOLITICAL"
    CORPORATE = "CORPORATE"
    SECTOR = "SECTOR"
    CROSS_MARKET = "CROSS_MARKET"
    SENTIMENT = "SENTIMENT"
    EVENT = "EVENT"
    EXECUTION = "EXECUTION"


class ConvergenceDomain(StrEnum):
    """Independent evidence factor-families for convergence scoring (§36, §150).

    Convergence counts agreement across INDEPENDENT domains, not indicator counts
    (TC-ADR-013). Correlated evidence is collapsed before scoring (§39, TC-ADR-028).
    """

    MARKET_STRUCTURE = "MARKET_STRUCTURE"
    MOMENTUM_VOLATILITY = "MOMENTUM_VOLATILITY"
    MACRO_MONETARY = "MACRO_MONETARY"
    NEWS_EVENT = "NEWS_EVENT"
    CORPORATE_SECTOR = "CORPORATE_SECTOR"
    STRATEGIC_MATERIALS_SUPPLY_CHAIN = "STRATEGIC_MATERIALS_SUPPLY_CHAIN"
    HEALTHCARE_LIFE_SCIENCES = "HEALTHCARE_LIFE_SCIENCES"
    CROSS_MARKET = "CROSS_MARKET"
    HISTORICAL_ANALOGUE = "HISTORICAL_ANALOGUE"
    EXECUTION_QUALITY = "EXECUTION_QUALITY"


class OpportunityOrigin(StrEnum):
    """How an opportunity was surfaced (§40, §41)."""

    MARKET = "MARKET"
    EVENT = "EVENT"
    CONVERGENCE = "CONVERGENCE"


class DecisionOutcome(StrEnum):
    """Decision Engine outcomes (§69). WAIT is a first-class state (§70)."""

    LONG = "LONG"
    SHORT = "SHORT"
    WAIT = "WAIT"
    REJECT = "REJECT"


class CriticVerdict(StrEnum):
    """Adversarial Critic output (§67). VETO requires explicit reason codes."""

    NO_OBJECTION = "NO_OBJECTION"
    CAUTION = "CAUTION"
    VETO = "VETO"


class ImpactDirection(StrEnum):
    """Expected direction of a market-impact hypothesis (§152)."""

    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    VOLATILITY = "VOLATILITY"
    UNCERTAIN = "UNCERTAIN"


class EventStatus(StrEnum):
    """Event lifecycle status (§16)."""

    EMERGING = "EMERGING"
    DEVELOPING = "DEVELOPING"
    CONFIRMED = "CONFIRMED"
    STABLE = "STABLE"
    RESOLVED = "RESOLVED"


class ThemeLifecycle(StrEnum):
    """Theme lifecycle (§147, TC-ADR-029). Themes are durable objects."""

    EMERGING = "EMERGING"
    ACCELERATING = "ACCELERATING"
    ESTABLISHED = "ESTABLISHED"
    DECELERATING = "DECELERATING"
    DORMANT = "DORMANT"
    RESOLVED = "RESOLVED"


class StrategyState(StrEnum):
    """Strategy decay lifecycle (§93)."""

    ACTIVE = "ACTIVE"
    WATCH = "WATCH"
    DEGRADED = "DEGRADED"
    SUSPENDED = "SUSPENDED"
    RETIRED = "RETIRED"


class HealthState(StrEnum):
    """System health states (§103). Failure fails closed (§104, Part XXXI §7)."""

    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    TRADING_DISABLED = "TRADING_DISABLED"
    CRITICAL = "CRITICAL"


class RelationshipKind(StrEnum):
    """Supply-chain / graph relationship types (§144)."""

    SUPPLIES = "SUPPLIES"
    CONSUMES = "CONSUMES"
    PRODUCES = "PRODUCES"
    DEPENDS_ON = "DEPENDS_ON"
    SUBSTITUTES_FOR = "SUBSTITUTES_FOR"
    COMPETES_WITH = "COMPETES_WITH"
    REGULATES = "REGULATES"
    FINANCES = "FINANCES"
    INSURES = "INSURES"
    TRANSPORTS = "TRANSPORTS"
    INDEX_MEMBER_OF = "INDEX_MEMBER_OF"
    EXPOSED_TO_COUNTRY = "EXPOSED_TO_COUNTRY"
    EXPOSED_TO_COMMODITY = "EXPOSED_TO_COMMODITY"
    EXPOSED_TO_THEME = "EXPOSED_TO_THEME"
