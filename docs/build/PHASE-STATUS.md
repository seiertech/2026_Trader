# Build Phase Status

Vertical, gated build (§107). Broad directory scaffolding exists (Part XXIV tree) but
empty dirs carry only `.gitkeep` — they are NOT half-built modules. We fill them along
the XAUUSD golden path (§123, §161), not up front (v1.1 directive: broad scope is not
permission to scaffold dozens of incomplete modules).

| Phase | Scope | Status |
|------:|-------|--------|
| 0 | Foundation: domain model, config, database, logging, tests, dashboard shell | ✅ **done** |
| 1 | MT5 live read (needs Windows host — TC-ADR-032) | ⏳ next |
| 2 | Historical market store: canonical bars, aggregation, indicators, replay | ⏳ |
| 3 | Quant: regime, trend, momentum, structure, volatility | ⏳ |
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
