"""Permission state machine + promotion gates (§133, §153, §75).

Deterministic policy code: this decides only whether a *state transition* is allowed.
It does not size, decide direction, or trade. AI cannot override it.
"""

from __future__ import annotations

from dataclasses import dataclass

from tc_domain.enums import MarketPermission
from tc_domain.policy import PolicyViolation, is_crypto_symbol

# Legal forward transitions (promotion). Anything else must be explicit demotion.
_PROMOTION_PATH: dict[MarketPermission, MarketPermission] = {
    MarketPermission.INTELLIGENCE_ONLY: MarketPermission.SHADOW_TRADABLE,
    MarketPermission.SHADOW_TRADABLE: MarketPermission.LIVE_TRADABLE,
}

# Ordering used to tell promotion from demotion.
_RANK: dict[MarketPermission, int] = {
    MarketPermission.PROHIBITED: -1,
    MarketPermission.INTELLIGENCE_ONLY: 0,
    MarketPermission.SHADOW_TRADABLE: 1,
    MarketPermission.LIVE_TRADABLE: 2,
}


@dataclass(frozen=True)
class PromotionRequest:
    """A request to change an instrument's permission state."""

    canonical_id: str
    current: MarketPermission
    target: MarketPermission
    # §75 promotion gates — required for LIVE_TRADABLE.
    adr_reference: str = ""          # e.g. "TC-ADR-0xx"
    edge_validated_oos: bool = False  # positive expectancy out-of-sample, net of costs
    sample_size: int = 0
    regimes_covered: int = 0          # distinct market regimes the evidence spans


@dataclass(frozen=True)
class PermissionDecision:
    allowed: bool
    resulting: MarketPermission
    reasons: tuple[str, ...] = ()


# §75 minimums for live promotion (research params; tighten as evidence matures).
MIN_SAMPLE_FOR_LIVE = 30
MIN_REGIMES_FOR_LIVE = 2


class PermissionEngine:
    """Evaluates permission transitions. Deterministic; refuses by default."""

    def evaluate(self, req: PromotionRequest) -> PermissionDecision:
        reasons: list[str] = []

        # 1. Crypto is prohibited, always, and can never be promoted (§7, TC-ADR-006).
        if is_crypto_symbol(req.canonical_id):
            return PermissionDecision(
                False, MarketPermission.PROHIBITED, ("ASSET_CLASS_PROHIBITED",)
            )

        # 2. PROHIBITED is terminal — nothing is promoted out of it without a spec change.
        if req.current is MarketPermission.PROHIBITED:
            return PermissionDecision(
                False, MarketPermission.PROHIBITED, ("CURRENT_IS_PROHIBITED",)
            )

        # 3. Demotion (including to PROHIBITED) is always allowed — safe direction.
        if _RANK[req.target] <= _RANK[req.current]:
            return PermissionDecision(True, req.target, ("DEMOTION_OR_NOOP",))

        # 4. Promotion must follow the path one step at a time (no skipping).
        expected = _PROMOTION_PATH.get(req.current)
        if expected is None or req.target is not expected:
            reasons.append("ILLEGAL_TRANSITION")
            return PermissionDecision(False, req.current, tuple(reasons))

        # 5. Any promotion requires an ADR reference (§133).
        if not req.adr_reference:
            reasons.append("ADR_REQUIRED")

        # 6. LIVE promotion additionally requires proof of edge (§75) — never profit
        #    or schedule (§0).
        if req.target is MarketPermission.LIVE_TRADABLE:
            if not req.edge_validated_oos:
                reasons.append("EDGE_NOT_VALIDATED_OOS")
            if req.sample_size < MIN_SAMPLE_FOR_LIVE:
                reasons.append("INSUFFICIENT_SAMPLE")
            if req.regimes_covered < MIN_REGIMES_FOR_LIVE:
                reasons.append("INSUFFICIENT_REGIME_COVERAGE")

        if reasons:
            return PermissionDecision(False, req.current, tuple(reasons))
        return PermissionDecision(True, req.target, ())

    def assert_tradable(
        self, canonical_id: str, permission: MarketPermission, *, live: bool
    ) -> None:
        """Raise unless ``permission`` allows trading at the requested level.

        ``live=False`` means "may this be shadow-traded?"; ``live=True`` means "may real
        money be risked?". Fail closed.
        """
        if is_crypto_symbol(canonical_id):
            raise PolicyViolation(
                "ASSET_CLASS_PROHIBITED", f"{canonical_id} is crypto (§7)"
            )
        needed = (
            MarketPermission.LIVE_TRADABLE if live else MarketPermission.SHADOW_TRADABLE
        )
        if _RANK[permission] < _RANK[needed]:
            raise PolicyViolation(
                "PERMISSION_INSUFFICIENT",
                f"{canonical_id} is {permission.value}; {needed.value} required "
                "(observation does not imply authority to trade, §133).",
            )
