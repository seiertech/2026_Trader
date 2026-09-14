"""Typed config models and the loader.

Depends on ``tc_domain`` for the shared vocabulary (single source of truth,
TC-ADR-031). No engine imports config directly at construction time other than
through :func:`load_config`, so policy enforcement has exactly one entry point.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, ValidationError, field_validator
from tc_domain.enums import AssetClass, MarketPermission, OperatingMode
from tc_domain.policy import PolicyViolation, assert_no_return_target, assert_not_crypto

# The 17 required risk controls (§77). Presence is enforced at load time.
REQUIRED_RISK_CONTROLS: frozenset[str] = frozenset(
    {
        "MAX_RISK_PER_TRADE", "MAX_DAILY_LOSS", "MAX_WEEKLY_LOSS", "MAX_DRAWDOWN",
        "MAX_OPEN_RISK", "MAX_POSITIONS", "MAX_LEVERAGE", "MAX_CORRELATED_EXPOSURE",
        "MAX_INSTRUMENT_EXPOSURE", "MIN_REWARD_RISK", "MAX_SPREAD", "MAX_SLIPPAGE",
        "MAX_CONSECUTIVE_LOSSES", "MANDATORY_STOP", "EVENT_BLACKOUT",
        "STALE_DATA_BLOCK", "KILL_SWITCH",
    }
)


class ConfigError(Exception):
    """Raised when configuration is missing, malformed or fails a policy check."""


class InstrumentConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    canonical_id: str
    display_name: str
    asset_class: AssetClass
    permission: MarketPermission = MarketPermission.INTELLIGENCE_ONLY
    broker_symbol: str | None = None


class RiskConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    risk_controls: dict[str, Any]

    @field_validator("risk_controls")
    @classmethod
    def _all_controls_present(cls, v: dict[str, Any]) -> dict[str, Any]:
        missing = REQUIRED_RISK_CONTROLS - set(v)
        if missing:
            raise ValueError(
                f"risk.yaml missing required controls (§77): {sorted(missing)}"
            )
        return v


class RuntimeConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    mode: OperatingMode = OperatingMode.SHADOW
    reference_unit_gbp: float = 250
    return_target: Any = None  # MUST stay null (Prime Directive §0, TC-ADR-017)
    market_data_provider: str = "replay"
    execution_provider: str = "shadow_simulator"
    golden_path_instrument: str = "XAUUSD"


class TradingCommandConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    runtime: RuntimeConfig
    risk: RiskConfig
    instruments: tuple[InstrumentConfig, ...]


def _read_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ConfigError(f"config file not found: {path}")
    with path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    if not isinstance(data, dict):
        raise ConfigError(f"config file {path} did not parse to a mapping")
    return data


def load_config(config_dir: str | Path = "config") -> TradingCommandConfig:
    """Load and validate all config, applying the un-overridable policy tier.

    Raises :class:`ConfigError` on any structural or policy failure — fail closed.
    """
    root = Path(config_dir)
    try:
        runtime = RuntimeConfig(**_read_yaml(root / "runtime.yaml"))
        risk = RiskConfig(**_read_yaml(root / "risk.yaml"))
        instruments_raw = _read_yaml(root / "instruments.yaml").get("instruments", [])
        instruments = tuple(InstrumentConfig(**row) for row in instruments_raw)
    except ValidationError as exc:
        raise ConfigError(f"config validation failed: {exc}") from exc

    # --- Policy tier (§0, §7) — applied once, here, at the single load entry point ---
    try:
        assert_no_return_target(runtime.return_target)
        for inst in instruments:
            assert_not_crypto(inst.canonical_id)
            if inst.broker_symbol:
                assert_not_crypto(inst.broker_symbol)
    except PolicyViolation as exc:
        # Surface as a ConfigError so startup fails closed with a clear reason code.
        raise ConfigError(str(exc)) from exc

    return TradingCommandConfig(runtime=runtime, risk=risk, instruments=instruments)
