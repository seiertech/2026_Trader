# TC-ADR-034 — Build the spec tree at the repository root

**Status:** ACCEPTED · **Date:** 2026-09-14 · **Supersedes OQ-4**

## Context

The spec's Part XXIV shows a project root named `trading-command/`. The actual GitHub
repository is `seiertech/2026_Trader`.

## Decision

The spec's directory tree is built **directly at the root of `2026_Trader`**
(`apps/`, `packages/`, `agents/`, `providers/`, `strategies/`, `config/`, `data/`,
`research/`, `tests/`, `docs/`). No `trading-command/` wrapper directory is created.
Renaming the GitHub repo is optional and cosmetic and is NOT done as part of the
build.

## Consequences

- Paths in the spec map 1:1 onto repo paths minus the leading `trading-command/`.
- No functional impact. Recorded for traceability between spec paths and repo paths.
