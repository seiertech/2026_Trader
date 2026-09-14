"""Convergence scoring (§36–§39, §150).

Model (§150), applied per domain then aggregated:

    adjusted_strength = raw_strength
                      × independence_factor      (down-weight correlated domains)
                      × freshness_factor          (stale evidence counts for less)
                      × source_confidence         (0..1)
                      × regime_relevance           (0..1; is this domain meaningful now)

The final 0–100 score rewards AGREEMENT across INDEPENDENT domains that point the same
direction, and penalises disagreement. Correlated domains (declared via a correlation
group) are collapsed to a single effective contribution before aggregation (§39), so
three semiconductor names moving together do not count as three independent signals.

Everything is deterministic and the component breakdown is returned intact (§38). The
exact weights are configuration-controlled research parameters, calibrated in Shadow
(§150) — sensible defaults live here.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from tc_domain.enums import ConvergenceDomain, ImpactDirection
from tc_domain.evidence import DomainEvidence


@dataclass(frozen=True)
class DomainInput:
    """One domain's contribution before adjustment (§36, §150)."""

    domain: ConvergenceDomain
    strength: float                       # 0..100 raw strength of this domain's read
    direction: ImpactDirection            # which way this domain points
    rationale: str = ""
    freshness: float = 1.0                # 0..1 (1 = fresh; decays with staleness)
    source_confidence: float = 1.0        # 0..1
    regime_relevance: float = 1.0         # 0..1 (is this domain meaningful in-regime)
    correlation_group: str | None = None  # domains sharing a group are collapsed (§39)


@dataclass(frozen=True)
class ConvergenceResult:
    """0–100 score with its retained components (§38)."""

    score: float
    direction: ImpactDirection            # net direction the evidence supports
    contributing: tuple[DomainEvidence, ...]   # per-domain adjusted evidence (kept)
    agreeing_domains: int
    conflicting_domains: int
    collapsed_groups: tuple[str, ...] = field(default_factory=tuple)
    detail: str = ""


def _adjust(d: DomainInput) -> float:
    """Adjusted strength per §150 (all factors clamped to sane ranges)."""
    f = _clamp01(d.freshness) * _clamp01(d.source_confidence) * _clamp01(d.regime_relevance)
    return _clamp(d.strength, 0.0, 100.0) * f


def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def _clamp01(x: float) -> float:
    return _clamp(x, 0.0, 1.0)


def score_convergence(
    inputs: list[DomainInput],
    *,
    independence_floor: float = 0.4,
) -> ConvergenceResult:
    """Compute the convergence score from independent domain inputs.

    Correlated domains (same ``correlation_group``) are collapsed to their single
    strongest adjusted contribution before aggregation (§39). The net direction is the
    side with the greater agreeing adjusted strength; the score scales with the
    dominance of the agreeing side and the number of independent domains that agree.

    ``independence_floor`` down-weights domains within a collapsed group that are not
    the group's representative, rather than dropping them entirely.
    """
    if not inputs:
        return ConvergenceResult(0.0, ImpactDirection.UNCERTAIN, (), 0, 0, (), "no evidence")

    # --- Step 1: collapse correlated groups (§39) ---
    groups: dict[str, list[DomainInput]] = {}
    singles: list[DomainInput] = []
    for d in inputs:
        if d.correlation_group:
            groups.setdefault(d.correlation_group, []).append(d)
        else:
            singles.append(d)

    # effective entries: (input, adjusted_strength, is_independent). A collapsed
    # group contributes exactly ONE independent entry (its representative); the other
    # members are retained for explainability but flagged non-independent so they add
    # NOTHING to breadth or the directional tally (§148, §39 — no double-counting).
    effective: list[tuple[DomainInput, float, bool]] = [(d, _adjust(d), True) for d in singles]
    collapsed: list[str] = []
    for name, members in groups.items():
        collapsed.append(name)
        members_sorted = sorted(members, key=lambda m: _adjust(m), reverse=True)
        rep = members_sorted[0]
        effective.append((rep, _adjust(rep), True))  # the one independent contribution
        for extra in members_sorted[1:]:
            effective.append((extra, 0.0, False))     # correlated: no extra weight

    independent = [(d, s) for d, s, ind in effective if ind]

    # --- Step 2: tally directional agreement (independent contributions only) ---
    bull = sum(s for d, s in independent if d.direction is ImpactDirection.BULLISH)
    bear = sum(s for d, s in independent if d.direction is ImpactDirection.BEARISH)
    agree_side = ImpactDirection.BULLISH if bull >= bear else ImpactDirection.BEARISH
    winning = max(bull, bear)
    losing = min(bull, bear)
    agreeing = sum(1 for d, _ in independent if d.direction is agree_side)
    conflicting = sum(
        1 for d, _ in independent
        if d.direction in (ImpactDirection.BULLISH, ImpactDirection.BEARISH)
        and d.direction is not agree_side
    )

    total = winning + losing
    if total <= 0:
        return ConvergenceResult(
            0.0, ImpactDirection.UNCERTAIN, (), 0, 0, tuple(collapsed),
            "no directional evidence",
        )

    # --- Step 3: score ---
    # Dominance: how one-sided the evidence is (0.5 = balanced, 1.0 = unanimous).
    dominance = winning / total
    # Breadth: independent agreeing domains, saturating (diminishing returns).
    breadth = min(1.0, agreeing / 4.0)
    # Mean adjusted strength of the agreeing side (0..100), independent entries only.
    agree_strengths = [s for d, s in independent if d.direction is agree_side]
    mean_strength = sum(agree_strengths) / len(agree_strengths) if agree_strengths else 0.0
    # Blend: strength scaled by dominance and breadth. Conflicting evidence lowers it
    # via dominance (< 1 when the other side has weight).
    raw = mean_strength * (0.5 + 0.5 * dominance) * (0.5 + 0.5 * breadth)
    score = _clamp(raw, 0.0, 100.0)

    # Retain ALL entries (independent + collapsed) for explainability (§38).
    contributing = tuple(
        DomainEvidence(
            domain=d.domain,
            strength=_clamp(s, 0.0, 100.0),
            rationale=d.rationale or f"{d.domain.value} {d.direction.value}",
        )
        for d, s, _ind in effective
    )
    detail = (
        f"agree={agreeing} conflict={conflicting} dominance={dominance:.2f} "
        f"breadth={breadth:.2f} mean_strength={mean_strength:.1f}"
    )
    return ConvergenceResult(
        score=round(score, 2),
        direction=agree_side if winning > losing else ImpactDirection.UNCERTAIN,
        contributing=contributing,
        agreeing_domains=agreeing,
        conflicting_domains=conflicting,
        collapsed_groups=tuple(collapsed),
        detail=detail,
    )
