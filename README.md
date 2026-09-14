# Trading Command

**Repo:** `seiertech/2026_Trader` · **Spec:** [TC-SPEC-001 v1.3](docs/build/TC-SPEC-001-master-spec.md) (BUILD AUTHORITY) · **Mode:** SHADOW (mandatory initial mode)

An evidence-driven market-intelligence, opportunity-discovery, trading-research and
*selective* autonomous-execution platform. It observes markets and the world around
them, builds relationships between events and tradable assets, identifies where
independent evidence converges, tests those situations against historical experience,
applies AI reasoning and adversarial challenge, controls risk **deterministically**,
simulates trades in Shadow, measures what actually happens, and learns where a genuine
trading edge exists.

> **Prime Directive (§0):** V1 exists to **prove or disprove tradable edge — not to
> make money.** There is **no return target.** Proving that *no* edge exists is a
> *successful* V1 outcome, provided the disproof is statistically sound. Any pressure
> — human or AI — to chase returns, trade more, or promote to live before edge is
> validated out-of-sample and net of costs is a **defect**. This sits in the same
> un-overridable tier as the crypto prohibition.

> Trading Command is **not** an "ask AI what to buy" system. `NO OPPORTUNITY` is a
> valid and desirable state. The system earns the right to trade real capital through
> evidence.

## Non-negotiables (from the spec)

- **Prime Directive (§0, `TC-ADR-017`):** prove/disprove edge; **no capital return target**; promotion gated by proof, never by profit or schedule. Un-overridable.
- **Crypto is PROHIBITED** — enforced in deterministic policy code; AI cannot override it (`TC-ADR-006`).
- **SHADOW is mandatory** before any live trading; the system defaults to SHADOW and **fails closed** (`TC-ADR-015`, §104).
- **AI cannot override deterministic risk** (`TC-ADR-012`). AI reasons over evidence; the Risk Engine controls capital.
- **Separation of concerns:** INTELLIGENCE / DECISION / RISK / EXECUTION are decoupled. Eightcap and MT5 are *infrastructure*, reached only through provider adapters (`TC-ADR-010`).
- **No look-ahead:** Evidence Packs contain only what was known at the decision timestamp (§89, §126). Original evidence/decisions are immutable (`TC-ADR-018`).
- **£250 is a reference unit** for risk/R/expectancy — *not* a capital base to compound and *not* a target (`TC-ADR-016`). No dashboard, agent or operator may display or act on a growth target (§75).

## Golden Path (first vertical, built before any breadth — §123)

```
XAUUSD:  MT5 price → quant → news/event → relationship graph → convergence →
         opportunity → evidence pack → historical analogue → AI → critic →
         decision → risk → SHADOW trade → monitor → exit → outcome → learning →
         dashboard
```

## Repository layout

Follows TC-SPEC-001 Part XXIV (+ v1.1 §157 additions, v1.2 `apps/cli/`). See the spec
for the full tree. Top level: `apps/` (runtime, api, dashboard, cli) · `packages/`
(domain + engines) · `agents/` · `providers/` · `strategies/` · `config/` · `data/` ·
`research/` · `tests/` · `docs/`.

## Build status

Vertical + gated build (§107). Current phase and open decisions are tracked in:

- **[docs/build/OPEN-QUESTIONS.md](docs/build/OPEN-QUESTIONS.md)** — owner rulings required (incl. the MT5-on-Windows constraint and the runtime-language decision).
- **docs/decisions/** — Architectural Decision Records.

| Phase | Scope | Status |
|------:|-------|--------|
| 0 | Foundation: domain model, config, database, logging, tests, dashboard shell | 🚧 in progress |
| 1 | MT5 live read (via provider; needs Windows MT5 host — see OQ-2) | ⏳ |
| 2–12 | Historical store → quant → news → graph → convergence → analogues → AI → shadow → learning → control plane | ⏳ |
| 13–14 | Paper → limited live (gated, evidence-earned) | ⏳ |

## Secrets

Never commit credentials. Copy `.env.example` → `.env` (git-ignored) and populate.
See §128–§129.

## License

Proprietary — Seiertech. All rights reserved.
