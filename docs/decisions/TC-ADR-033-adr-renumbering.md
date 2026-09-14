# TC-ADR-033 — Resolve the duplicate ADR numbering (v1.1 vs v1.2)

**Status:** ACCEPTED · **Date:** 2026-09-14 · **Supersedes OQ-1**

## Context

The v1.1 expansion defined **TC-ADR-021 … TC-ADR-030**. The v1.2 addendum then
defined a *second* block also numbered **TC-ADR-021 … TC-ADR-027**. An ADR register
whose identifiers collide cannot serve as an audit trail — the one thing it exists to
do. The verbatim spec text keeps its original numbering (it is a faithful capture);
the collision must be resolved for the *working* register.

## Decision

Session build decisions already occupy TC-ADR-031 (stack), TC-ADR-032 (MT5), this
entry TC-ADR-033 (renumbering policy), and TC-ADR-034 (repo layout). The v1.2
performance/control-plane block is therefore **renumbered TC-ADR-035 … TC-ADR-041**
in the working register, in the order it appears in v1.2:

| v1.2 original | Working number | Subject |
|---|---|---|
| TC-ADR-021 | **TC-ADR-035** | Performance, P&L & attribution are first-class domains |
| TC-ADR-022 | **TC-ADR-036** | Primary dashboard is a trading/intelligence cockpit |
| TC-ADR-023 | **TC-ADR-037** | Separate performance ledgers per mode (SHADOW/PAPER/LIVE) |
| TC-ADR-024 | **TC-ADR-038** | Every trade supports multi-dimensional attribution |
| TC-ADR-025 | **TC-ADR-039** | Both a web Control Plane and a CLI/operator console |
| TC-ADR-026 | **TC-ADR-040** | Strategy/config versions retained with performance records |
| TC-ADR-027 | **TC-ADR-041** | Measure contribution of strategies/agents/evidence/filters/critic |

This document (TC-ADR-033) records the renumbering policy itself and is the anchor
entry. The individual decisions are catalogued in `docs/decisions/REGISTER.md`.

The v1.1 decisions (TC-ADR-021 … TC-ADR-030) keep their numbers — they were first and
are uncontested.

## Consequences

- Every ADR identifier in the working register is unique. The spec's own change-
  control mechanism becomes usable.
- `docs/decisions/REGISTER.md` is the authoritative index mapping working numbers to
  subjects and to spec sections. When in doubt, the register wins over prose.
- Purely a labelling decision; no code depends on ADR numbers.
