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
