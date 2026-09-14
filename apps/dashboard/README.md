# Trading Command — Dashboard (Human Control Plane)

Next.js + TypeScript web Control Plane (TC-SPEC-001 §97, Part XXII; TC-ADR-031/-039).

**Phase 0 status:** shell only. Renders OPERATING MODE, SYSTEM HEALTH, dependency
health, REFERENCE UNIT (£250, not a target), and the KILL SWITCH. The Prime Directive
(§0 — no return target) is displayed prominently.

The full cockpit (§98: P&L, opportunities, positions, events, regimes, performance
attribution) is built vertically alongside the XAUUSD golden path (§123), not up
front. This shell has no live data; Phase 1 wires it to `apps/api`.

## Run

```bash
npm install
npm run dev      # http://localhost:3000
```

Domain types are hand-mirrored from the Python source of truth in `lib/domain.ts`
(TC-ADR-031). `£250` is a reference unit for risk/R/expectancy only; there is no
capital return target and the UI must never display or act on one (§0, §75).
