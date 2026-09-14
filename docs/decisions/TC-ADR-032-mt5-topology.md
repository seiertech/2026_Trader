# TC-ADR-032 — MT5 host topology & Shadow data provider

**Status:** ACCEPTED · **Date:** 2026-09-14 · **Supersedes OQ-2**

## Context

TC-ADR-004 fixes MetaTrader 5 as the V1 market and execution gateway. The official
`MetaTrader5` Python package is a **Windows-only binary** that communicates with a
locally-running MT5 *terminal* via local IPC. There is no cloud/REST trading API for
retail Eightcap MT5 accounts. Community "MT5-on-Linux" options all run the real
Windows terminal under Wine or in a Windows VM and proxy to it — they relocate the
Windows dependency, they do not remove it.

The build environment (and any Linux server) therefore cannot host the terminal
directly.

## Decision

1. The **`market-data`** and **`execution-engine`** packages depend only on the
   abstract `MarketDataProvider` / `ExecutionProvider` contracts (§96), never on the
   `MetaTrader5` package directly.
2. **Shadow (the mandatory initial mode, §79) runs against a deterministic
   replay/synthetic provider** — real live MT5 is NOT required to prove the XAUUSD
   golden path in Shadow. This is faithful to §79 (simulated execution, no broker
   orders) and enables the whole vertical to be built and tested on Linux.
3. The concrete **`Mt5MarketDataProvider` / `Mt5ExecutionProvider`** is a thin
   adapter that runs **where the MT5 terminal lives** — a Windows host/VM the operator
   controls — reached over a small local bridge (RPyC/socket). It is a separate
   deployable so the Linux-hosted "brain" and the Windows-hosted MT5 edge stay
   decoupled (this is exactly TC-ADR-004's "MT5 is infrastructure" principle).
4. Live MT5 read (Phase 1) and any live execution require that Windows host to exist
   and be reachable. Until then the system uses the replay/synthetic provider.

## Consequences

- No spec deviation: this is the provider-abstraction and fail-closed design the spec
  already mandates (Part XXXI §3, §7). No ADR was strictly required, but the physical
  dependency is important enough to record.
- Operator responsibility: a Windows host/VM running the Eightcap MT5 terminal must be
  provisioned before Phase 1 live data. Confirmed acceptable by the owner.
- Secrets for MT5 live only on that host / in env (§128–§129); never committed.
