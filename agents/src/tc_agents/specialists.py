"""The nine specialists (§58-66). Thin interpreters over deterministic engine output.

Every specialist reads from a shared ``context`` dict supplied by the runtime (regime
assessment, indicator values, macro input, exposure summary, event state...) and returns
an :class:`Assessment`. If the context lacks what a specialist needs, it returns a
low-confidence NEUTRAL rather than guessing — never invent facts (§44).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from tc_domain.enums import RegimeType

from tc_agents.base import Assessment

_TRENDING = {RegimeType.STRONG_TREND, RegimeType.WEAK_TREND, RegimeType.BREAKOUT}


def _neutral(name: str, why: str) -> Assessment:
    return Assessment(name, "NEUTRAL", "NEITHER", 0.1, f"insufficient context: {why}")


@dataclass(frozen=True)
class RegimeSpecialist:
    """§58 — determines the current market regime."""

    name: str = "regime"

    def assess(self, context: dict[str, Any]) -> Assessment:
        r = context.get("regime")
        if r is None:
            return _neutral(self.name, "no regime assessment")
        regime = getattr(r, "regime", None)
        adx = getattr(r, "adx", None)
        conf = 0.3 if regime is RegimeType.UNKNOWN else min(1.0, ((adx or 0) / 40.0))
        return Assessment(
            self.name, str(getattr(regime, "value", regime)), "NEITHER",
            round(conf, 3), f"regime={getattr(regime,'value',regime)}, ADX={adx}",
        )


@dataclass(frozen=True)
class TrendSpecialist:
    """§59 — directional structure."""

    name: str = "trend"

    def assess(self, context: dict[str, Any]) -> Assessment:
        r = context.get("regime")
        if r is None:
            return _neutral(self.name, "no regime assessment")
        up = getattr(r, "trend_up", None)
        regime = getattr(r, "regime", None)
        if up is None or regime not in _TRENDING:
            return Assessment(self.name, "NO_TREND", "NEITHER", 0.3,
                              f"regime={getattr(regime,'value',regime)} is not trending")
        verdict = "TRENDING_UP" if up else "TRENDING_DOWN"
        adx = getattr(r, "adx", None) or 0
        return Assessment(self.name, verdict, "LONG" if up else "SHORT",
                          round(min(1.0, adx / 40.0), 3),
                          f"EMA structure {'up' if up else 'down'}, ADX={adx:.1f}")


@dataclass(frozen=True)
class MomentumSpecialist:
    """§60 — acceleration / deceleration / divergence."""

    name: str = "momentum"

    def assess(self, context: dict[str, Any]) -> Assessment:
        rsi = context.get("rsi")
        if rsi is None:
            return _neutral(self.name, "no RSI")
        if rsi >= 70:
            return Assessment(self.name, "OVERBOUGHT", "SHORT", 0.5,
                              f"RSI {rsi:.0f} stretched")
        if rsi <= 30:
            return Assessment(self.name, "OVERSOLD", "LONG", 0.5, f"RSI {rsi:.0f} stretched")
        lean = "LONG" if rsi > 55 else "SHORT" if rsi < 45 else "NEITHER"
        return Assessment(self.name, "NEUTRAL_MOMENTUM", lean, 0.35, f"RSI {rsi:.0f}")


@dataclass(frozen=True)
class StructureSpecialist:
    """§61 — support / resistance / breakout / breakdown / invalidation."""

    name: str = "structure"

    def assess(self, context: dict[str, Any]) -> Assessment:
        r = context.get("regime")
        if r is None:
            return _neutral(self.name, "no regime assessment")
        if getattr(r, "breakout", False):
            return Assessment(self.name, "BREAKOUT", "LONG", 0.6, "fresh high vs lookback")
        if getattr(r, "breakdown", False):
            return Assessment(self.name, "BREAKDOWN", "SHORT", 0.6, "fresh low vs lookback")
        return Assessment(self.name, "RANGE_BOUND", "NEITHER", 0.4,
                          "no fresh extreme vs lookback")


@dataclass(frozen=True)
class VolatilitySpecialist:
    """§62 — is volatility appropriate for the strategy?"""

    name: str = "volatility"

    def assess(self, context: dict[str, Any]) -> Assessment:
        r = context.get("regime")
        ratio = getattr(r, "vol_ratio", None) if r is not None else None
        if ratio is None:
            return _neutral(self.name, "no volatility ratio")
        if ratio >= 1.6:
            return Assessment(self.name, "EXPANDING", "NEITHER", 0.6,
                              f"ATR ratio {ratio:.2f} — expansion; widen stops")
        if ratio <= 0.6:
            return Assessment(self.name, "CONTRACTING", "NEITHER", 0.5,
                              f"ATR ratio {ratio:.2f} — contraction; breakout risk")
        return Assessment(self.name, "NORMAL", "NEITHER", 0.4, f"ATR ratio {ratio:.2f}")


@dataclass(frozen=True)
class MacroSpecialist:
    """§63 — rates / inflation / employment / growth / central banks."""

    name = "macro"

    def assess(self, context: dict[str, Any]) -> Assessment:
        mi = context.get("macro_input")  # a convergence DomainInput from tc_macro
        if mi is None:
            return _neutral(self.name, "no macro release in context")
        direction = getattr(getattr(mi, "direction", None), "value", "UNCERTAIN")
        supports = {"BULLISH": "LONG", "BEARISH": "SHORT"}.get(direction, "NEITHER")
        strength = float(getattr(mi, "strength", 0.0))
        return Assessment(self.name, direction, supports, round(strength / 100.0, 3),
                          getattr(mi, "rationale", "macro surprise"))


@dataclass(frozen=True)
class EventIntelligenceSpecialist:
    """§64 — politics / geopolitics / sanctions / tariffs / energy / breaking events."""

    name = "event_intelligence"

    def assess(self, context: dict[str, Any]) -> Assessment:
        ev = context.get("event")
        if ev is None:
            return _neutral(self.name, "no event in context")
        # Confidence follows corroboration, not drama (§29).
        sources = int(getattr(ev, "source_count", 1))
        conf = min(1.0, sources / 5.0)
        blackout = bool(context.get("in_blackout", False))
        verdict = "BLACKOUT" if blackout else str(getattr(ev, "category", "Other"))
        note = (
            "inside a high-impact release blackout — no new entries (§77)"
            if blackout else
            f"{getattr(ev,'category','Other')} event, {sources} source(s), "
            f"novelty {getattr(ev,'novelty','?')}"
        )
        return Assessment(self.name, verdict, "NEITHER", round(conf, 3), note)


@dataclass(frozen=True)
class MarketLeadersSpecialist:
    """§65 — company/sector movement related to tradable instruments."""

    name = "market_leaders"

    def assess(self, context: dict[str, Any]) -> Assessment:
        f = context.get("basket_factor")
        if f is None:
            return _neutral(self.name, "no basket factor in context")
        direction = getattr(getattr(f, "direction", None), "value", "UNCERTAIN")
        supports = {"BULLISH": "LONG", "BEARISH": "SHORT"}.get(direction, "NEITHER")
        # One basket = one factor (§148); coherence gates the confidence.
        conf = float(getattr(f, "coherence", 0.0)) * min(
            1.0, float(getattr(f, "strength", 0.0)) / 100.0
        )
        return Assessment(self.name, direction, supports, round(conf, 3),
                          getattr(f, "detail", "basket move"))


@dataclass(frozen=True)
class PortfolioSpecialist:
    """§66 — is this candidate appropriate given existing exposure?"""

    name = "portfolio"

    def assess(self, context: dict[str, Any]) -> Assessment:
        exp = context.get("exposure")
        if exp is None:
            return _neutral(self.name, "no exposure summary")
        instrument = context.get("instrument", "")
        direction = context.get("direction", "")
        opposing = bool(context.get("has_opposing", False))
        cluster_risk = getattr(exp, "by_cluster", {}) or {}
        n = int(getattr(exp, "open_positions", 0))

        if opposing:
            return Assessment(self.name, "CONFLICTS_WITH_BOOK", "NEITHER", 0.8,
                              f"already hold the opposite side of {instrument}")
        worst = max(cluster_risk.values(), default=0)
        if float(worst) > 0:
            return Assessment(self.name, "ADDS_TO_CLUSTER", "NEITHER", 0.5,
                              f"{n} open position(s); correlated cluster risk {worst}")
        return Assessment(self.name, "CLEAR", direction or "NEITHER", 0.4,
                          f"{n} open position(s), no correlated overlap")


def all_specialists() -> tuple[object, ...]:
    """The full specialist roster (§58-66)."""
    return (
        RegimeSpecialist(), TrendSpecialist(), MomentumSpecialist(),
        StructureSpecialist(), VolatilitySpecialist(), MacroSpecialist(),
        EventIntelligenceSpecialist(), MarketLeadersSpecialist(), PortfolioSpecialist(),
    )
