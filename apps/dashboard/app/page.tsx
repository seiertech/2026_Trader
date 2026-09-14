import type { HealthState, SystemStatus } from "@/lib/domain";

// Phase 0 shell: static placeholder status. Phase 1 wires this to apps/api which
// reads live state from the Python runtime. The cockpit panels (§98, TC-ADR-036)
// are stubbed here as "not yet built" — we build vertically (§107), starting with
// the XAUUSD golden path (§123), not with breadth.
const STATUS: SystemStatus = {
  mode: "SHADOW",
  health: "HEALTHY",
  components: [
    { name: "MT5", state: "DEGRADED", detail: "replay provider (no Windows host yet)" },
    { name: "Eightcap", state: "DEGRADED", detail: "not connected in SHADOW" },
    { name: "AI", state: "HEALTHY", detail: "deterministic-only until Phase 9" },
    { name: "News / Intelligence", state: "HEALTHY", detail: "not yet ingesting" },
  ],
  killSwitch: false,
  referenceUnitGbp: 250,
  returnTarget: null,
};

const HEALTH_COLOUR: Record<HealthState, string> = {
  HEALTHY: "#22B24C",
  DEGRADED: "#F5C518",
  TRADING_DISABLED: "#F5820B",
  CRITICAL: "#E5322D",
};

function Pill({ state }: { state: HealthState }) {
  return (
    <span
      style={{
        background: HEALTH_COLOUR[state],
        color: "#0b0e14",
        borderRadius: 4,
        padding: "2px 8px",
        fontSize: 12,
        fontWeight: 700,
      }}
    >
      {state}
    </span>
  );
}

export default function Page() {
  return (
    <main style={{ maxWidth: 900, margin: "0 auto", padding: "32px 20px" }}>
      <header style={{ borderBottom: "1px solid #1c2333", paddingBottom: 16 }}>
        <h1 style={{ margin: 0, fontSize: 22, letterSpacing: 1 }}>TRADING COMMAND</h1>
        <p style={{ margin: "6px 0 0", color: "#7f8aa0", fontSize: 13 }}>
          Human Control Plane · TC-SPEC-001 v1.3 · Phase 0 shell
        </p>
      </header>

      {/* Prime Directive is displayed, front and centre — no return target (§0). */}
      <section
        style={{
          margin: "20px 0",
          padding: 16,
          border: "1px solid #1c2333",
          borderRadius: 8,
          background: "#0f1420",
        }}
      >
        <div style={{ fontSize: 12, color: "#7f8aa0", marginBottom: 6 }}>
          PRIME DIRECTIVE (§0)
        </div>
        <div style={{ fontSize: 14, lineHeight: 1.5 }}>
          V1 exists to <b>prove or disprove tradable edge — not to make money</b>.
          There is <b>no return target</b>. Promotion is gated by proof, never profit
          or schedule.
        </div>
      </section>

      <section style={{ display: "flex", gap: 16, flexWrap: "wrap" }}>
        <Card label="OPERATING MODE" value={STATUS.mode} />
        <Card label="SYSTEM HEALTH" node={<Pill state={STATUS.health} />} />
        <Card label="REFERENCE UNIT" value={`£${STATUS.referenceUnitGbp}`} sub="risk/R only — not a target" />
        <Card
          label="KILL SWITCH"
          node={
            <Pill state={STATUS.killSwitch ? "CRITICAL" : "HEALTHY"} />
          }
          sub={STATUS.killSwitch ? "ENGAGED" : "armed / off"}
        />
      </section>

      <section style={{ marginTop: 24 }}>
        <h2 style={{ fontSize: 14, color: "#7f8aa0" }}>DEPENDENCIES (§98, §103)</h2>
        <div style={{ display: "grid", gridTemplateColumns: "1fr auto", gap: 8 }}>
          {STATUS.components.map((c) => (
            <div key={c.name} style={{ display: "contents" }}>
              <div>
                {c.name}
                {c.detail ? (
                  <span style={{ color: "#7f8aa0", fontSize: 12 }}> — {c.detail}</span>
                ) : null}
              </div>
              <Pill state={c.state} />
            </div>
          ))}
        </div>
      </section>

      <section style={{ marginTop: 24, color: "#7f8aa0", fontSize: 13 }}>
        <h2 style={{ fontSize: 14 }}>COCKPIT (§98) — not yet built</h2>
        <p>
          P&amp;L, opportunities, positions, developing events, regimes, and
          performance attribution land as the vertical XAUUSD golden path is built
          (§123). This shell only proves MODE, health and the kill switch.
        </p>
      </section>
    </main>
  );
}

function Card({
  label,
  value,
  node,
  sub,
}: {
  label: string;
  value?: string;
  node?: React.ReactNode;
  sub?: string;
}) {
  return (
    <div
      style={{
        flex: "1 1 180px",
        padding: 16,
        border: "1px solid #1c2333",
        borderRadius: 8,
        background: "#0f1420",
      }}
    >
      <div style={{ fontSize: 11, color: "#7f8aa0", marginBottom: 8 }}>{label}</div>
      <div style={{ fontSize: 18, fontWeight: 700 }}>{value ?? node}</div>
      {sub ? <div style={{ fontSize: 11, color: "#7f8aa0", marginTop: 6 }}>{sub}</div> : null}
    </div>
  );
}
