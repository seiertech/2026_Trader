"""tc_risk — the Risk Engine (§73–§77, §77a).

The Risk Engine controls capital deterministically. AI SHALL NOT override it (§73,
TC-ADR-012). This package holds the position-sizing method (§77a fractional Kelly,
TC-CR-001 / TC-ADR-042) and, over time, the §77 control clamps.

Fractional Kelly rules implemented here are DETERMINISTIC POLICY TIER — the
positive-edge gate and the §77 ceiling clamp are as un-overridable as the crypto
prohibition and the Prime Directive.
"""

from tc_risk.kelly import (
    BindingConstraint,
    EdgeStats,
    SizingResult,
    kelly_fraction,
    size_risk_fraction,
    wilson_lower_bound,
)

__all__ = [
    "BindingConstraint",
    "EdgeStats",
    "SizingResult",
    "kelly_fraction",
    "size_risk_fraction",
    "wilson_lower_bound",
]
