# TC-ADR-032 — MT5 host topology & Shadow data provider

**Status:** ACCEPTED · **Date:** 2026-09-14 · **Updated:** 2026-09-14 (host confirmed) · **Supersedes OQ-2**

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
   adapter that runs **where the MT5 terminal lives** — a **dedicated Windows machine**
   the operator controls (CONFIRMED, see below) — reached over a small local bridge
   (RPyC/socket). It is a separate deployable so the Linux-hosted "brain" and the
   Windows-hosted MT5 edge stay decoupled (this is exactly TC-ADR-004's "MT5 is
   infrastructure" principle).
4. Live MT5 read (Phase 1) and any live execution require that Windows machine to be
   running and reachable. Until then the system uses the replay/synthetic provider.

## Host: CONFIRMED — dedicated Windows machine

The operator has confirmed a **dedicated Windows machine** will host the MT5 terminal
(not a Wine/VM workaround). This removes the OQ-2 uncertainty. Operating requirements
that follow from MT5 being a desktop terminal:

- **Always-on for continuous observation.** MT5 is a desktop app; if the machine
  sleeps or the terminal closes, the live feed stops. Continuous SHADOW observation
  wants this machine effectively always-on. A dedicated box suits this well.
- **Credentials are local to that machine only.** Eightcap/MT5 login lives in the
  Windows machine's environment / secret store, never in the repo (§128–§129). The
  Linux brain never sees broker credentials.
- **Network path between brain and edge must be controlled.** The two communicate
  over a socket/RPC bridge. Same-LAN is simplest; if the brain is hosted elsewhere the
  link MUST be locked down — it is a channel that can eventually place real orders, so
  it is treated as security-sensitive (fail closed on loss of the link, §104).
- **Only relevant from Phase 1 onward.** Shadow is fully buildable/testable on the
  replay/synthetic provider first; the Windows machine is not a prerequisite to begin.

## Consequences

- No spec deviation: this is the provider-abstraction and fail-closed design the spec
  already mandates (Part XXXI §3, §7). No ADR was strictly required, but the physical
  dependency is important enough to record.
- Operator responsibility: a **dedicated Windows machine** running the Eightcap MT5
  terminal is provisioned before Phase 1 live data. **Confirmed by the owner
  (2026-09-14).**
- Secrets for MT5 live only on that host / in env (§128–§129); never committed.
