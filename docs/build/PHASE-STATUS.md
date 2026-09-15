# Build Phase Status

Vertical, gated build (§107). Broad directory scaffolding exists (Part XXIV tree) but
empty dirs carry only `.gitkeep` — they are NOT half-built modules. We fill them along
the XAUUSD golden path (§123, §161), not up front (v1.1 directive: broad scope is not
permission to scaffold dozens of incomplete modules).

| Phase | Scope | Status |
|------:|-------|--------|
| 0 | Foundation: domain model, config, database, logging, tests, dashboard shell | ✅ **done** |
| 1 | MT5 live read (needs Windows host — TC-ADR-032) | 🟡 contracts + replay provider done; live Mt5 adapter pending Windows host |
| 2 | Historical market store: canonical bars, aggregation, replay | 🟡 replay + aggregation + DuckDB persistence done; full history pending |
| 3 | Quant: regime, trend, momentum, structure, volatility | 🟡 indicators + regime classifier done; specialist depth pending |
| 15 | Decision Engine (§68-70): LONG/SHORT/WAIT/REJECT, WAIT first-class | ✅ deterministic engine done |
| 16 | Strategies (§71-72): trend/momentum/mean-reversion/vol-expansion + registry | 🟡 4 research families + regime eligibility done; more pending |
| — | Risk Engine gate (§77): all controls enforced in code | ✅ deterministic gate done |
| — | Adversarial Critic (§67): deterministic VETO/CAUTION/NO_OBJECTION | ✅ done (AI critic Phase 9) |
| 10 | Shadow: sizing, cost model, simulated execution, metrics | 🟡 simulator + metrics done; full portfolio/session modelling pending |
| 4 | News intelligence | ⏳ |
| 5 | Entity & relationship graph | ⏳ |
| 6 | Market leaders | ⏳ |
| 7 | Convergence | ⏳ |
| 8 | Historical analogues | ⏳ |
| 9 | AI (abstraction, specialists, critic) | ⏳ |
| 10 | Shadow (£250 virtual account, simulated execution, cost modelling) | ⏳ |
| 11 | Learning (forward labels, agent/strategy/filter contribution) | 🟡 forward-outcome labelling + per-cell attribution + small-sample honesty done; agent/filter contribution pending |
| 12 | Control plane (full cockpit, performance, explainability) | ⏳ |
| 13 | Paper | ⏳ |
| 14 | Limited live (gated, evidence-earned) | ⏳ |

## Phase 0 — what was built

**Packages (Python 3.12, TC-ADR-031):**
- `packages/domain` (`tc_domain`) — taxonomy enums, `Instrument` + the 8-instrument
  canonical universe, `Opportunity` / `EvidencePack` / `Decision` / hypothesis value
  objects (immutable where the spec demands, §90), UTC time helpers (§125), and the
  **deterministic policy tier** (`policy.py`): crypto prohibition (§7, TC-ADR-006) and
  no-return-target (§0, §75, TC-ADR-017).
- `packages/config` (`tc_config`) — typed YAML loader; applies the policy tier at the
  single startup entry point and fails closed (§104).
- `packages/observability` (`tc_observability`) — structured UTC JSON logging (§105),
  fail-closed health registry (§103/§104), append-only audit log (§105).
- `packages/database` (`tc_database`) — append-only, immutable Experience Store
  (§48/§88/§90) with an in-memory implementation; DuckDB adapter is optional.

**Config:** `config/runtime.yaml` (SHADOW default, no target), `config/risk.yaml`
(all 17 controls, §77), `config/instruments.yaml` (8 canonical instruments).

**Apps:** `apps/dashboard` (Next.js shell — MODE/health/kill-switch + Prime Directive),
`apps/cli` (`tc status|health|markets`, working; dangerous commands stubbed).

**Tests:** 33 unit tests, all passing — crypto prohibition, no-return-target,
config load + fail-closed, 17 risk controls, 8 instruments none-live, domain
immutability, naive-datetime rejection.

## XAUUSD Shadow golden-path slice — what was built (vertical, §123)

The first end-to-end vertical, running on the replay provider (no Windows/MT5 needed):

- `packages/market-data` (`tc_market_data`) — `MarketDataProvider`/`ExecutionProvider`
  contracts (§96); `ReplayMarketDataProvider` with strict no-look-ahead (§126);
  calendar-aligned timeframe aggregation (§35).
- `packages/quant-engine` (`tc_quant`) — deterministic indicators (SMA/EMA/RSI/MACD/
  ATR/ADX/ROC/Bollinger, §33) and a regime classifier (§34); pure math, no AI (§55).
- `packages/shadow-engine` (`tc_shadow`) — cost model, risk-based sizing, virtual £250
  account with a §85 affordability guard, trade simulator, and performance metrics
  (win rate, profit factor, expectancy in cash **and R**, MFE/MAE, drawdown; §84–§87).
- `apps/runtime` (`tc_runtime`) — orchestrates the golden path end to end: replay →
  aggregate → regime → strategy setup → risk-sized shadow trade → outcome → metrics.
- `data/reference/XAUUSD_1m_sample.csv` — deterministic synthetic sample (flagged
  synthetic, not real data). Real history arrives via the Windows Mt5 provider later.
- CLI: `tc golden-path` runs the whole pipeline and prints a report.

**Honest results on the sample:** the mean-reverting sample reads as RANGE, so the
trend/breakout demo strategy finds few setups; at 1h the one trade lost (-1R) and the
report flags non-positive expectancy as a *valid* outcome (§0/§130). At 15m the §85
affordability guard correctly rejects every setup — a £250 account cannot hold the
position tight intraday stops demand. No edge is claimed (TC-ADR-020).

**Tests:** 68 total (64 unit + 4 golden-path integration), all passing; ruff clean.

## Persistence — DuckDB Experience Store (§48, §88, §90)

The Experience Store is now durable, so run results survive for later learning:

- `packages/database` (`tc_database`) — `DuckDBExperienceStore` implements the existing
  `ExperienceStore` protocol; append-only and immutable **at the DB layer** (re-writing
  an id is rejected; no update/delete methods exist — removing auditability needs an
  ADR). UTC ISO-8601 timestamps, JSON payloads, insertion order preserved.
- `tc_database.trades` — serialises a `SimulatedTrade` ↔ `ExperienceRecord` exactly
  (Decimals as strings, no float drift), carrying the §77a sizing audit; `persist_trade`
  / `load_trades` helpers keep the shadow engine storage-agnostic.
- Runtime: `run_golden_path(..., store=...)` persists each trade. CLI:
  `tc golden-path --persist run.duckdb` writes to a file; reopening reconstructs the
  trades exactly.

**Tests:** 94 total (+9: DuckDB append/get/all/count, re-write rejected, no update/
delete, UTC round-trip, survives reopen, exact trade round-trip, duplicate rejected,
golden-path→DuckDB→reload). ruff clean.

## Fractional Kelly sizing (§77a, TC-CR-001, TC-ADR-042)

`packages/risk-engine` (`tc_risk`): fractional Kelly (quarter-Kelly default, capped
0.50), positive-edge gate, §77 ceiling clamp (never raises), unvalidated→fixed-risk
fallback, conservative lower-bound estimate, full audit record, per-mode inputs. Wired
into the simulator; the demo strategy is unvalidated so it correctly falls back to the
fixed 1% research risk.

## Learning / attribution — Phase 11 slice (§49, §50, §53, §91)

Turns accumulated experience into knowledge about where edge exists (the Prime
Directive's purpose, §0/§130):

- `packages/learning-engine` (`tc_learning`):
  - `labelling.py` — forward-outcome labelling (§49): for a decision at time T,
    records the market's return at 5m/15m/30m/1h/4h/1d, oriented to the opportunity's
    bias. Horizons beyond the data are `None`, never fabricated. Keyed to the decision
    instant (no leak-back, §89).
  - `attribution.py` — per-cell attribution (§91): groups outcomes by
    instrument/regime/direction (etc.) and reports sample size, win rate, expectancy
    in R (the headline), profit factor. **Small-sample honesty (§53):** cells below
    30 trades are flagged WEAK; adequate cells are only PROVISIONAL — never
    auto-"proven" (that needs the §75 gates).
- `tc_database.labels` — persists every opportunity's forward label, **traded AND
  rejected** (§50: rejected candidates must be measured, so we can later ask whether
  the filters/critic improved expectancy). Immutable/append-only like all experience.
- Runtime forward-labels every opportunity and persists rejections. CLI: `tc
  golden-path --persist run.duckdb` records trades + labels; `tc attribution
  run.duckdb --by instrument,direction` prints the per-cell table.

**Demonstrated:** at 15m on the sample, all 55 opportunities are rejected by the §85
affordability guard — and all 55 are still forward-labelled and stored (§50 working).
At 1h, the single trade is flagged ⚠ WEAK in attribution (n=1 ≪ 30) — the system
refuses to treat one result as evidence of edge (§53).

**Tests:** 107 total (+13: labelling per-horizon + bias orientation + missing→None,
attribution grouping/expectancy/sorting, WEAK vs PROVISIONAL, rejected-opportunity
persistence). ruff clean.


## Decision / Risk / Challenge middle — full OODA pipeline (§67, §68-70, §77)

The pipeline no longer shortcuts strategy→shadow. Every opportunity flows through the
full middle before execution:

    eligible strategies (§72) → adversarial critic (§67) → risk gate (§77)
      → decision engine (§68-70) → only LONG/SHORT → shadow simulator

- `packages/risk-engine/tc_risk/gate.py` — deterministic §77 gate: APPROVE / REDUCE
  (cap to headroom) / REJECT (fail closed) with reason codes. Enforces KILL_SWITCH,
  MANDATORY_STOP, STALE_DATA_BLOCK, MIN_REWARD_RISK, MAX_SPREAD, MAX_POSITIONS,
  MAX_CONSECUTIVE_LOSSES, MAX_DAILY_LOSS, MAX_OPEN_RISK, MAX_INSTRUMENT_EXPOSURE.
  Never raises risk.
- `packages/decision-engine/tc_decision/engine.py` — Decision Engine (§68-70):
  precedence VETO→REJECT, gate REJECT→REJECT, expired→REJECT, unclear→WAIT,
  CAUTION/REDUCE→WAIT, else LONG/SHORT. WAIT first-class (§70). Immutable Decision
  with plain-English + detailed explainability (§101).
- `packages/decision-engine/tc_decision/critic.py` — deterministic Adversarial Critic
  (§67): VETO (stale/blackout/no-stop/reward-risk) / CAUTION (wide spread, low
  convergence, loss streak, ineligible regime) / NO_OBJECTION. AI critic adds on top
  in Phase 9, never removes these.
- `strategies/tc_strategies` — 4 regime-eligible research families (§71-72) +
  registry; no strategy presumed profitable (TC-ADR-020).
- Runtime threads portfolio/session state through the gate+critic, tallies the
  decision outcomes (§69), and stamps strategy+regime on trades for attribution (§91).

**Demonstrated at 15m:** 133 opportunities across 4 strategies → 10 LONG/SHORT, 123
WAIT; all forward-labelled by strategy; every one measured (§50).

**Tests:** 160 total (risk gate 14, decision 11, critic 11, strategies 17, + prior).
ruff clean.


## Intelligence conveyor — brain-side build-out (no live data)

A full conveyor pass built the intelligence and control layers deterministically, on
the replay/synthetic data, with no Windows/MT5 dependency. **214 tests, ruff clean.**

| Package | Spec | What it does |
|---|---|---|
| `tc_convergence` | §36-39, §150 | evidence-domain 0-100 score; independence + correlated-collapse; retains components |
| `tc_evidence` | §43, §90 | immutable Evidence Pack at decision time; pack_id threaded through decision + trade |
| `tc_graph` | §18, §21-22, §143-146 | typed entities + temporal directional edges; event→instrument propagation w/ per-hop confidence decay + inverse polarity |
| `tc_themes` | §20, §147 | durable themes w/ lifecycle (EMERGING…RESOLVED) from evidence/velocity/confirmation; theme→instrument via graph |
| `tc_leaders` | §19, §148 | config baskets; a correlated basket move = ONE factor (not N), tagged for convergence collapse |
| `tc_news` | §24, §27, §28-32 | IntelligenceProvider adapters (offline FixtureProvider); dedup (5 orgs → 1 event), velocity, novelty, classification |
| `tc_historical` | §51-53 | analogue matching + §52 outcome stats; §53 small-sample honesty (8/10 → WEAK, wide CI) |
| `tc_ai` | §54-57 | AiProvider abstraction + routing tiers; advisory-only assessments; **cannot** override risk (TC-ADR-012) |
| dashboard cockpit | §86, §98-102 | `tc snapshot` → JSON; Next.js renders cockpit / funnel / rejection / performance |

Config seeds added: `relationships.yaml`, `themes.yaml`, `companies.yaml`.

**Doctrine held throughout:** deterministic-first (§55), provider abstraction
(TC-ADR-010), no-look-ahead (§89/§126), small-sample honesty (§53), correlated-evidence
collapse (§39/§148), AI advisory-only (§55/TC-ADR-012), and the Prime Directive —
no return target (§0). Live MT5 data (Windows edge, ADR-032) remains the one gated
dependency, deferred by design.
