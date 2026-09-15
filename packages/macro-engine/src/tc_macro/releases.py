"""Macro releases, surprise scoring and the convergence bridge (§46, §63, §150)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from tc_domain.enums import ConvergenceDomain, ImpactDirection


class SurpriseDirection(StrEnum):
    """Which way a POSITIVE surprise pushes the associated currency/asset."""

    HAWKISH_BULLISH = "HAWKISH_BULLISH"   # beat => currency bullish (CPI, rates, GDP)
    DOVISH_BEARISH = "DOVISH_BEARISH"     # beat => currency bearish (unemployment)


# Default polarity per §15 scheduled type. Explicit, not inferred.
DEFAULT_POLARITY: dict[str, SurpriseDirection] = {
    "CPI": SurpriseDirection.HAWKISH_BULLISH,
    "GDP": SurpriseDirection.HAWKISH_BULLISH,
    "PMI": SurpriseDirection.HAWKISH_BULLISH,
    "INTEREST_RATE_DECISION": SurpriseDirection.HAWKISH_BULLISH,
    "EMPLOYMENT": SurpriseDirection.HAWKISH_BULLISH,   # payroll beat = strong economy
    "UNEMPLOYMENT": SurpriseDirection.DOVISH_BEARISH,  # higher unemployment = weak
}


@dataclass(frozen=True)
class MacroRelease:
    """An economic release with the §46 fields."""

    event_type: str            # e.g. "CPI"
    country: str               # e.g. "US"
    actual: float
    forecast: float
    previous: float
    # Typical absolute surprise for this series, used to normalise (research param).
    typical_surprise: float = 0.2

    @property
    def surprise(self) -> float:
        """Raw surprise: actual − forecast (§46)."""
        return self.actual - self.forecast

    @property
    def normalised_surprise(self) -> float:
        """Surprise in 'typical surprise' units — comparable across series."""
        if self.typical_surprise <= 0:
            return 0.0
        return self.surprise / self.typical_surprise


def surprise_score(release: MacroRelease) -> float:
    """Map a normalised surprise to a 0..100 strength (saturating at ~3 sigma)."""
    mag = min(abs(release.normalised_surprise), 3.0)
    return round((mag / 3.0) * 100.0, 2)


def macro_convergence_input(
    release: MacroRelease,
    *,
    polarity: SurpriseDirection | None = None,
    freshness: float = 1.0,
):
    """Adapt a release to a MACRO_MONETARY convergence DomainInput (§150).

    Direction is derived from the surprise sign AND the series polarity — an
    unemployment beat is NOT bullish just because the number rose. A zero surprise is
    UNCERTAIN: an in-line print carries no directional information.
    """
    from tc_convergence import DomainInput

    pol = polarity or DEFAULT_POLARITY.get(
        release.event_type.upper(), SurpriseDirection.HAWKISH_BULLISH
    )
    s = release.surprise
    if s == 0:
        direction = ImpactDirection.UNCERTAIN
    else:
        positive_is_bullish = pol is SurpriseDirection.HAWKISH_BULLISH
        bullish = (s > 0) if positive_is_bullish else (s < 0)
        direction = ImpactDirection.BULLISH if bullish else ImpactDirection.BEARISH

    return DomainInput(
        domain=ConvergenceDomain.MACRO_MONETARY,
        strength=surprise_score(release),
        direction=direction,
        rationale=(
            f"{release.country} {release.event_type}: actual {release.actual} vs "
            f"forecast {release.forecast} (surprise {s:+.2f}, "
            f"{release.normalised_surprise:+.2f}σ)"
        ),
        freshness=freshness,
        correlation_group=f"macro:{release.country}:{release.event_type}",
    )
