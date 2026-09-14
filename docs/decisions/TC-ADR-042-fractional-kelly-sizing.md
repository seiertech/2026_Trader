# TC-ADR-042 — Fractional Kelly position sizing

**Status:** ACCEPTED · **Date:** 2026-09-14 · **Source:** TC-CR-001 · **Maps to:** CR's "TC-ADR-028 (v1.3)"

## Context

The Risk Engine (§73–77) defines risk *ceilings* but not the *method* for choosing
per-trade risk beneath them (§76 gives only a 1% research default). TC-CR-001
specifies **fractional Kelly** as that method. Kelly is the growth-optimal fraction to
risk given a known edge, and yields a positive size only when edge is positive — which
matches the Prime Directive (§0) and "NO OPPORTUNITY is valid" (§3). It is adopted
deliberately fractional and capped because Trading Command *estimates* `p` and `b`
from finite, potentially overfit samples; full Kelly would systematically over-bet
whenever the measured edge exceeds the true edge.

## Decision

Position sizing SHALL use **fractional Kelly** (default quarter-Kelly, `KELLY_FRACTION
= 0.25`, config-driven, never > 0.50), computed **only from validated out-of-sample
statistics** that satisfy the §75 promotion gates and §87 Shadow validation. It is
**always capped by the deterministic §77 risk ceilings and never raises risk above
them**. It defaults to **zero or the §76 fixed minimal research risk** when edge is
unproven or non-positive. Kelly is a ceiling and a discipline, never a mandate to
increase risk. Implemented as §77a.

Key rules (all deterministic policy tier — AI cannot override):
- `f* = (b·p − q) / b`; `f_applied = KELLY_FRACTION × f*`;
  `risk_per_trade = min(f_applied, MAX_RISK_PER_TRADE)` and all other §77 controls.
- **Positive-edge gate:** `f* ≤ 0 → NO_POSITIVE_EDGE → size 0 → no trade`.
- **Unvalidated → fallback:** missing/stale/below-minimum `p`,`b`,`sample_size`
  ⇒ Kelly NOT used ⇒ fixed minimal research risk or zero (fail closed).
- **Estimation safety:** size against a conservative lower-confidence-bound estimate,
  not the point estimate, so error biases toward under-betting.
- **Auditability:** record `p_used`, `b_used`, `sample_size`, `kelly_fraction`,
  `f_star`, `f_applied`, `binding_constraint`, `mode` in the immutable Evidence Pack.
- **Mode independence:** Kelly inputs computed per mode; SHADOW stats never size
  PAPER/LIVE and vice versa.

## Consequences

- Additive: implemented inside the Risk Engine as §77a; §73–77 ceilings and the mode
  state machine are unchanged.
- Kelly runs AFTER the Decision Engine proposes direction and BEFORE order
  construction — it sets size, not direction.
- Because nothing in the system is validated out-of-sample yet, Kelly currently
  **falls back to the fixed §76 research risk** everywhere. This is the CR working as
  intended, not a no-op; Kelly activates only once a strategy passes §75/§87.
- ADR numbering: uses TC-ADR-042 (next free in the resolved register) rather than the
  CR's "028", which already denotes a v1.1 decision here. Mapped in REGISTER.md.
