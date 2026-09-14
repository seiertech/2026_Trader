# Architectural Decision Register

Authoritative index of all ADRs. Where an ADR number collides between spec versions,
the **working number** in this register is canonical (see TC-ADR-033). This register
wins over prose when there is ambiguity.

## v1.0 core decisions (from spec Part XXX) — uncontested

| # | Subject |
|---|---|
| TC-ADR-001 | GitHub is source authority |
| TC-ADR-002 | Kiro is the primary build environment |
| TC-ADR-003 | Trading Command is the proprietary intelligence platform |
| TC-ADR-004 | MetaTrader 5 is the V1 market & execution gateway |
| TC-ADR-005 | Eightcap is the initial broker |
| TC-ADR-006 | Crypto is prohibited (deterministic, un-overridable) |
| TC-ADR-007 | Initial tradable universe = 8 instruments |
| TC-ADR-008 | Individual equities are intelligence inputs, not V1 tradable |
| TC-ADR-009 | Free intelligence sources preferred for V1 |
| TC-ADR-010 | All external providers are adapter-based |
| TC-ADR-011 | AI is selective, not continuously invoked |
| TC-ADR-012 | AI cannot override deterministic risk |
| TC-ADR-013 | Evidence domains, not indicator counts, determine convergence |
| TC-ADR-014 | Historical & rejected opportunities are measured |
| TC-ADR-015 | Shadow is mandatory before live trading |
| TC-ADR-016 | £250 is a reference unit for risk/R/expectancy, not a capital base (v1.3) |
| TC-ADR-017 | V1 has NO capital return target; promotion gated by proof not profit/schedule (v1.3) |
| TC-ADR-018 | Original evidence & decisions are immutable |
| TC-ADR-019 | Measure whether each agent/filter adds value |
| TC-ADR-020 | No strategy or AI model is presumed to have an edge |

## v1.1 expansion decisions (uncontested — keep their numbers)

| # | Subject |
|---|---|
| TC-ADR-021 | V1 intelligence coverage is global & multi-domain |
| TC-ADR-022 | Healthcare & Life Sciences is a first-class intelligence domain |
| TC-ADR-023 | Strategic Materials is a first-class intelligence domain |
| TC-ADR-024 | Supply chains are explicit graph relationships |
| TC-ADR-025 | Graph supports 1st/2nd/3rd-order market-impact hypotheses |
| TC-ADR-026 | Monitored and tradable are separate states |
| TC-ADR-027 | Global indices may be Shadow-tested when broker-supported & policy-enabled |
| TC-ADR-028 | Convergence adjusts for correlated/common-factor evidence |
| TC-ADR-029 | Themes are persistent lifecycle objects |
| TC-ADR-030 | System searches for the cleanest tradable expression of an event |

## Session build decisions

| # | Subject | Doc |
|---|---|---|
| TC-ADR-031 | Runtime stack: Python engines + Next.js dashboard + Python CLI | TC-ADR-031-runtime-stack.md |
| TC-ADR-032 | MT5 host topology; Shadow uses replay/synthetic provider | TC-ADR-032-mt5-topology.md |
| TC-ADR-033 | Resolve duplicate ADR numbering (v1.2 block → 033–039) | TC-ADR-033-adr-renumbering.md |
| TC-ADR-034 | Build spec tree at repo root of 2026_Trader | TC-ADR-034-repo-root-layout.md |

## v1.2 addendum decisions — renumbered per TC-ADR-033

Original v1.2 numbers TC-ADR-021…027 collided with v1.1; catalogued here with working
numbers TC-ADR-033-series continuation (035–041 to avoid clashing with 031–034 above).

| Working # | v1.2 original | Subject |
|---|---|---|
| TC-ADR-035 | TC-ADR-021 | Performance, P&L & attribution are first-class product domains |
| TC-ADR-036 | TC-ADR-022 | Primary dashboard is a trading/intelligence cockpit, not a health page |
| TC-ADR-037 | TC-ADR-023 | Separate performance ledgers for SHADOW/PAPER/LIVE modes |
| TC-ADR-038 | TC-ADR-024 | Every trade supports multi-dimensional performance attribution |
| TC-ADR-039 | TC-ADR-025 | Both a web Control Plane and a lightweight CLI/operator console |
| TC-ADR-040 | TC-ADR-026 | Strategy/config versions retained with performance records |
| TC-ADR-041 | TC-ADR-027 | Measure performance contribution of strategies/agents/evidence/filters/critic |
