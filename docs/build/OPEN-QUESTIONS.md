# Trading Command — Open Questions & Owner Rulings Required

These are decisions that TC-SPEC-001 v1.2 does not resolve unambiguously, or that
have a real-world constraint the spec did not anticipate. Per **TC-SPEC-001 Part XXXI**,
material deviations require an explicit ADR. Nothing below has been silently decided.

Status legend: 🔴 BLOCKS phase · 🟠 needs ruling, has safe default · 🟢 resolved.

---

## OQ-1 — 🟠 Duplicate ADR numbers (spec defect in the change-control mechanism)

The v1.1 expansion defines **TC-ADR-021 … TC-ADR-030**. The v1.2 addendum then
defines a *second* block of decisions also numbered **TC-ADR-021 … TC-ADR-027**.
So `TC-ADR-021` refers to two different things ("V1 intelligence coverage is global"
in v1.1, and "Performance is a first-class domain" in v1.2).

This matters because the spec's own governance (Part XXXI) says changes require "an
explicit ADR" — an ADR register with colliding identifiers cannot serve as an audit
trail, which is the one thing it exists to do.

**Interim decision (reversible):** the v1.2 block is referenced internally as
**TC-ADR-P01 … TC-ADR-P07** so every identifier is unique. The verbatim spec text
keeps its original numbers.

**Ruling needed:** Do you want (a) the v1.2 block renumbered to **TC-ADR-031…037**
(chronological, my recommendation), (b) keep the P01…P07 scheme, or (c) something
else? Purely a labelling decision — no code depends on it yet.

> **v1.3 update:** v1.3 restates TC-ADR-016 and TC-ADR-017 (reference unit / no
> return target) but does NOT touch the 021–027 collision, so this question is still
> open. v1.3's Precedence clause (v1.3 > v1.2 > v1.1 > v1.0) governs *section*
> conflicts but does not renumber ADRs.

---

## OQ-2 — 🔴 MetaTrader 5 cannot run natively on this Linux sandbox / on a server

This is the one hard blocker, and it's worth being blunt about because it shapes the
whole runtime topology.

**The constraint:** The official `MetaTrader5` Python package is a **Windows-only
binary wheel**. It talks to a locally-running MT5 *terminal* over local IPC — there
is no REST/cloud API. It does not install on Linux, and Eightcap does not expose an
independent HTTP trading API for retail MT5 accounts. (Confirmed against PyPI and the
MT5 docs; the community Linux options — `mt5linux`, `pymt5linux`, socket bridges —
all work by running the *actual Windows terminal under Wine or in a Windows VM* and
proxying to it. They do not remove the Windows dependency; they relocate it.)

**What this means:** Trading Command's *intelligence, convergence, decision, risk,
shadow and learning* engines (Phases 0, 2–12) have **no MT5 dependency** and run
anywhere. Only **Phase 1 (live MT5 read)** and eventual live execution need a machine
with the MT5 terminal — i.e. a Windows box or a Windows VM you control, running the
terminal, reachable by the runtime.

**This does not block the build.** The spec is architected exactly for this: §96
`ExecutionProvider` interface, §23/§27 provider adapters, §79 SHADOW as mandatory
initial mode with *simulated* execution and no broker orders. So the plan is:

1. Define the `MarketDataProvider` / `ExecutionProvider` contracts (§96) now.
2. Build the whole vertical against those contracts with a **deterministic
   replay/synthetic provider** for Shadow — real live MT5 is not required to prove
   the XAUUSD golden path in Shadow.
3. Implement the concrete `Mt5ExecutionProvider` as a thin adapter that runs where
   the terminal lives, reached over a small local bridge (RPyC/socket). Ship it as
   its own deployable so the Linux-hosted brain and the Windows-hosted MT5 edge stay
   decoupled — which is exactly TC-ADR-004's "MT5 is infrastructure" principle.

**Ruling needed:** Confirm you have (or can stand up) a **Windows host / VM running
the Eightcap MT5 terminal** for the live-data phase. Until then Phase 1 uses the
replay/synthetic provider. No ADR is required — this is faithful to the spec — but I
want you to know the physical dependency exists before we reach Phase 1.

---

## OQ-3 — 🟠 Runtime language: spec shows TypeScript interfaces but mandates a Python-heavy quant/data stack

The spec's interface snippets (§27, §41, §56, §96, §152, §153) are TypeScript, and
the dashboard is explicitly React/Next.js (§97). But the core is a quant + historical
+ statistical + ML-adjacent research engine (Parts VII, XI, XII, XIX, XX), the MT5
integration is Python-first, and free intelligence tooling (GDELT clients, feed
parsing, dataframes) is strongest in Python.

**Interim decision (reversible):** treat the TS interfaces as *contract
specifications* (language-neutral), and build the **runtime/engines in Python**
(3.12), with the **dashboard in Next.js/TypeScript** per §97 and the **CLI in
Python** per v1.2. The two talk over an internal API (`apps/api/`, which the spec
already lists). This is the lowest-friction reading and keeps every named repo folder.

**Ruling needed:** Confirm **Python engines + TS/Next dashboard**, OR tell me you
want an all-TypeScript monorepo (Node runtime, e.g. `mathjs`/`danfojs` for quant).
I recommend the former; the quant/historical/statistics burden is where this system
lives and Python is materially stronger there. This choice is expensive to reverse
after Phase 3, cheap now.

---

## OQ-4 — 🟠 Repository name & structure root

The spec's Part XXIV shows a `trading-command/` project root. The actual GitHub repo
is **`seiertech/2026_Trader`** and it is empty.

**Interim decision:** build the spec's tree **at the repository root** of
`2026_Trader` (i.e. `apps/`, `packages/`, … live directly in the repo), rather than
nesting a `trading-command/` folder inside it. Renaming the GitHub repo to
`trading-command` is optional and cosmetic.

**Ruling needed:** Fine to build at repo root of `2026_Trader`? Or do you want the
repo renamed / the tree nested under `trading-command/`?

---

## OQ-5 — 🟢 Branch & commit policy (resolved from standing instruction)

Standing instruction on file: push directly to `main`, no feature branches or PRs
unless explicitly asked. Current branch is `main` (repo default). Committing straight
to `main`. No ruling needed — noted here for the audit trail.
