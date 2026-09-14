"""The Risk Engine gate (§73, §77).

Every proposed trade passes through this deterministic gate BEFORE execution. The Risk
Engine controls capital; AI SHALL NOT override it (§73, TC-ADR-012). This is the same
un-overridable tier as the crypto prohibition and the Prime Directive.

The gate enforces the §77 controls that are checkable at decision time against the
current portfolio/session state. Each control that fails contributes a reason code.
The verdict is the WORST outcome across all controls:

    APPROVE   — no control breached; trade may proceed at requested risk.
    REDUCE    — an open-risk / budget control is breachable but the trade can proceed
                at a smaller size (the gate returns the capped risk fraction).
    REJECT    — a hard control is breached; no trade (fail closed).

The gate NEVER raises risk — it only holds it or reduces it. Controls not yet
meaningful at decision time (e.g. MAX_SLIPPAGE, which is measured on fill) are checked
in the simulator/execution layer, not here; this gate documents which it owns.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from enum import StrEnum


class GateVerdict(StrEnum):
    APPROVE = "APPROVE"
    REDUCE = "REDUCE"
    REJECT = "REJECT"


# Reason codes (stable strings for audit/attribution).
class RiskReason(StrEnum):
    KILL_SWITCH = "KILL_SWITCH"
    MANDATORY_STOP_MISSING = "MANDATORY_STOP_MISSING"
    REWARD_RISK_TOO_LOW = "MIN_REWARD_RISK"
    SPREAD_TOO_WIDE = "MAX_SPREAD"
    STALE_DATA = "STALE_DATA_BLOCK"
    MAX_POSITIONS = "MAX_POSITIONS"
    MAX_CONSECUTIVE_LOSSES = "MAX_CONSECUTIVE_LOSSES"
    MAX_DAILY_LOSS = "MAX_DAILY_LOSS"
    MAX_OPEN_RISK = "MAX_OPEN_RISK"
    MAX_INSTRUMENT_EXPOSURE = "MAX_INSTRUMENT_EXPOSURE"


@dataclass(frozen=True)
class PortfolioState:
    """Everything the gate needs to know about current exposure/session (§66, §77)."""

    open_positions: int = 0
    open_risk_fraction: Decimal = Decimal(0)         # summed risk-at-stop / ref unit
    instrument_risk_fraction: Decimal = Decimal(0)   # for the candidate's instrument
    consecutive_losses: int = 0
    daily_loss_fraction: Decimal = Decimal(0)        # today's realised loss / ref unit
    data_is_stale: bool = False
    kill_switch: bool = False


@dataclass(frozen=True)
class ProposedTrade:
    """The candidate the gate evaluates."""

    instrument: str
    direction: str                # LONG | SHORT
    requested_risk_fraction: Decimal
    reward_risk: Decimal          # target distance / stop distance
    has_stop: bool
    spread: Decimal | None = None  # in price units, if known at decision time


@dataclass(frozen=True)
class GateResult:
    verdict: GateVerdict
    approved_risk_fraction: Decimal   # 0 on REJECT; possibly reduced on REDUCE
    reasons: tuple[str, ...] = field(default_factory=tuple)

    @property
    def approved(self) -> bool:
        return self.verdict is not GateVerdict.REJECT and self.approved_risk_fraction > 0


def _as_decimal(v: object, default: Decimal) -> Decimal:
    if v is None or isinstance(v, bool):
        return default
    try:
        return Decimal(str(v))
    except Exception:
        return default


def evaluate(
    trade: ProposedTrade,
    portfolio: PortfolioState,
    controls: dict[str, object],
) -> GateResult:
    """Run the §77 gate. ``controls`` is the risk_controls mapping from risk.yaml.

    Deterministic and fail-closed: any hard breach → REJECT; open-risk breaches →
    REDUCE (capped fraction); otherwise APPROVE at the requested risk.
    """
    reasons: list[str] = []

    # ---- Hard controls: any one of these → REJECT (fail closed) ----

    # Kill switch: operator hard-off (§77). Nothing trades.
    if portfolio.kill_switch or controls.get("KILL_SWITCH") is True:
        reasons.append(RiskReason.KILL_SWITCH)

    # Mandatory stop (§77): every position MUST carry a stop.
    if controls.get("MANDATORY_STOP") is True and not trade.has_stop:
        reasons.append(RiskReason.MANDATORY_STOP_MISSING)

    # Stale data (§104): do not trade on stale market data.
    if controls.get("STALE_DATA_BLOCK") is True and portfolio.data_is_stale:
        reasons.append(RiskReason.STALE_DATA)

    # Minimum reward:risk (§77).
    min_rr = _as_decimal(controls.get("MIN_REWARD_RISK"), Decimal(0))
    if min_rr > 0 and trade.reward_risk < min_rr:
        reasons.append(RiskReason.REWARD_RISK_TOO_LOW)

    # Max spread (§77): only if a spread and a limit are both known.
    max_spread = controls.get("MAX_SPREAD")
    if (
        max_spread is not None
        and trade.spread is not None
        and trade.spread > _as_decimal(max_spread, Decimal("Infinity"))
    ):
        reasons.append(RiskReason.SPREAD_TOO_WIDE)

    # Max positions (§77): would opening this exceed the cap?
    max_pos = controls.get("MAX_POSITIONS")
    if max_pos is not None and portfolio.open_positions >= int(_as_decimal(max_pos, Decimal(0))):
        reasons.append(RiskReason.MAX_POSITIONS)

    # Max consecutive losses (§77): cool-off after a streak.
    max_streak = controls.get("MAX_CONSECUTIVE_LOSSES")
    if max_streak is not None and portfolio.consecutive_losses >= int(
        _as_decimal(max_streak, Decimal(0))
    ):
        reasons.append(RiskReason.MAX_CONSECUTIVE_LOSSES)

    # Max daily loss (§77): stop trading once today's loss budget is spent.
    max_daily = _as_decimal(controls.get("MAX_DAILY_LOSS"), Decimal(0))
    if max_daily > 0 and portfolio.daily_loss_fraction >= max_daily:
        reasons.append(RiskReason.MAX_DAILY_LOSS)

    if reasons:
        return GateResult(GateVerdict.REJECT, Decimal(0), tuple(reasons))

    # ---- Soft controls: cap the size rather than reject (REDUCE) ----

    approved = trade.requested_risk_fraction
    reduce_reasons: list[str] = []

    # Max open risk (§77): summed risk across open positions must not exceed the cap.
    max_open = _as_decimal(controls.get("MAX_OPEN_RISK"), Decimal("Infinity"))
    headroom = max_open - portfolio.open_risk_fraction
    if headroom <= 0:
        return GateResult(GateVerdict.REJECT, Decimal(0), (RiskReason.MAX_OPEN_RISK,))
    if approved > headroom:
        approved = headroom
        reduce_reasons.append(RiskReason.MAX_OPEN_RISK)

    # Max instrument exposure (§77): per-instrument risk cap.
    max_inst = _as_decimal(controls.get("MAX_INSTRUMENT_EXPOSURE"), Decimal("Infinity"))
    inst_headroom = max_inst - portfolio.instrument_risk_fraction
    if inst_headroom <= 0:
        return GateResult(
            GateVerdict.REJECT, Decimal(0), (RiskReason.MAX_INSTRUMENT_EXPOSURE,)
        )
    if approved > inst_headroom:
        approved = inst_headroom
        reduce_reasons.append(RiskReason.MAX_INSTRUMENT_EXPOSURE)

    if reduce_reasons:
        return GateResult(GateVerdict.REDUCE, approved, tuple(reduce_reasons))
    return GateResult(GateVerdict.APPROVE, approved, ())
