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
