import fs from "node:fs";
import path from "node:path";

import type { CockpitSnapshot, HealthState } from "@/lib/domain";

// Load the cockpit snapshot emitted by `tc snapshot` (§98-102). Read at request time
// from the public dir; a live API replaces this file source in a later phase. If no
// snapshot exists yet, render an explicit "no snapshot" state rather than fabricate.
function loadSnapshot(): CockpitSnapshot | null {
  try {
    const p = path.join(process.cwd(), "public", "snapshot.json");
    return JSON.parse(fs.readFileSync(p, "utf-8")) as CockpitSnapshot;
  } catch {
    return null;
  }
}

const HEALTH_COLOUR: Record<HealthState, string> = {
  HEALTHY: "#22B24C",
  DEGRADED: "#F5C518",
  TRADING_DISABLED: "#F5820B",
  CRITICAL: "#E5322D",
};

function Pill({ state }: { state: HealthState }) {
  return (
    <span style={{ background: HEALTH_COLOUR[state], color: "#0b0e14", borderRadius: 4,
      padding: "2px 8px", fontSize: 12, fontWeight: 700 }}>{state}</span>
  );
}

function Card({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <div style={{ flex: "1 1 150px", padding: 14, border: "1px solid #1c2333",
      borderRadius: 8, background: "#0f1420" }}>
      <div style={{ fontSize: 11, color: "#7f8aa0", marginBottom: 6 }}>{label}</div>
      <div style={{ fontSize: 18, fontWeight: 700 }}>{value}</div>
      {sub ? <div style={{ fontSize: 11, color: "#7f8aa0", marginTop: 4 }}>{sub}</div> : null}
    </div>
  );
}

export default function Page() {
  const s = loadSnapshot();

  return (
    <main style={{ maxWidth: 1000, margin: "0 auto", padding: "32px 20px" }}>
      <header style={{ borderBottom: "1px solid #1c2333", paddingBottom: 16 }}>
        <h1 style={{ margin: 0, fontSize: 22, letterSpacing: 1 }}>TRADING COMMAND</h1>
        <p style={{ margin: "6px 0 0", color: "#7f8aa0", fontSize: 13 }}>
          Human Control Plane · Trading &amp; Intelligence Cockpit (§98) ·{" "}
          {s ? `snapshot ${s.generated_at}` : "no snapshot"}
        </p>
      </header>

      {/* Prime Directive — no return target (§0) */}
      <section style={{ margin: "18px 0", padding: 14, border: "1px solid #1c2333",
        borderRadius: 8, background: "#0f1420" }}>
        <div style={{ fontSize: 12, color: "#7f8aa0", marginBottom: 6 }}>PRIME DIRECTIVE (§0)</div>
        <div style={{ fontSize: 14, lineHeight: 1.5 }}>
          V1 exists to <b>prove or disprove tradable edge — not to make money</b>. No
          return target. Promotion is gated by proof, never profit.
        </div>
      </section>

      {!s ? (
        <p style={{ color: "#7f8aa0" }}>
          No snapshot found. Generate one with <code>tc snapshot</code>.
        </p>
      ) : (
        <>
          {/* Main cockpit (§98) */}
          <section style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
            <Card label="MODE" value={s.mode} />
            <Card label="SHADOW EQUITY" value={`£${s.shadow_equity.toFixed(2)}`}
              sub="reference unit £250 — not a target" />
            <Card label="REALISED P&L" value={`£${s.realized_pnl.toFixed(2)}`} />
            <Card label="TOTAL RETURN" value={`${s.total_return_pct.toFixed(2)}%`} />
            <Card label="MAX DRAWDOWN" value={`£${s.max_drawdown.toFixed(2)}`} />
            <div style={{ flex: "1 1 150px", padding: 14, border: "1px solid #1c2333",
              borderRadius: 8, background: "#0f1420" }}>
              <div style={{ fontSize: 11, color: "#7f8aa0", marginBottom: 6 }}>KILL SWITCH</div>
              <Pill state={s.kill_switch ? "CRITICAL" : "HEALTHY"} />
            </div>
          </section>

          {/* Opportunity / decision funnel (§100) + rejection view (§102) */}
          <section style={{ marginTop: 22 }}>
            <h2 style={{ fontSize: 14, color: "#7f8aa0" }}>OPPORTUNITY FUNNEL (§100, §102)</h2>
            <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
              <Card label="OPPORTUNITIES" value={String(s.opportunities)} />
              <Card label="LONG / SHORT" value={`${s.decisions.LONG} / ${s.decisions.SHORT}`} />
              <Card label="WAIT" value={String(s.decisions.WAIT)} sub="first-class state (§70)" />
              <Card label="REJECTED" value={String(s.rejected)} sub="measured anyway (§50)" />
            </div>
          </section>

          {/* Performance (§86, v1.2) */}
          <section style={{ marginTop: 22 }}>
            <h2 style={{ fontSize: 14, color: "#7f8aa0" }}>PERFORMANCE (§86)</h2>
            <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
              <Card label="TRADES" value={String(s.performance.trades)} />
              <Card label="WIN RATE" value={s.performance.win_rate.toFixed(2)} />
              <Card label="EXPECTANCY (R)" value={s.performance.expectancy_r.toFixed(2)}
                sub="headline — not win rate (§87)" />
              <Card label="PROFIT FACTOR"
                value={s.performance.profit_factor === null ? "n/a" : s.performance.profit_factor.toFixed(2)} />
              <Card label="COSTS" value={`£${s.performance.total_costs.toFixed(2)}`} />
            </div>
          </section>

          {/* Recent closed trades (§98) */}
          <section style={{ marginTop: 22 }}>
            <h2 style={{ fontSize: 14, color: "#7f8aa0" }}>RECENT CLOSED TRADES</h2>
            {s.recent_trades.length === 0 ? (
              <p style={{ color: "#7f8aa0", fontSize: 13 }}>
                No trades in this run — {s.rejected} opportunity(ies) resolved to WAIT/REJECT
                or were unaffordable (§85). A valid, honest result (§0/§130).
              </p>
            ) : (
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
                <thead>
                  <tr style={{ color: "#7f8aa0", textAlign: "left" }}>
                    <th style={{ padding: "6px 8px" }}>Instrument</th>
                    <th>Dir</th><th>Strategy</th><th>Regime</th>
                    <th>Exit</th><th>R</th><th>Net P&L</th>
                  </tr>
                </thead>
                <tbody>
                  {s.recent_trades.map((t, i) => (
                    <tr key={i} style={{ borderTop: "1px solid #1c2333" }}>
                      <td style={{ padding: "6px 8px" }}>{t.instrument}</td>
                      <td>{t.direction}</td><td>{t.strategy}</td><td>{t.regime}</td>
                      <td>{t.exit_reason}</td>
                      <td style={{ color: t.r >= 0 ? "#22B24C" : "#E5322D" }}>{t.r.toFixed(2)}</td>
                      <td style={{ color: t.net_pnl >= 0 ? "#22B24C" : "#E5322D" }}>
                        £{t.net_pnl.toFixed(2)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </section>
        </>
      )}
    </main>
  );
}
