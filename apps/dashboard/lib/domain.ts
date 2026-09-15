// TypeScript mirror of the Trading Command domain contract.
// Source of truth is packages/domain (Python); these types are hand-mirrored per
// TC-ADR-031. Keep in sync — a generator can replace this later.

export type OperatingMode =
  | "OFF"
  | "SHADOW"
  | "PAPER"
  | "LIVE_LIMITED"
  | "LIVE_AUTO";

export type HealthState =
  | "HEALTHY"
  | "DEGRADED"
  | "TRADING_DISABLED"
  | "CRITICAL";

export type MarketPermission =
  | "INTELLIGENCE_ONLY"
  | "SHADOW_TRADABLE"
  | "LIVE_TRADABLE"
  | "PROHIBITED";

export interface SystemStatus {
  mode: OperatingMode;
  health: HealthState;
  // Component health (§98/§103): MT5, Eightcap, AI, News/Intelligence.
  components: { name: string; state: HealthState; detail?: string }[];
  killSwitch: boolean;
  // £250 is a reference unit, NOT a capital base or target (§74, TC-ADR-016).
  referenceUnitGbp: number;
  // There is NO return target (§0, §75, TC-ADR-017). Always null.
  returnTarget: null;
}

// The cockpit snapshot shape (§98-102). Mirrors apps/runtime/tc_runtime/snapshot.py
// (Python is the source of truth; keep in sync — TC-ADR-031).
export interface RecentTrade {
  instrument: string;
  direction: string;
  strategy: string;
  regime: string;
  entry: string;
  exit: string;
  exit_reason: string;
  r: number;
  net_pnl: number;
  evidence_pack_id: string;
}

export interface Performance {
  trades: number;
  wins: number;
  losses: number;
  win_rate: number;
  profit_factor: number | null;
  expectancy_r: number;
  expectancy_cash: number;
  avg_mfe_r: number;
  avg_mae_r: number;
  total_costs: number;
}

export interface CockpitSnapshot {
  generated_at: string;
  mode: OperatingMode;
  system_health: HealthState;
  reference_unit_gbp: number;
  return_target: null;
  shadow_equity: number;
  realized_pnl: number;
  total_return_pct: number;
  max_drawdown: number;
  kill_switch: boolean;
  opportunities: number;
  decisions: { LONG: number; SHORT: number; WAIT: number; REJECT: number };
  rejected: number;
  performance: Performance;
  recent_trades: RecentTrade[];
}
