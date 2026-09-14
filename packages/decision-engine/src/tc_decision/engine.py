"""Decision Engine logic (§68–§70).

Decision precedence (deterministic, fail-closed):

  1. Critic VETO                      → REJECT   (§67: veto is binding)
  2. Risk gate REJECT                 → REJECT   (§73: risk controls capital)
  3. Opportunity expired / stale      → REJECT   (§42)
  4. Bias unclear (no direction)      → WAIT     (§70)
  5. Critic CAUTION or gate REDUCE    → WAIT     (reassess; don't force a trade, §3)
  6. Otherwise                        → LONG or SHORT per the opportunity bias

WAIT is first-class (§70): the same opportunity may be re-evaluated on a later bar.
REJECT is terminal for that opportunity instance.

The engine records BOTH explainability registers (§101): a plain-English line for the
operator and a detailed evidence string for audit/research. The produced Decision is
immutable (§90).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from tc_domain.enums import CriticVerdict, DecisionOutcome, RegimeType
from tc_domain.evidence import CriticAssessment, Decision


@dataclass(frozen=True)
class DecisionInputs:
    """Everything the Decision Engine consumes (§68), as far as this slice needs."""

    opportunity_id: str
    evidence_pack_id: str
    instrument: str
    bias: str                      # "LONG" | "SHORT" | "" (unclear)
    regime: RegimeType
    convergence_score: float
    decided_at: datetime
    expired: bool = False
    critic: CriticAssessment | None = None
    gate_verdict: str = "APPROVE"  # APPROVE | REDUCE | REJECT
    gate_reasons: tuple[str, ...] = ()


def _plain(outcome: DecisionOutcome, why: str) -> str:
    return f"{outcome.value}: {why}"


def decide(inp: DecisionInputs, *, decision_id: str) -> Decision:
    """Produce an immutable Decision from the inputs, following the §68–70 precedence."""
    critic = inp.critic
    detail_parts = [
        f"instrument={inp.instrument}",
        f"regime={inp.regime.value}",
        f"convergence={inp.convergence_score:.1f}",
        f"bias={inp.bias or 'UNCLEAR'}",
        f"gate={inp.gate_verdict}{list(inp.gate_reasons) or ''}",
        f"critic={critic.verdict.value if critic else 'NONE'}"
        + (f"{list(critic.reason_codes)}" if critic and critic.reason_codes else ""),
    ]

    def build(outcome: DecisionOutcome, why: str) -> Decision:
        return Decision(
            id=decision_id,
            opportunity_id=inp.opportunity_id,
            evidence_pack_id=inp.evidence_pack_id,
            outcome=outcome,
            decided_at=inp.decided_at,
            plain_english=_plain(outcome, why),
            detailed_evidence="; ".join(detail_parts) + f" | {why}",
            critic=critic,
        )

    # 1. Critic VETO is binding (§67).
    if critic is not None and critic.verdict is CriticVerdict.VETO:
        return build(DecisionOutcome.REJECT,
                     f"critic VETO ({', '.join(critic.reason_codes) or 'no code'})")

    # 2. Risk gate rejected the trade (§73) — risk controls capital.
    if inp.gate_verdict == "REJECT":
        return build(DecisionOutcome.REJECT,
                     f"risk gate REJECT ({', '.join(inp.gate_reasons) or 'no reason'})")

    # 3. Stale / expired opportunity (§42).
    if inp.expired:
        return build(DecisionOutcome.REJECT, "opportunity expired (stale)")

    # 4. No clear directional bias → WAIT (reassess later, §70).
    if inp.bias not in ("LONG", "SHORT"):
        return build(DecisionOutcome.WAIT, "no clear directional bias yet")

    # 5. Critic CAUTION or gate REDUCE → WAIT rather than force activity (§3).
    if critic is not None and critic.verdict is CriticVerdict.CAUTION:
        return build(DecisionOutcome.WAIT,
                     f"critic CAUTION ({', '.join(critic.reason_codes) or 'no code'}); await confirmation")
    if inp.gate_verdict == "REDUCE":
        return build(DecisionOutcome.WAIT,
                     f"risk gate REDUCE ({', '.join(inp.gate_reasons)}); await better conditions")

    # 6. Clean path → act on the opportunity's bias.
    outcome = DecisionOutcome.LONG if inp.bias == "LONG" else DecisionOutcome.SHORT
    why = f"evidence supports {inp.bias.lower()}; no objection, risk approved"
    return build(outcome, why)
