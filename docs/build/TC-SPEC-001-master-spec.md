# TRADING COMMAND

## Master Product, Architecture, Taxonomy & Build Specification

**Document ID:** TC-SPEC-001
**Version:** 1.3
**Status:** BUILD AUTHORITY
**Primary Build Environment:** Kiro
**Source Authority:** GitHub
**Initial Broker:** Eightcap
**Trading Gateway:** MetaTrader 5
**Initial Mode:** SHADOW
**Reference Unit (for R and expectancy math only):** £250
**Primary V1 Objective:** PROVE OR DISPROVE EDGE — not return
**Capital Return Target:** NONE IN V1 (explicitly out of scope)
**Crypto:** PROHIBITED

> This document is the committed build authority for the Trading Command platform,
> per **TC-ADR-001 (GitHub is source authority)** and **TC-ADR-002 (Kiro is the
> primary build environment)**. It is the verbatim capture of TC-SPEC-001 v1.0 +
> v1.1 expansion + v1.2 addendum + v1.3 amendment as supplied by the product owner.
>
> Implementation notes, deviations, and open questions are NOT recorded here.
> They live in `docs/decisions/` as Architectural Decision Records (ADRs) and in
> `docs/build/OPEN-QUESTIONS.md`. This file changes only when the owner revises
> the spec itself.

---

## Precedence

Where sections conflict, the later version governs: **v1.3 > v1.2 > v1.1 > v1.0**.
This document supersedes all prior versions in full.

---

# PART 0 — PRIME DIRECTIVE

## 0. Prime Directive

Trading Command V1 exists to **discover and honestly validate tradable edge**. It is
NOT rewarded for returns, and has no return target.

A V1 that proves *no* edge exists in its universe has **succeeded**, provided the
disproof is statistically sound.

Any pressure — human or AI — to generate returns, increase trade frequency, or
promote toward live trading *before* an edge is validated out-of-sample and net of
real costs SHALL be treated as a defect.

This directive sits in the same deterministic, un-overridable tier as the crypto
prohibition. It outranks all other objectives. AI cannot override it. Human urgency
cannot override it.

```text
V1 DELIVERABLE = A PROVEN OR DISPROVEN THEORY OF EDGE
                 + THE INSTRUMENT TO KEEP TESTING MORE

MONEY IS A CONSEQUENCE ALLOWED TO HAPPEN LATER,
ONCE SOMETHING REAL HAS BEEN FOUND.
```

---

# PART I — PRODUCT DEFINITION

## 1. Product

Trading Command is an evidence-driven market intelligence, opportunity discovery,
trading research and selective autonomous execution platform.

It combines: live market data; quantitative analysis; economic information;
monetary-policy information; normal news; political news; geopolitical events;
technology news; regulatory developments; corporate events; market-leader
behaviour; cross-market relationships; historical market behaviour; AI reasoning;
deterministic risk management; execution; post-trade analysis; continuous evidence
accumulation.

Trading Command SHALL NOT operate as a generic "Ask AI what to buy." system.

The platform SHALL identify, validate, rank, challenge, simulate and eventually
execute trading opportunities based upon multiple independent evidence domains.

## 2. North-Star Principle

Trading Command exists to answer: **What is happening, why does it matter, which
tradable markets could be affected, is the expected market reaction actually
occurring, and does sufficient evidence exist to justify risking capital?**

## 3. Trading Philosophy

The platform SHALL prioritise **selectivity over activity.** Trading Command is not
rewarded for producing trades. It is rewarded for identifying situations
demonstrating statistically defensible positive expectancy. Therefore `NO
OPPORTUNITY` is a valid and desirable system state.

## 4. Fundamental Operating Model

OBSERVE → DETECT → UNDERSTAND → RELATE → QUANTIFY → COMPARE → CONVERGE → CHALLENGE
→ DECIDE → CONTROL RISK → SIMULATE / EXECUTE → MONITOR → EXIT → REVIEW → LEARN →
REPEAT

---

# PART II — SCOPE

## 5. Initial Tradable Universe (V1)

Eight primary instruments.

- **Forex:** GBPUSD, EURUSD, USDJPY
- **Equity Indices:** NAS100, US500, UK100
- **Commodities:** XAUUSD, USOIL

Actual Eightcap/MT5 symbol identifiers SHALL be discovered during integration and
mapped to canonical Trading Command identifiers.

## 6. Explicit Exclusions

V1 SHALL NOT trade: cryptocurrencies; individual equities; options; futures
directly; bonds directly; ETFs; leveraged tokens; synthetic crypto products.
Individual equities MAY be monitored as intelligence sources.

## 7. Crypto Rule

`CRYPTO = PROHIBITED`. Any crypto instrument entering the trading pipeline SHALL
result in `ASSET_CLASS_PROHIBITED`. This rule SHALL exist within deterministic
policy code. AI cannot override it.

---

# PART III — SYSTEM ARCHITECTURE

## 8. Fixed Architecture

```
USER → TRADING COMMAND UI (HUMAN CONTROL PLANE) → TRADING COMMAND
  INTELLIGENCE PLATFORM
  [ Market | Macro | News | Events | Companies | Graph ]
      ↓ CONVERGENCE ENGINE
      ↓ OPPORTUNITY ENGINE
      ↓ EVIDENCE PACK
      ↓ [ QUANT | HISTORICAL ANALOGUES | AI REASONING ]
      ↓ AI CRITIC
      ↓ DECISION ENGINE
      ↓ RISK ENGINE
      ↓ SIMULATION / EXECUTION
  → META TRADER 5 → EIGHTCAP
```

## 9. Architecture Principle

Eightcap and MT5 are infrastructure. Trading Command contains the proprietary
intelligence. The architecture SHALL maintain separation between INTELLIGENCE /
DECISION / RISK / EXECUTION. No external provider SHALL become deeply coupled to
the core domain model.

---

# PART IV — CORE TAXONOMY

## 10. Taxonomy Root

MARKET, INSTRUMENT, OBSERVATION, SIGNAL, EVENT, ENTITY, RELATIONSHIP, THEME,
REGIME, OPPORTUNITY, EVIDENCE, STRATEGY, ASSESSMENT, DECISION, RISK, ORDER,
POSITION, OUTCOME, LEARNING.

## 11. Instrument Taxonomy

- Forex: GBPUSD, EURUSD, USDJPY
- Index: NAS100, US500, UK100
- Commodity: XAUUSD, USOIL

## 12. Observation Taxonomy

PRICE_CHANGE, VOLUME_CHANGE, VOLATILITY_CHANGE, SPREAD_CHANGE, BREAKOUT, BREAKDOWN,
TREND_CHANGE, NEWS_ITEM, ECONOMIC_RELEASE, COMPANY_PRICE_MOVE,
COMPANY_ANNOUNCEMENT, POLITICAL_EVENT, CENTRAL_BANK_EVENT. Observations SHALL NOT
themselves represent trading decisions.

## 13. Signal Taxonomy

TECHNICAL, MACRO, NEWS, POLITICAL, GEOPOLITICAL, CORPORATE, SECTOR, CROSS_MARKET,
SENTIMENT, EVENT, EXECUTION.

## 14. News Taxonomy

NEWS → Economy, Politics, Geopolitics, Conflict, Trade, Tariffs, Sanctions, Energy,
Technology, AI, Semiconductors, Banking, Regulation, Corporate, Supply Chain,
Cybersecurity, Natural Disaster, Labour/Strikes, Other.

## 15. Event Taxonomy

- **Scheduled:** CPI, GDP, PMI, EMPLOYMENT, INTEREST_RATE_DECISION, BUDGET,
  CENTRAL_BANK_SPEECH, EARNINGS, ELECTION
- **Breaking:** MILITARY_ESCALATION, EMERGENCY_RATE_ACTION, RESIGNATION, SANCTION,
  TARIFF, CYBERATTACK, ENERGY_DISRUPTION, CORPORATE_SHOCK
- **Developing:** WAR, TRADE_DISPUTE, POLITICAL_INSTABILITY, ELECTION_TREND,
  ENERGY_CRISIS, SUPPLY_CHAIN_DISRUPTION, BANKING_STRESS

## 16. Event Attributes

eventId, eventType, title, firstSeen, lastUpdated, region, countries, entities,
themes, sourceCount, severity, novelty, velocity, confidence, status.
Status: EMERGING, DEVELOPING, CONFIRMED, STABLE, RESOLVED.

## 17. News Intelligence Dimensions

RELEVANCE, SEVERITY, NOVELTY, VELOCITY, CONFIDENCE — distinct measurements.

## 18. Entity Taxonomy

COUNTRY, GOVERNMENT, CENTRAL_BANK, COMPANY, SECTOR, COMMODITY, CURRENCY, INDEX,
PERSON, REGULATOR, INDUSTRY, REGION.

## 19. Market Leader Taxonomy

Initial intelligence baskets (configuration-driven):
- **Technology / Mega Cap:** NVIDIA, Microsoft, Apple, Amazon, Alphabet, Meta
- **Semiconductor:** NVIDIA, AMD, Broadcom, TSMC, ASML
- **US Banking:** JPMorgan, Bank of America, Goldman Sachs
- **UK Banking:** HSBC, Barclays, Lloyds, NatWest
- **Energy:** ExxonMobil, Chevron, Shell, BP
- **Defence:** Lockheed Martin, RTX, BAE Systems, Rheinmetall

## 20. Theme Taxonomy

AI, SEMICONDUCTORS, ENERGY, BANKING, DEFENCE, INFLATION, INTEREST_RATES,
USD_STRENGTH, GBP_STRENGTH, RISK_ON, RISK_OFF, CHINA, MIDDLE_EAST, UK_ECONOMY,
US_ECONOMY, EUROPEAN_ECONOMY.

## 21. Relationship Taxonomy

COMPANY→SECTOR, COMPANY→INDEX, EVENT→COUNTRY, EVENT→COMMODITY,
CENTRAL_BANK→CURRENCY, THEME→COMPANY, THEME→INSTRUMENT, COMPANY→INSTRUMENT,
EVENT→THEME, INSTRUMENT→INSTRUMENT.

## 22. Market Relationship Graph

The graph SHALL allow intelligence to propagate from an observed event to
potentially affected tradable instruments (e.g. NVIDIA → SEMICONDUCTORS →
TECHNOLOGY → NAS100; MIDDLE EAST ESCALATION → ENERGY RISK → OIL/GOLD →
USOIL/XAUUSD; BANK OF ENGLAND → MONETARY POLICY → GBP → GBPUSD/EURGBP).

---

# PART V — DATA SOURCES

## 23. Market Data

Primary V1 source: MetaTrader 5 → Eightcap. Required: quotes, candles, ticks where
available, spread, account, positions, orders, history, instrument metadata.

## 24. News Sources

Architecture SHALL support multiple providers; objective is zero-cost sources
wherever practical. Candidates: BBC, Guardian, NPR, France24, Euronews, DW, GDELT.
Subject to each source's terms and technical availability. Providers SHALL be
adapters rather than core dependencies.

## 25. Official Sources

- **UK:** GOV.UK, Bank of England, ONS
- **US:** Federal Reserve, BLS, BEA, SEC, other official agencies
- **Europe:** ECB, Eurostat, European Commission, EU institutions

## 26. Company Sources

SEC EDGAR, company IR, company RSS, regulatory announcements, public corporate
releases. Company intelligence SHALL be separated from tradable-instrument scope.

## 27. Provider Interface

```typescript
interface IntelligenceProvider {
  id: string;
  fetch(since: Date): Promise<RawIntelligenceItem[]>;
}
```

No business logic SHALL depend upon a specific news provider.

---

# PART VI — NEWS & EVENT INTELLIGENCE ENGINE

## 28. Ingestion Pipeline

SOURCE → INGEST → NORMALISE → DEDUPLICATE → CLUSTER → CLASSIFY → ENTITY EXTRACTION
→ THEME EXTRACTION → RELEVANCE → SEVERITY → NOVELTY → VELOCITY → RELATIONSHIP GRAPH
→ MARKET IMPACT HYPOTHESIS.

## 29. Deduplication

Five news organisations reporting the same event SHALL become ONE EVENT with
sourceCount = 5. Source count may strengthen confidence that the event exists; it
SHALL NOT artificially multiply market evidence.

## 30. News Velocity

Velocity measures how rapidly an event is spreading. The system SHALL detect
increasing information velocity.

## 31. Novelty

Distinguish NEW INFORMATION / REPEATED INFORMATION / UPDATE / MATERIAL UPDATE. A
repeated headline SHALL NOT repeatedly trigger analysis.

## 32. Market Impact Hypothesis

An event may create potential effects (a hypothesis). It SHALL NOT constitute
permission to trade.

---

# PART VII — MARKET INTELLIGENCE

## 33. Quant Engine

Deterministic calculations as appropriate: EMA, SMA, RSI, MACD, ATR, ADX, ROC,
Bollinger Bands, volatility, volume, trend, support, resistance, breakout,
breakdown, range, momentum, price acceleration, spread, reward/risk.

## 34. Market Regime

STRONG_TREND, WEAK_TREND, RANGE, BREAKOUT, VOLATILITY_EXPANSION,
VOLATILITY_CONTRACTION, EVENT_DRIVEN, DISORDERLY, UNKNOWN. Strategies SHALL be
regime-aware.

## 35. Multi-Timeframe Model

1m, 5m, 15m, 1h, 4h, 1d. Different strategies MAY use different combinations.

---

# PART VIII — CONVERGENCE

## 36. Evidence Domains

Grouped into independent domains: PRICE/STRUCTURE, MOMENTUM/VOLATILITY, MACRO,
NEWS/EVENT, COMPANY/SECTOR, CROSS-MARKET, HISTORICAL, EXECUTION.

## 37. Convergence Principle

An opportunity becomes stronger when genuinely independent evidence domains agree.

## 38. Convergence Score

The Convergence Engine SHALL produce 0–100 but SHALL retain the underlying
evidence. The score SHALL NOT replace explainability.

## 39. Correlated Evidence

Correlated observations SHALL NOT be treated as independent confirmation (e.g.
NVIDIA↓ AMD↓ Broadcom↓ may represent SEMICONDUCTOR_WEAKNESS, not three signals).

---

# PART IX — OPPORTUNITY ENGINE

## 40. Opportunity Sources

Market-Led (price event → investigate cause); Event-Led (world event → investigate
affected markets); Convergence-Led (multiple domains align → high-quality
candidate).

## 41. Opportunity Entity

```typescript
interface Opportunity {
  id: string;
  instrument: string;
  origin: "MARKET" | "EVENT" | "CONVERGENCE";
  detectedAt: Date;
  expiresAt: Date;
  convergenceScore: number;
  evidenceIds: string[];
}
```

## 42. Opportunity Expiry

Every opportunity SHALL have an expiry. Stale opportunities SHALL be rejected.

---

# PART X — EVIDENCE MODEL

## 43. Evidence Pack

Before a trading decision is made, an immutable Evidence Pack SHALL be created
containing: instrument, timestamp, market regime, price, multi-timeframe structure,
momentum, volatility, spread, macro context, news events, political/geopolitical
context, company/sector context, cross-market observations, historical analogues,
portfolio state, strategy candidates.

## 44. Evidence Principle

AI SHALL reason over evidence. AI SHALL NOT be expected to invent missing market
facts.

---

# PART XI — HISTORICAL DATA

## 45. Pre-Population

Trading Command SHOULD begin Shadow with historical data. Target market prices 5–10
years; high-resolution target 1-minute where available; derive 5m/15m/1h/4h/1d.

## 46. Economic History

Target 5–10 years including event, forecast, actual, previous, surprise, timestamp
for significant events.

## 47. Market Leader History

Target 5–10 years where freely and legally obtainable; at minimum daily prices.

## 48. Historical News

Do NOT block the build waiting for a perfect historical news archive. Use structured
historical event datasets, official historical event data, GDELT or equivalent.
From first deployment, Trading Command SHALL build its own Experience Store.

## 49. Forward Outcome Labelling

For every detected opportunity — traded or rejected — record subsequent market
behaviour at 5m, 15m, 30m, 1h, 4h, 1d. This is mandatory.

## 50. Why Rejected Opportunities Matter

Trading Command SHALL measure what would have happened to rejected candidates (did
the Critic improve performance? did the macro filter improve expectancy? are
high-convergence opportunities actually superior?).

---

# PART XII — HISTORICAL ANALOGUE ENGINE

## 51. Purpose

For a current Evidence Pack: find historically comparable conditions and determine
what subsequently occurred.

## 52. Outputs

sample size, win rate, average positive return, average negative return, average R,
expectancy, MFE, MAE, maximum drawdown, confidence interval where appropriate.

## 53. Statistical Discipline

Small historical samples SHALL be identified as weak evidence. The system SHALL NOT
treat 8/10 historical wins as strong evidence without considering sample size and
selection methodology.

---

# PART XIII — AI INTELLIGENCE

## 54. AI Role

AI SHALL primarily perform: interpretation, contextual reasoning, event impact
analysis, relationship reasoning, conflicting evidence analysis, scenario analysis,
trade thesis construction, adversarial criticism.

## 55. AI Shall Not Replace

price calculations, technical indicators, position sizing, risk limits, account
reconciliation, order validation, statistical calculations — where deterministic
software is appropriate.

## 56. AI Provider Abstraction

```typescript
interface AiProvider {
  analyse<T>(request: AiRequest): Promise<T>;
}
```

Potential providers: OpenAI, Anthropic, future local model.

## 57. AI Routing

LOW VALUE → no AI; MEDIUM → cheap/fast model; HIGH → strong reasoning model; HIGH +
AMBIGUOUS → strong reasoning + critic.

---

# PART XIV — SPECIALIST INTELLIGENCE

- **58. Regime Specialist** — determines current market regime.
- **59. Trend Specialist** — determines directional structure.
- **60. Momentum Specialist** — acceleration/deceleration/divergence.
- **61. Structure Specialist** — support, resistance, breakout, breakdown, invalidation.
- **62. Volatility Specialist** — whether volatility is appropriate for the strategy.
- **63. Macro Specialist** — rates, inflation, employment, growth, central banks, fiscal policy.
- **64. Event Intelligence Specialist** — politics, geopolitics, war, sanctions, tariffs, energy, technology, regulation, breaking events.
- **65. Market Leaders Specialist** — company/sector movement, news, earnings, guidance, filings; relates to tradable indices/commodities/currencies.
- **66. Portfolio Specialist** — whether a candidate is appropriate given existing exposure.
- **67. Adversarial Critic** — attempts to prove the trade should NOT occur. Output: NO_OBJECTION / CAUTION / VETO. VETO requires explicit reason codes.

---

# PART XV — DECISION METHODOLOGY

## 68. Decision Inputs

Opportunity, Evidence Pack, Strategy Fit, Regime, Quant Evidence, Macro Evidence,
Event Evidence, Company/Sector Evidence, Cross-Market Evidence, Historical Evidence,
AI Assessment, Critic, Portfolio State, Execution Conditions.

## 69. Decision Outcomes

LONG, SHORT, WAIT, REJECT.

## 70. WAIT

WAIT is a first-class state. Trading Command MAY subsequently reassess the same
opportunity.

---

# PART XVI — STRATEGIES

## 71. Initial Strategy Families

TREND FOLLOWING, BREAKOUT, MOMENTUM CONTINUATION, MEAN REVERSION, VOLATILITY
EXPANSION, EVENT REACTION, EVENT + PRICE CONVERGENCE. No strategy SHALL be assumed
profitable.

## 72. Strategy Eligibility

Strategies SHALL specify compatible regimes.

---

# PART XVII — RISK

## 73. Risk Philosophy

AI identifies opportunities. Risk Engine controls capital. AI SHALL NOT override
deterministic risk limits.

## 74. Reference Unit

£250 is a **reference unit for expressing risk, R and expectancy** — not a capital
base to be compounded and not a return objective. The Shadow ledger SHALL use the
same reference unit so that expectancy in R is directly comparable. The reference
unit exists to make risk-per-trade and expectancy legible. It carries no growth
expectation.

## 75. Promotion Gates

There is **no return target**. Progression through modes is gated by **proof of edge,
never by profit or by schedule**. Advance a strategy to the next mode only when it
shows, on data it was NOT fitted to: positive expectancy in R net of modeled spread +
slippage + inference cost; a minimum sample size (defined per strategy; no cell
believed below it); stability across at least two distinct market regimes;
false-discovery control applied across all attribution slices. Fail any gate → the
strategy stays in SHADOW or is retired. No exceptions, no overrides, no schedule
pressure. Mode order remains SHADOW → PAPER → LIVE_LIMITED → LIVE_AUTO. No dashboard,
agent or operator SHALL display or act upon a capital growth target, because none
exists in V1.

## 76. Initial Risk Research Configuration

Initial Shadow assumption MAY use risk per trade 1% (reference £2.50). Remains a
research parameter until validated against Eightcap contract sizes and
instrument-specific minimum positions.

## 77. Risk Controls

MAX_RISK_PER_TRADE, MAX_DAILY_LOSS, MAX_WEEKLY_LOSS, MAX_DRAWDOWN, MAX_OPEN_RISK,
MAX_POSITIONS, MAX_LEVERAGE, MAX_CORRELATED_EXPOSURE, MAX_INSTRUMENT_EXPOSURE,
MIN_REWARD_RISK, MAX_SPREAD, MAX_SLIPPAGE, MAX_CONSECUTIVE_LOSSES, MANDATORY_STOP,
EVENT_BLACKOUT, STALE_DATA_BLOCK, KILL_SWITCH, KELLY_FRACTION.

> `KELLY_FRACTION` added by TC-CR-001 (see §77a). Default 0.25 (quarter-Kelly),
> config-driven, MUST NOT exceed 0.50.

## 77a. Position Sizing (added by TC-CR-001)

The Risk Engine SHALL size positions using the **Kelly criterion**, applied
fractionally and subordinate to all deterministic risk ceilings in §77.

**Formula.**

```text
f* = (b·p − q) / b
  p  = validated probability of a winning trade for the strategy/cell
  q  = 1 − p
  b  = validated payoff ratio (average win / average loss, in R)
  f* = growth-optimal fraction of capital to risk
```

**Fractional Kelly.** The system SHALL NOT bet full Kelly:

```text
f_applied = KELLY_FRACTION × f*
KELLY_FRACTION default = 0.25 (quarter-Kelly); config-driven; SHALL NOT exceed 0.50.
```

**Ceiling, not mandate.** `f_applied` is an upper suggestion only:

```text
risk_per_trade = min( f_applied , MAX_RISK_PER_TRADE )
```

and SHALL additionally respect every other §77 control (MAX_OPEN_RISK,
MAX_CORRELATED_EXPOSURE, MAX_INSTRUMENT_EXPOSURE, MAX_POSITIONS, MIN_REWARD_RISK,
etc.). Any breach SHALL reduce or reject the size. **Kelly SHALL NEVER raise risk
above a §77 ceiling.**

**Positive-edge gate.** Kelly sizes a trade only when `f* > 0` (i.e. `b·p > q`). If
`f* ≤ 0`, the deterministic outcome SHALL be `NO_POSITIVE_EDGE → size = 0 → no trade`.

**Unvalidated strategies.** `p` and `b` SHALL be drawn only from **validated,
out-of-sample** statistics satisfying the §75 promotion gates and §87 Shadow
validation (including minimum sample size). Where a strategy/cell has NOT met those
gates, Kelly SHALL NOT be used; sizing SHALL default to a **fixed minimal research
risk** (the §76 default) or zero. Kelly is never applied to an unproven edge estimate.

**Estimation safety.** `p` and `b` are estimates, not truths. The system SHOULD size
against a conservative (lower-confidence-bound) estimate of edge rather than the point
estimate, so estimation error biases toward under-betting.

**Auditability.** The inputs to every sizing decision SHALL be recorded in the trade's
immutable Evidence Pack: `p_used`, `b_used`, `sample_size`, `kelly_fraction`,
`f_star`, `f_applied`, `binding_constraint` (kelly | MAX_RISK_PER_TRADE |
MAX_OPEN_RISK | correlated | other), `mode`.

**Mode independence.** Kelly inputs SHALL be computed per mode. SHADOW-derived `p`/`b`
SHALL NOT size PAPER or LIVE trades, and vice versa (Performance Data Integrity:
separate ledgers per mode).

---

# PART XVIII — OPERATING MODES

- **78. OFF** — No trading analysis.
- **79. SHADOW** — Live environment, real market info, real intelligence, real
  decisions, simulated execution, NO broker orders. Mandatory initial mode.
- **80. PAPER** — Broker/platform simulation where available.
- **81. LIVE_LIMITED** — Real money; small position sizes, limited instruments,
  limited strategies, strict risk.
- **82. LIVE_AUTO** — Autonomous execution; requires explicit operator activation
  and prior validation gates.

---

# PART XIX — SHADOW METHODOLOGY

## 83. Shadow Objective

Does Trading Command demonstrate persistent positive expectancy under realistic
conditions?

## 84. Shadow Simulation

For every simulated trade record: entry, position size, stop, target, spread,
estimated slippage, estimated commission, funding where relevant, exit, P&L, R, MFE,
MAE.

## 85. Shadow Account

Maintain a virtual £250 account with realistic position sizing and capital
constraints. The simulator SHALL NOT permit trades that the equivalent live £250
account could not execute.

## 86. Shadow Metrics

Starting Equity, Current Equity, Return %, P&L, Maximum Drawdown, Win Rate, Profit
Factor, Expectancy, Average R, Average Winner, Average Loser, MFE, MAE, Trades,
Opportunities, Rejected Opportunities.

## 87. Shadow Validation

Do NOT define success purely by win rate. Primary indicators: positive expectancy
after costs, acceptable drawdown, adequate sample size, stability across time,
out-of-sample performance, forward performance, strategy consistency.

---

# PART XX — LEARNING METHODOLOGY

## 88. Experience Store

Every system observation SHALL progressively create proprietary experience: what
was observed, what was known at the time, what agents concluded, what decision was
made, what subsequently occurred.

## 89. No Future Leakage

Evidence Packs SHALL contain only information available at the decision timestamp.
Future information SHALL never enter historical decision reconstruction.

## 90. Immutable Thesis

Once an opportunity/trade decision is made, the original evidence and thesis become
immutable. Subsequent reassessments are separate records.

## 91. Agent Evaluation

Measure each specialist by predictive contribution, accuracy, profit contribution,
loss contribution, regime performance, instrument performance, strategy performance,
confidence calibration.

## 92. Agent Weighting

Agent influence MAY become contextual.

## 93. Strategy Decay

Strategies MAY become ACTIVE, WATCH, DEGRADED, SUSPENDED, RETIRED.

---

# PART XXI — EXECUTION

## 94. MT5 Integration

Required capabilities: account information, symbol information, quotes, historical
bars, positions, orders, order checking, order submission, order modification,
position closure, trade history.

## 95. Eightcap

Eightcap SHALL remain broker authority for actual account, orders, positions,
executions. Local state SHALL be reconciled against broker state.

## 96. Execution Abstraction

```typescript
interface ExecutionProvider {
  getAccount();
  getPositions();
  validateOrder();
  submitOrder();
  modifyOrder();
  closePosition();
}
```

Initial implementation: `Mt5ExecutionProvider`.

---

# PART XXII — HUMAN CONTROL PLANE

## 97. Dashboard

Repository: `apps/dashboard/`. Technology: React / Next.js.

## 98. Main Dashboard

MODE, SYSTEM HEALTH, MT5 STATUS, EIGHTCAP STATUS, AI STATUS, NEWS STATUS, REFERENCE
EQUITY, SHADOW EQUITY, P&L, DRAWDOWN, OPEN RISK, OPPORTUNITIES, POSITIONS,
DEVELOPING EVENTS, AI COST, KILL SWITCH.

## 99. Market Intelligence View

Developing Events, News Velocity, Macro Events, Political Events, Geopolitical
Events, Market Leader Movement, Sector Movement, Themes, Potentially Affected
Instruments.

## 100. Opportunity View

Per-opportunity convergence score with component evidence bands and decision +
reason (e.g. XAUUSD Potential LONG, Convergence 91, decision WAIT — await breakout
confirmation).

## 101. Explainability

Every decision SHALL be explainable in Plain English (operator) and Detailed
Evidence (audit/research).

## 102. Rejection View

Show rejected opportunities and explicit reasons. Mandatory.

---

# PART XXIII — OBSERVABILITY

## 103. Health States

HEALTHY, DEGRADED, TRADING_DISABLED, CRITICAL.

## 104. Fail Closed

Failure of critical dependencies SHALL prevent new live trades.

## 105. Audit

Every important action SHALL be timestamped and recorded.

---

# PART XXIV — REPOSITORY STRUCTURE

```
trading-command/
├── apps/            runtime/ api/ dashboard/  (+ cli/ per v1.2)
├── packages/        domain/ mt5-provider/ market-data/ quant-engine/
│                    news-ingestion/ event-engine/ entity-engine/
│                    relationship-graph/ market-leaders/ macro-engine/
│                    convergence-engine/ opportunity-engine/ evidence-engine/
│                    historical-engine/ ai-gateway/ decision-engine/
│                    portfolio-engine/ risk-engine/ shadow-engine/
│                    execution-engine/ position-manager/ learning-engine/
│                    database/ observability/
│                    (+ healthcare-intelligence/ strategic-materials/
│                       supply-chain-engine/ theme-engine/ cross-market-engine/
│                       market-permissions/ per v1.1)
├── agents/          regime/ trend/ momentum/ structure/ volatility/ macro/
│                    event-intelligence/ market-leaders/ portfolio/ critic/
│                    (+ healthcare/ strategic-materials/ supply-chain/
│                       cross-market/ per v1.1)
├── providers/       news/ official/ company/ market/
├── strategies/      trend-following/ breakout/ momentum/ mean-reversion/
│                    volatility-expansion/ event-reaction/ convergence/
├── config/          instruments.yaml companies.yaml sources.yaml
│                    relationships.yaml risk.yaml ai.yaml runtime.yaml
│                    (+ healthcare.yaml strategic-materials.yaml themes.yaml
│                       supply-chains.yaml market-permissions.yaml per v1.1)
├── data/            historical/ reference/
├── research/
├── tests/           unit/ integration/ replay/ regression/
├── docs/            architecture/ taxonomy/ methodology/ decisions/ build/
├── README.md
└── .env.example
```

---

# PART XXV — BUILD METHODOLOGY

## 107. Build Principle

Do NOT attempt to build every component simultaneously. Build vertically. Each unit
SHALL be specified, implemented, tested, integrated, demonstrated, accepted before
dependent functionality is considered complete.

## 108. Phase 0 — Foundation

repository, domain model, configuration, database, logging, testing framework,
dashboard shell.

## 109. Phase 1 — MT5

Prove Trading Command → MT5 → Eightcap: connect, read account, discover instruments,
read prices, read bars, read spread, read positions. No trading required.

## 110. Phase 2 — Historical Market Store

Load historical price data. Create canonical bars, timeframe aggregation, indicator
calculation, replay capability.

## 111. Phase 3 — Quant

regime, trend, momentum, structure, volatility.

## 112. Phase 4 — News Intelligence

feed adapters, normalisation, deduplication, clustering, classification, velocity,
novelty.

## 113. Phase 5 — Entity & Relationship Graph

companies, sectors, countries, themes, markets, relationships.

## 114. Phase 6 — Market Leaders

leader baskets, company price movement, sector movement, corporate events.

## 115. Phase 7 — Convergence

combine independent evidence domains; generate opportunities.

## 116. Phase 8 — Historical Analogues

historical matching and outcome analysis.

## 117. Phase 9 — AI

AI provider abstraction, structured prompts, structured outputs, specialists, critic.

## 118. Phase 10 — Shadow

£250 virtual account, real-time opportunity processing, simulated execution,
position management, cost modelling, performance measurement.

## 119. Phase 11 — Learning

forward outcome labels, agent performance, strategy performance, filter
contribution, confidence calibration.

## 120. Phase 12 — Control Plane

intelligence dashboard, opportunity dashboard, decision explanation, shadow
portfolio, performance, research, configuration, health, kill switch.

## 121. Phase 13 — Paper

Validate real execution workflow using simulation/demo facilities where available.

## 122. Phase 14 — Limited Live

Only after validation.

---

# PART XXVI — FIRST END-TO-END USE CASE

## 123. Golden Path

The first complete vertical use case SHALL be **XAUUSD**:

MT5 price → quant analysis → news/event observation → relationship mapping →
convergence → opportunity → evidence pack → historical analogue → AI analysis →
critic → decision → risk → SHADOW TRADE → position monitoring → exit → outcome →
learning → dashboard.

Do not build breadth before this works.

---

# PART XXVII — DATA QUALITY

## 124. Source Provenance

Every external observation SHALL retain provider, source, timestamp, ingestedAt,
original identifier, confidence where applicable.

## 125. Time

All internal timestamps SHALL use UTC. Display MAY convert to local time.

## 126. No Look-Ahead

Historical replay SHALL reproduce information as it was available at the historical
timestamp. Mandatory.

## 127. Survivorship Bias

Historical company/sector research SHALL account for changing index constituents
where material. Current winners SHALL NOT simply be projected backwards.

---

# PART XXVIII — SECURITY

## 128. Secrets

Never commit Eightcap credentials, MT5 credentials, AI API keys, provider API keys.

## 129. Environment

Secrets SHALL use environment variables or an appropriate secret store. `.env`
SHALL be ignored by Git.

---

# PART XXIX — ACCEPTANCE PRINCIPLES

## 130. V1 Success

V1 success is **not defined by any capital outcome**. There is no return target (see
§0, §75). V1 success is: Trading Command can reliably observe markets and external
intelligence, identify and explain opportunities, simulate realistic trades net of
real costs, measure outcomes honestly, and determine whether any strategy/evidence
combination demonstrates persistent, out-of-sample positive expectancy. Proving that
**no** edge exists in the V1 universe is a **successful** outcome, provided the
disproof is statistically sound. The deliverable is a proven-or-disproven theory of
edge, plus the instrument to keep testing.

## 131. Shadow Success

Requires evidence of positive expectancy after costs, controlled drawdown, adequate
observations, out-of-sample validity, forward stability, operational reliability.
Exact statistical release thresholds defined after the research engine can measure
them correctly.

## 132. Scaling Principle

Capital exposure SHALL scale only because validated evidence supports it (see §75
promotion gates). There is no return target and therefore no circumstance in which
exposure scales to "catch up" to one.

---

# PART XXX — ARCHITECTURAL DECISIONS (v1.0)

- **TC-ADR-001** GitHub is source authority.
- **TC-ADR-002** Kiro is the primary build environment.
- **TC-ADR-003** Trading Command is the proprietary intelligence platform.
- **TC-ADR-004** MetaTrader 5 is the V1 market and execution gateway.
- **TC-ADR-005** Eightcap is the initial broker.
- **TC-ADR-006** Crypto is prohibited.
- **TC-ADR-007** The initial tradable universe contains eight instruments.
- **TC-ADR-008** Individual equities are intelligence inputs, not V1 tradable assets.
- **TC-ADR-009** Free intelligence sources are preferred for V1.
- **TC-ADR-010** All external providers are adapter-based.
- **TC-ADR-011** AI is selective rather than continuously invoked.
- **TC-ADR-012** AI cannot override deterministic risk.
- **TC-ADR-013** Evidence domains rather than indicator counts determine convergence.
- **TC-ADR-014** Historical and rejected opportunities are measured.
- **TC-ADR-015** Shadow is mandatory before live trading.
- **TC-ADR-016** £250 is a reference unit for risk/R/expectancy, not a capital base to compound.
- **TC-ADR-017** V1 has NO capital return target. Progression is gated by proof of edge, never by profit or schedule (see §0, §75).
- **TC-ADR-018** Original evidence and decisions are immutable.
- **TC-ADR-019** The system SHALL measure whether each agent/filter adds value.
- **TC-ADR-020** No strategy or AI model is presumed to possess an edge.

---

# PART XXXI — KIRO BUILD INSTRUCTION

Kiro SHALL treat this document as the product and architecture authority. Where
implementation ambiguity exists: (1) preserve separation of concerns; (2) favour
deterministic computation over LLM computation; (3) maintain provider abstraction;
(4) preserve evidence provenance; (5) preserve historical reproducibility; (6)
prevent look-ahead bias; (7) fail closed; (8) default to SHADOW; (9) never introduce
cryptocurrency; (10) never introduce live execution without an explicit approved
build unit.

Kiro SHALL NOT silently: add new asset classes; expand the trading universe;
replace MT5; replace Eightcap; introduce paid data dependencies; change risk
methodology; change the £250 reference unit or introduce any capital return target;
activate live trading; alter taxonomy; remove auditability. Such changes require an
explicit ADR.

---

# PART XXXII — FINAL PRODUCT DEFINITION

Trading Command is a continuously operating market-intelligence system that observes
markets and the world around them, builds relationships between events and tradable
assets, identifies situations where independent evidence converges, tests those
situations against historical experience, applies AI reasoning and adversarial
challenge, controls risk deterministically, simulates trades in Shadow, measures
what actually happens, and progressively learns where genuine trading edge exists.

Long-term transition: INTELLIGENCE → EVIDENCE → EDGE DISCOVERY → SHADOW VALIDATION →
PAPER VALIDATION → LIMITED LIVE → PROVEN STRATEGIES → CONTROLLED AUTONOMY. The system
SHALL earn the right to trade real capital through evidence.

---

# V1.1 EXPANSION — GLOBAL INTELLIGENCE, STRATEGIC MATERIALS, HEALTHCARE & GLOBAL MARKETS

**Version:** 1.1 — V1 SHALL implement the full intelligence model below. Trading
permissions remain independently controlled by policy.

## 133. Core Scope Distinction

Every market/entity SHALL carry an explicit permission state: INTELLIGENCE_ONLY,
SHADOW_TRADABLE, LIVE_TRADABLE, PROHIBITED. Observation SHALL NOT imply authority to
trade. Promotion requires configuration change, evidence, and an ADR. Crypto remains
PROHIBITED.

## 134. World & Market Intelligence Taxonomy

MARKET, ECONOMY_AND_MACRO, MONETARY_POLICY, POLITICS, GEOPOLITICS,
CONFLICT_AND_SECURITY, COMPANY_AND_CORPORATE, TECHNOLOGY_AND_AI,
HEALTHCARE_AND_LIFE_SCIENCES, ENERGY, STRATEGIC_MATERIALS, CLIMATE_AND_WEATHER,
TRADE_AND_SUPPLY_CHAIN, REGULATION, CYBERSECURITY, SOCIAL_AND_MAJOR_EVENTS. All
domains SHALL feed the common Event/Entity/Theme/Relationship/Evidence/Opportunity
models rather than create disconnected pipelines.

## 135. Expanded Global Index Universe

Monitor and shadow-evaluate global indices subject to actual Eightcap/MT5 symbol
discovery: US (NASDAQ 100, S&P 500, Dow Jones 30); UK (FTSE 100); Europe (DAX 40,
CAC 40, Euro Stoxx 50 where available); Asia-Pacific (Nikkei 225, Hang Seng where
available, ASX 200). Canonical names decoupled from broker symbols. Discover broker
symbol, contract size, minimum volume, tick size, trading hours, margin and spread
before enabling SHADOW_TRADABLE or LIVE_TRADABLE.

## 136. Expanded FX Intelligence Universe

Core V1 pairs remain GBPUSD, EURUSD, USDJPY. Graph MAY monitor additional liquid
pairs (EURGBP, GBPJPY, AUDUSD, USDCHF, USDCAD) defaulting to INTELLIGENCE_ONLY until
promoted.

## 137. Strategic Materials Domain

PRECIOUS (Gold, Silver, Platinum, Palladium); INDUSTRIAL (Copper, Aluminium, Nickel,
Zinc); BATTERY (Lithium, Nickel, Cobalt, Graphite, Manganese); SEMICONDUCTOR
(Gallium, Germanium, Silicon); RARE_EARTHS (Neodymium, Dysprosium, Praseodymium);
ENERGY_MATERIALS (Uranium). Broker-supported instruments MAY be promoted to
SHADOW_TRADABLE after symbol discovery; others remain intelligence-only.

## 138. Strategic Materials Intelligence Methodology

Model demand/supply transmission rather than simply price momentum (e.g. AI_CAPEX →
DATA_CENTRES → POWER_DEMAND → GRID_EXPANSION → COPPER/URANIUM/SILVER →
PRODUCERS/UTILITIES/INDUSTRIALS → EQUITY_INDICES).

## 139. Healthcare & Life Sciences Domain

PHARMACEUTICALS, BIOTECHNOLOGY, MEDICAL_DEVICES, HEALTH_INSURANCE,
HEALTHCARE_SERVICES, DIAGNOSTICS, VACCINES, PUBLIC_HEALTH, DRUG_PRICING,
CLINICAL_TRIALS, REGULATORY_APPROVALS, SAFETY_AND_RECALLS, PATENTS_AND_EXCLUSIVITY,
M_AND_A, DISEASE_OUTBREAKS.

## 140. Healthcare Event Taxonomy

CLINICAL_TRIAL_RESULT, TRIAL_HALT, DRUG_APPROVAL, DRUG_REJECTION, LABEL_EXPANSION,
SAFETY_WARNING, PRODUCT_RECALL, PATENT_DECISION, DRUG_PRICING_CHANGE,
REIMBURSEMENT_CHANGE, HEALTH_POLICY_CHANGE, M_AND_A, PIPELINE_UPDATE,
DISEASE_OUTBREAK, PUBLIC_HEALTH_EMERGENCY, VACCINE_DEVELOPMENT, SUPPLY_SHORTAGE.

## 141. Healthcare Authority Sources

FDA, EMA, MHRA, NHS/UK health authorities, CDC, WHO, company IR, regulatory filings,
combined with general-news coverage; source provenance and authority level retained.

## 142. Healthcare Market Leaders

Configurable basket: Eli Lilly, Novo Nordisk, Johnson & Johnson, UnitedHealth Group,
AstraZeneca, Roche, Novartis, Pfizer, Merck. Configuration-driven, additions/removals
without code changes.

## 143. Healthcare Relationship Examples

REGULATORY_APPROVAL → COMPANY → COMPETITORS → THERAPEUTIC_AREA → HEALTHCARE_SECTOR →
INDEX; DISEASE_OUTBREAK → PHARMA/BIOTECH/DIAGNOSTICS → TRAVEL/CONSUMER/SUPPLY_CHAIN →
RISK_SENTIMENT → INDICES/FX/COMMODITIES. First-, second- and third-order hypotheses;
higher-order carries lower default confidence until confirmed by market evidence.

## 144. Supply Chain Intelligence

First-class relationship domain: RAW_MATERIAL → COMPONENT → MANUFACTURER → INDUSTRY →
MARKET_LEADER → INDEX → TRADABLE_INSTRUMENT. Relationship types: SUPPLIES, CONSUMES,
PRODUCES, DEPENDS_ON, SUBSTITUTES_FOR, COMPETES_WITH, REGULATES, FINANCES, INSURES,
TRANSPORTS, INDEX_MEMBER_OF, EXPOSED_TO_COUNTRY, EXPOSED_TO_COMMODITY,
EXPOSED_TO_THEME.

## 145. Relationship Graph Semantics

Every edge SHOULD support relationshipType, sourceEntityId, targetEntityId,
direction, strength, confidence, validFrom, validTo, provenance, lastVerifiedAt.
Relationships SHALL be temporal where necessary; the graph SHALL NOT assume a
relationship is permanent.

## 146. Causal Hypothesis vs Correlation

Distinguish CAUSAL_HYPOTHESIS, CORRELATION, CO_MOVEMENT, COMMON_FACTOR,
UNKNOWN_RELATIONSHIP. AI MAY propose causal hypotheses; deterministic/statistical
modules SHALL test whether observed market behaviour supports them.

## 147. Global Theme Engine

Themes SHALL be durable objects with lifecycle EMERGING, ACCELERATING, ESTABLISHED,
DECELERATING, DORMANT, RESOLVED. Theme strength based on independent evidence,
persistence, velocity and market confirmation.

## 148. Expanded Market Leaders Methodology

Leader baskets at multiple levels (COMPANY, SECTOR, INDUSTRY, THEME, REGION,
SUPPLY_CHAIN). A basket move SHALL be represented as one derived factor when
constituents are highly correlated, preventing false convergence.

## 149. Cross-Market Intelligence

Monitor propagation between markets (e.g. BOND_YIELDS → USD → GOLD → EQUITY_INDICES).
The system SHALL search for the cleanest tradable expression of an event rather than
automatically trade the market geographically closest to the event.

## 150. Evidence Independence Model

Convergence scoring SHALL group evidence into factor families: MARKET_STRUCTURE,
MOMENTUM_VOLATILITY, MACRO_MONETARY, NEWS_EVENT, CORPORATE_SECTOR,
STRATEGIC_MATERIALS_SUPPLY_CHAIN, HEALTHCARE_LIFE_SCIENCES, CROSS_MARKET,
HISTORICAL_ANALOGUE, EXECUTION_QUALITY. Score includes an independence adjustment and
a freshness adjustment: Adjusted Evidence = Raw × Independence × Freshness × Source
Confidence × Regime Relevance. Formula configuration-controlled and calibrated in
Shadow.

## 151. Opportunity Methodology v1.1

OBSERVATION → EVENT/MARKET ANOMALY → ENTITY + THEME RESOLUTION → RELATIONSHIP
PROPAGATION → IMPACT HYPOTHESES → MARKET CONFIRMATION → CONVERGENCE → HISTORICAL
ANALOGUES → AI THESIS → ADVERSARIAL CRITIC → RISK ELIGIBILITY → SHADOW DECISION →
OUTCOME LABELLING. No news story, company move or material price change directly
authorises a trade.

## 152. Hypothesis Object

```typescript
interface MarketImpactHypothesis {
  id: string;
  triggerEventId: string;
  targetInstrumentId: string;
  expectedDirection: "BULLISH" | "BEARISH" | "VOLATILITY" | "UNCERTAIN";
  horizon: string;
  transmissionPath: string[];
  confidence: number;
  createdAt: Date;
  expiresAt: Date;
  confirmationRequirements: string[];
  invalidationConditions: string[];
}
```

## 153. Market Permission Object

```typescript
type MarketPermission =
  | "INTELLIGENCE_ONLY" | "SHADOW_TRADABLE" | "LIVE_TRADABLE" | "PROHIBITED";

interface InstrumentPolicy {
  canonicalId: string;
  brokerSymbol?: string;
  assetClass: string;
  permission: MarketPermission;
  minEvidenceScore?: number;
  allowedStrategies: string[];
  riskProfile?: string;
}
```

## 154. Shadow-First Global Research

V1 SHOULD evaluate a wider set of eligible broker-supported indices, FX and metals
than the initial live universe. Simulated trades SHALL obey actual broker constraints
(minimum volume, contract size, spread, margin, session, estimated costs). Shadow
results segmented by instrument, asset class, region, strategy, regime, theme, event
type, evidence-domain combination, session, time horizon.

## 155. Historical Data Expansion

Where practical: global indices 5–10y; core FX 5–10y; gold/oil 5–10y; silver/copper
5–10y where available; market leaders 5–10y; macro events 5–10y; health events
structured history; strategic materials daily/reference history; index constituents
historical membership where material. Do not delay Shadow for perfect coverage;
missing domains SHALL be explicitly flagged rather than silently imputed.

## 156. Healthcare & Materials Specialists

Add healthcare-intelligence, strategic-materials, supply-chain, cross-market
specialists. These SHALL create structured assessments, not trade orders.

## 157. Expanded Repository Additions

packages: healthcare-intelligence, strategic-materials, supply-chain-engine,
theme-engine, cross-market-engine, market-permissions. agents: healthcare,
strategic-materials, supply-chain, cross-market. config: healthcare.yaml,
strategic-materials.yaml, themes.yaml, supply-chains.yaml, market-permissions.yaml.

## 158. Expanded Dashboard

World Intelligence view: GLOBAL THEMES, DEVELOPING EVENTS, REGIONAL RISK,
MACRO/CENTRAL BANKS, TECHNOLOGY/AI, HEALTHCARE/LIFE SCIENCES, ENERGY, STRATEGIC
MATERIALS, SUPPLY CHAINS, MARKET LEADERS, CROSS-MARKET PROPAGATION. Operator SHALL be
able to click a theme/event and see the transmission graph to affected instruments.

## 159. Research Questions V1 SHALL Answer

(1) Which evidence-domain combinations have positive expectancy? (2) Which markets
best express particular event types? (3) Does news velocity add predictive value
after price confirmation? (4) Do market-leader baskets add value beyond index price
data? (5) Do strategic-material relationships add predictive value? (6) Do healthcare
events create exploitable sector/index effects? (7) Which second-order relationships
are reliable? (8) Which specialists improve decisions and which reduce expectancy?
(9) Which regimes favour each strategy? (10) Does higher convergence correspond to
higher realised expectancy?

## 160. V1 Build Scope Decision

V1 SHALL cover the full intelligence taxonomy, relationship graph and Shadow research
framework. This does NOT mean every monitored entity becomes live tradable. V1 must:
SEE broadly, UNDERSTAND relationships, FORM hypotheses, TEST against markets, SHADOW
trade eligible instruments, MEASURE outcomes, LEARN which evidence matters.

## 161. Revised Golden Path

The original XAUUSD golden path remains the first vertical implementation. After
XAUUSD is proven end-to-end, expand: (1) XAUUSD; (2) GBPUSD/EURUSD/USDJPY; (3)
NASDAQ/S&P 500/FTSE 100; (4) DAX/European indices; (5) SILVER/COPPER where
broker-supported; (6) additional global indices; (7) other eligible
metals/commodities. Intelligence domains may be built broadly while execution
expansion remains gated.

## 162. Additional Architectural Decisions (v1.1)

- **TC-ADR-021** V1 intelligence coverage is global and multi-domain.
- **TC-ADR-022** Healthcare & Life Sciences is a first-class intelligence domain.
- **TC-ADR-023** Strategic Materials is a first-class intelligence domain.
- **TC-ADR-024** Supply chains are explicit graph relationships.
- **TC-ADR-025** The graph supports first-, second- and third-order market impact hypotheses.
- **TC-ADR-026** Monitored and tradable are separate states.
- **TC-ADR-027** Global indices may be Shadow-tested when broker-supported and policy-enabled.
- **TC-ADR-028** Evidence convergence SHALL adjust for correlated/common-factor evidence.
- **TC-ADR-029** Themes are persistent lifecycle objects rather than transient tags.
- **TC-ADR-030** Trading Command searches for the cleanest tradable expression of an event.

> **NOTE (build authority):** The v1.2 addendum below ALSO defines a block of ADRs
> numbered TC-ADR-021 … TC-ADR-027, which collide with the v1.1 numbers above. This
> is a defect in the source spec. Pending owner ruling (see
> `docs/build/OPEN-QUESTIONS.md`), the v1.2 performance/control-plane decisions are
> referred to internally as **TC-ADR-P01 … TC-ADR-P07** to keep ADR identifiers
> unique. The text is reproduced verbatim below under its original numbering.

---

# V1.1 KIRO IMPLEMENTATION DIRECTIVE

Kiro SHALL treat TC-SPEC-001 v1.1 as the current build authority and the V1.1
sections as superseding narrower V1.0 scope statements where they conflict. The full
V1 product includes global intelligence, healthcare, strategic materials,
supply-chain relationships, expanded index monitoring and global theme reasoning.
Implementation SHALL remain vertical and gated. Broad scope SHALL NOT be interpreted
as permission to scaffold dozens of incomplete modules at once. The first executable
objective remains the XAUUSD vertical path.

---

# V1.2 ADDENDUM — PERFORMANCE, P&L, ATTRIBUTION & CONTROL PLANE

**Version:** 1.2 — **Status:** BUILD AUTHORITY

## Performance Domain

Performance is a first-class Trading Command domain and SHALL NOT be implemented
merely as dashboard decoration. The system SHALL maintain authoritative performance
records for SHADOW, PAPER, LIVE_LIMITED and LIVE_AUTO independently.

### Core P&L Measures

account balance; account equity; starting equity; realised P&L; unrealised P&L; gross
P&L; net P&L after modeled/actual costs; daily/weekly/monthly/YTD/all-time P&L; return
percentage; cumulative return; peak equity; current drawdown; maximum drawdown; open
risk; margin usage where applicable; available capital.

### Trading Performance Measures

opportunities detected/traded/rejected/expired; wins; losses; breakeven trades; win
rate; loss rate; average winner; average loser; win/loss ratio; profit factor;
expectancy; expectancy in R; average R; cumulative R; MFE; MAE; average holding
period; consecutive wins/losses; largest winner/loser; trading costs; slippage; spread
cost; financing/funding cost where relevant.

## Performance Attribution

Every closed and open trade SHALL be attributable across dimensions known at decision
time: INSTRUMENT, ASSET CLASS, REGION, STRATEGY, MARKET REGIME, OPPORTUNITY ORIGIN,
CONVERGENCE BAND, PRICE/STRUCTURE EVIDENCE, MOMENTUM/VOLATILITY EVIDENCE, MACRO
EVIDENCE, NEWS/EVENT EVIDENCE, COMPANY/SECTOR EVIDENCE, CROSS-MARKET EVIDENCE,
HISTORICAL EVIDENCE, AI ASSESSMENT, CRITIC OUTCOME, TIME OF DAY, DAY OF WEEK, HOLDING
PERIOD, EVENT TYPE, THEME. Trading Command SHALL answer: why did we make/lose money?
which strategies possess positive expectancy? which evidence combinations improve
expectancy? which agents/filters reduce performance? which markets and regimes should
receive more/less attention?

## Performance Views

Control Plane SHALL include a dedicated Performance workspace: EQUITY CURVE, CUMULATIVE
P&L, DAILY/WEEKLY/MONTHLY P&L, P&L BY INSTRUMENT/ASSET CLASS/STRATEGY/REGIME/
OPPORTUNITY ORIGIN/CONVERGENCE BAND/EVENT TYPE/THEME/EVIDENCE COMBINATION/AI-CRITIC
OUTCOME, COST ATTRIBUTION, DRAWDOWN HISTORY, TRADE HISTORY.

## Main Trading Cockpit

Primary dashboard SHALL expose at minimum: OPERATING MODE; SYSTEM HEALTH; MT5/EIGHTCAP/
AI/NEWS status; BALANCE; EQUITY; REALIZED P&L; UNREALIZED P&L; TODAY/WEEK/MONTH P&L;
TOTAL RETURN; CURRENT/MAX DRAWDOWN; OPEN RISK; AVAILABLE CAPITAL; OPEN POSITIONS; ACTIVE
OPPORTUNITIES; DEVELOPING EVENTS; CURRENT MARKET REGIMES; PORTFOLIO EXPOSURE; RECENT
CLOSED TRADES; WIN RATE; PROFIT FACTOR; EXPECTANCY; AVERAGE R; BEST/WORST MARKET;
BEST/WORST STRATEGY; AI COST; KILL SWITCH.

## Portfolio & Exposure View

Current exposure by INSTRUMENT, ASSET CLASS, CURRENCY, REGION, THEME, DIRECTION,
CORRELATED RISK CLUSTER. Operator SHALL distinguish nominal exposure from risk-at-stop.

## Trade Detail & Explainability

Every trade SHALL have a detail view: immutable original Evidence Pack; opportunity
origin; convergence score + component evidence; strategy selected; AI thesis; critic
assessment; risk decision; entry rationale; entry/stop/target; position sizing
calculation; market state at entry; subsequent reassessments; exit reason; realised
P&L; realised R; MFE/MAE; costs; post-trade attribution; lessons generated by the
learning engine.

## Performance Data Integrity

SHADOW performance SHALL never be mixed with LIVE. PAPER SHALL never be mixed with
LIVE. All performance records SHALL retain mode, strategy version, configuration
version, AI model/provider version where applicable, and Evidence Pack identifiers.
Strategy/configuration changes SHALL create version boundaries so that results from
materially different strategies are not silently aggregated.

## Control Plane Interfaces

Two operator interfaces: **Web Control Plane** under `apps/dashboard/`; **CLI / Text
Operator Console** under `apps/cli/`. Minimum CLI concepts: status, health, markets,
opportunities, positions, performance, risk, events, explain <id>, pause,
resume-shadow. Dangerous/live commands SHALL require explicit safeguards and SHALL NOT
bypass deterministic policy controls.

## V1.2 Architectural Decisions

> Numbering as written in the source (collides with v1.1 §162). Tracked internally as
> TC-ADR-P01…P07 — see the NOTE under §162 and `docs/build/OPEN-QUESTIONS.md`.

- **TC-ADR-021 (P01)** Performance, P&L and attribution are first-class product domains.
- **TC-ADR-022 (P02)** The primary dashboard is a trading and intelligence cockpit, not merely a system-health page.
- **TC-ADR-023 (P03)** Trading Command SHALL maintain separate performance ledgers for SHADOW, PAPER and LIVE modes.
- **TC-ADR-024 (P04)** Every trade SHALL support multi-dimensional performance attribution.
- **TC-ADR-025 (P05)** Trading Command SHALL provide both a web Control Plane and lightweight CLI/operator console.
- **TC-ADR-026 (P06)** Strategy and configuration versions SHALL be retained with performance records to prevent invalid aggregation.
- **TC-ADR-027 (P07)** The system SHALL explicitly measure the performance contribution of strategies, agents, evidence domains, filters and the adversarial critic.

---

**END OF TC-SPEC-001 v1.2**

---

# V1.3 AMENDMENT — REMOVAL OF RETURN TARGET

**Version:** 1.3 — **Status:** BUILD AUTHORITY

## Rationale

The £25,000 / 12-month return target was a hidden requirement that forced the design
toward fast event-reaction trades it is structurally too slow to win, and created
pressure that would corrupt the platform's own attribution engine into an overfitting
machine. Removing it frees the architecture to become what it is actually good at:
discovering and honestly validating relationship-based edge. The document's own
philosophy (selectivity over activity; earn the right to trade through evidence;
§130–132) already pointed here. v1.3 removes the contradiction.

## Changes

- Added **§0 Prime Directive**: V1 proves or disproves edge; no return target; same
  un-overridable tier as the crypto rule.
- Added **Precedence** clause: v1.3 > v1.2 > v1.1 > v1.0.
- Header: £250 relabelled as a reference unit; return target set to NONE.
- **§74** Reference Capital → Reference Unit (risk/R/expectancy only).
- **§75** Stretch Target → Promotion Gates (advance on proof, never profit/schedule).
- **§130** V1 Success: disproving edge is a valid success; no capital outcome.
- **§132** Scaling Principle: no "catch-up" scaling toward a target.
- **TC-ADR-016 / TC-ADR-017**: restated for reference unit and no-target policy.
- Kiro guardrails: forbid introducing any capital return target.
- All £25,000 references removed throughout.

The £250 references that remain denote the reference unit and the
realistic-fill constraint on the simulator; they carry no growth expectation.

**END OF TC-SPEC-001 v1.3**

---

# TC-CR-001 — POSITION SIZING (FRACTIONAL KELLY)

**Type:** Additive · **Status:** BUILD AUTHORITY (merged) · **Target:** v1.3

Adds **§77a Position Sizing** (fractional Kelly), adds `KELLY_FRACTION` to the §77
control list, and records one new ADR.

**New ADR — TC-ADR-042 (working number).** Position sizing SHALL use fractional Kelly
(default quarter-Kelly), computed only from validated out-of-sample statistics, always
capped by deterministic §77 risk ceilings, defaulting to zero/minimal fixed risk when
edge is unproven or non-positive. Kelly is a ceiling and a discipline, never a mandate
to increase risk.

> **ADR numbering note.** TC-CR-001 proposed this as "TC-ADR-028 (v1.3)". In this
> repo's working register the 021–030 range is already occupied by the v1.1 block and
> the v1.2 block was renumbered to 035–041 (see TC-ADR-033). The next free number is
> therefore **TC-ADR-042**, which is used here and mapped back to the CR's "028" in
> `docs/decisions/REGISTER.md`. The CR's intent is unchanged; only the identifier is
> adapted to the resolved register.

**Build tier.** The positive-edge gate (`f* ≤ 0 → NO_POSITIVE_EDGE → size 0`) and the
§77 ceiling clamp are **deterministic policy code**, in the same un-overridable tier
as the crypto prohibition and the Prime Directive. AI SHALL NOT override them. Options/
Black-Scholes machinery is out of scope (§6).

**END OF TC-CR-001**
