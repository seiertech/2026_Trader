# Build Phase Status

Vertical, gated build (§107). Broad directory scaffolding exists (Part XXIV tree) but
empty dirs carry only `.gitkeep` — they are NOT half-built modules. We fill them along
the XAUUSD golden path (§123, §161), not up front (v1.1 directive: broad scope is not
permission to scaffold dozens of incomplete modules).

| Phase | Scope | Status |
|------:|-------|--------|
| 0 | Foundation: domain model, config, database, logging, tests, dashboard shell | ✅ **done** |
| 1 | MT5 live read (needs Windows host — TC-ADR-032) | 🟡 contracts + replay provider done; live Mt5 adapter pending Windows host |
| 2 | Historical market store: canonical bars, aggregation, replay | 🟡 replay + aggregation done; DuckDB persistence + full history pending |
| 3 | Quant: regime, trend, momentum, structure, volatility | 🟡 indicators + regime classifier done; specialist depth pending |
| 10 | Shadow: sizing, cost model, simulated execution, metrics | 🟡 simulator + metrics done; full portfolio/session modelling pending |
| 4 | News intelligence | ⏳ |
| 5 | Entity & relationship graph | ⏳ |
| 6 | Market leaders | ⏳ |
| 7 | Convergence | ⏳ |
| 8 | Historical analogues | ⏳ |
| 9 | AI (abstraction, specialists, critic) | ⏳ |
| 10 | Shadow (£250 virtual account, simulated execution, cost modelling) | ⏳ |
| 11 | Learning (forward labels, agent/strategy/filter contribution) | ⏳ |
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
