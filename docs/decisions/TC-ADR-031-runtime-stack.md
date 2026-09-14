# TC-ADR-031 — Runtime language & stack

**Status:** ACCEPTED · **Date:** 2026-09-14 · **Supersedes OQ-3**

## Context

TC-SPEC-001 expresses its contracts as TypeScript interfaces (§27, §41, §56, §96,
§152, §153) and mandates a React/Next.js dashboard (§97). But the core of the system
is a quantitative + historical + statistical research engine (Parts VII, XI, XII,
XIX, XX), the MT5 integration is Python-first (the official `MetaTrader5` package is
Python), and the free-first intelligence tooling (GDELT, feed parsing, dataframes) is
strongest in Python. §55 further mandates that price/statistics/indicator/position-
sizing math be deterministic software, not LLM — i.e. numerically serious code.

## Decision

- **Engines / runtime / API / CLI:** **Python 3.12.**
- **Dashboard (`apps/dashboard/`):** **Next.js + TypeScript**, per §97 (unchanged).
- **The TypeScript interfaces in the spec are treated as language-neutral contract
  specifications.** They are re-expressed as typed Python (dataclasses / Pydantic /
  Protocols) in `packages/domain`, and — where the dashboard needs them — as
  TypeScript types generated or hand-mirrored from the same source of truth.
- Python engines expose state to the dashboard over the internal API
  (`apps/api/`, already in the spec tree).

## Consequences

- Quant, historical-analogue, statistics and MT5 code live where the ecosystem is
  strongest; no numeric work is forced through a JS runtime.
- Two languages in the repo. Mitigated by a single contract source (`packages/domain`)
  and a thin, typed API boundary. The dashboard never re-implements domain logic.
- Does not touch any spec guardrail (Part XXXI). Provider abstraction, separation of
  concerns, and deterministic-over-LLM are all preserved and in fact reinforced.
