"""Deterministic Adversarial Critic (§67).

Mandate: attempt to prove the proposed trade should NOT occur. Output is
NO_OBJECTION / CAUTION / VETO; a VETO carries explicit reason codes (§67).

The AI critic arrives in Phase 9. This deterministic critic handles the objections
that SHOULD be deterministic anyway (§55): mechanical conditions where a trade is
plainly ill-advised. It lives in the same un-overridable tier as risk — the AI critic
will ADD judgement on top, never remove these.

Objection ladder (worst wins):
  VETO      — condition that makes the trade indefensible now:
              stale data, event blackout, reward:risk below floor, missing stop.
  CAUTION   — condition that warrants waiting rather than forbidding:
              wide (but not blocking) spread, low convergence, recent loss streak,
              regime not eligible for the strategy.
  NO_OBJECTION — nothing found.

The critic does not size or decide direction; it only challenges. Its verdict feeds
the Decision Engine (which treats VETO as terminal and CAUTION as WAIT).
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from tc_domain.enums import CriticVerdict
from tc_domain.evidence import CriticAssessment


@dataclass(frozen=True)
class CriticInputs:
    """Facts the critic challenges (all known at decision time)."""

    reward_risk: Decimal
    has_stop: bool
    convergence_score: float
    data_is_stale: bool = False
    in_event_blackout: bool = False
    spread: Decimal | None = None
    caution_spread: Decimal | None = None   # spread above this → CAUTION (not block)
    consecutive_losses: int = 0
    caution_loss_streak: int = 3            # streak at/above this → CAUTION
    min_reward_risk: Decimal = Decimal("1.5")
    min_convergence: float = 40.0           # below this → CAUTION (weak case)
    regime_eligible: bool = True            # is the regime valid for the strategy (§72)


def criticise(inp: CriticInputs) -> CriticAssessment:
    """Return the adversarial assessment (§67). Worst objection wins."""
    veto: list[str] = []
    caution: list[str] = []

    # --- VETO conditions: the trade is indefensible right now ---
    if inp.data_is_stale:
        veto.append("STALE_DATA")
    if inp.in_event_blackout:
        veto.append("EVENT_BLACKOUT")
    if not inp.has_stop:
        veto.append("NO_STOP")
    if inp.reward_risk < inp.min_reward_risk:
        veto.append("REWARD_RISK_TOO_LOW")

    # --- CAUTION conditions: prefer to wait, not forbid ---
    if (
        inp.spread is not None
        and inp.caution_spread is not None
        and inp.spread > inp.caution_spread
    ):
        caution.append("WIDE_SPREAD")
    if inp.convergence_score < inp.min_convergence:
        caution.append("LOW_CONVERGENCE")
    if inp.consecutive_losses >= inp.caution_loss_streak:
        caution.append("LOSS_STREAK")
    if not inp.regime_eligible:
        caution.append("REGIME_NOT_ELIGIBLE")

    if veto:
        return CriticAssessment(
            verdict=CriticVerdict.VETO,
            reason_codes=tuple(veto),
            notes="deterministic veto: trade indefensible under current conditions",
        )
    if caution:
        return CriticAssessment(
            verdict=CriticVerdict.CAUTION,
            reason_codes=tuple(caution),
            notes="deterministic caution: prefer to wait for better conditions",
        )
    return CriticAssessment(verdict=CriticVerdict.NO_OBJECTION)
